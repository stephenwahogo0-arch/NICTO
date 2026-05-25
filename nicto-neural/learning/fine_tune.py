import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import copy
import json
import os
from typing import Dict, List, Optional, Tuple


class LoRAAdapter(nn.Module):
    def __init__(self, layer: nn.Linear, rank: int = 8, alpha: float = 16.0):
        super().__init__()
        self.layer = layer
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        in_features = layer.in_features
        out_features = layer.out_features
        self.lora_A = nn.Parameter(torch.zeros(in_features, rank))
        self.lora_B = nn.Parameter(torch.zeros(rank, out_features))
        nn.init.kaiming_uniform_(self.lora_A, a=5 ** 0.5)
        nn.init.zeros_(self.lora_B)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        original = self.layer(x)
        lora_out = (x @ self.lora_A) @ self.lora_B
        return original + lora_out * self.scaling


class FineTuner:
    def __init__(self, config, model: nn.Module):
        self.config = config
        self.model = model
        self.device = torch.device(config.device if torch.cuda.is_available() and config.device == "cuda" else "cpu")
        self.model.to(self.device)
        self.adapters: Dict[str, LoRAAdapter] = {}
        self.original_weights: Dict[str, nn.Parameter] = {}
        self.is_lora_wrapped = False

    def wrap_with_lora(self, target_modules: List[str] = None, rank: int = 8, alpha: float = 16.0) -> None:
        if target_modules is None:
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
        self.adapters.clear()
        self.original_weights.clear()
        for name, module in self.model.named_modules():
            for target in target_modules:
                if target in name and isinstance(module, nn.Linear):
                    adapter = LoRAAdapter(module, rank=rank, alpha=alpha)
                    self.adapters[name] = adapter
                    self.original_weights[name] = module.weight
                    self._replace_module(self.model, name.split("."), adapter)
        self.is_lora_wrapped = True

    def _replace_module(self, root: nn.Module, name_parts: List[str], new_module: nn.Module) -> None:
        if len(name_parts) == 1:
            setattr(root, name_parts[0], new_module)
        else:
            child = getattr(root, name_parts[0])
            self._replace_module(child, name_parts[1:], new_module)

    def freeze_base(self) -> None:
        for name, param in self.model.named_parameters():
            is_lora = any(adapter_name in name for adapter_name in self.adapters.keys())
            if not is_lora and "lora_A" not in name and "lora_B" not in name:
                param.requires_grad = False

    def unfreeze_lora(self) -> None:
        for name, param in self.model.named_parameters():
            if "lora_A" in name or "lora_B" in name:
                param.requires_grad = True

    def train(self, dataset: List[Dict], epochs: int = 5, lr: float = 1e-4) -> Dict:
        self.freeze_base()
        self.unfreeze_lora()
        trainable_params = [p for p in self.model.parameters() if p.requires_grad]
        if not trainable_params:
            return {"loss": float("inf"), "accuracy": 0.0, "epochs": 0}

        optimizer = optim.AdamW(trainable_params, lr=lr)
        criterion = nn.MSELoss()
        inputs_list = []
        outputs_list = []
        for example in dataset:
            inp = example.get("input", "")
            out = example.get("output", example.get("expected", ""))
            inp_t = self._text_to_tensor(str(inp))
            out_t = self._text_to_tensor(str(out))
            inputs_list.append(inp_t)
            outputs_list.append(out_t)

        if not inputs_list:
            inputs_t = torch.randn(len(dataset), self.config.d_model)
            outputs_t = torch.randn(len(dataset), self.config.d_model)
        else:
            inputs_t = torch.stack(inputs_list)
            outputs_t = torch.stack(outputs_list)

        tensor_dataset = TensorDataset(inputs_t, outputs_t)
        dataloader = DataLoader(tensor_dataset, batch_size=min(32, len(tensor_dataset)), shuffle=True)
        history = []
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0
            correct = 0
            total = 0
            for batch_inputs, batch_targets in dataloader:
                batch_inputs = batch_inputs.to(self.device)
                batch_targets = batch_targets.to(self.device)
                optimizer.zero_grad()
                outputs = self.model(batch_inputs)
                loss = criterion(outputs, batch_targets)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
                optimizer.step()
                total_loss += loss.item()
                if outputs.dim() > 1 and outputs.shape[-1] > 1:
                    pred = outputs.argmax(dim=-1)
                    tgt = batch_targets.argmax(dim=-1)
                    if pred.numel() == tgt.numel():
                        correct += (pred == tgt).sum().item()
                        total += tgt.numel()
            avg_loss = total_loss / max(len(dataloader), 1)
            accuracy = correct / max(total, 1)
            history.append({"loss": avg_loss, "accuracy": accuracy})
        return {"loss": avg_loss, "accuracy": accuracy, "epochs": epochs, "history": history}

    def save_adapter(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        adapter_state = {}
        for name, adapter in self.adapters.items():
            adapter_state[name] = {
                "lora_A": adapter.lora_A.detach().cpu().numpy().tolist(),
                "lora_B": adapter.lora_B.detach().cpu().numpy().tolist(),
                "rank": adapter.rank,
                "alpha": adapter.alpha,
            }
        with open(path, "w") as f:
            json.dump(adapter_state, f)

    def load_adapter(self, path: str) -> None:
        with open(path, "r") as f:
            adapter_state = json.load(f)
        for name, state in adapter_state.items():
            if name in self.adapters:
                self.adapters[name].lora_A.data = torch.tensor(state["lora_A"], dtype=torch.float32)
                self.adapters[name].lora_B.data = torch.tensor(state["lora_B"], dtype=torch.float32)
                self.adapters[name].rank = state.get("rank", 8)
                self.adapters[name].alpha = state.get("alpha", 16.0)
                self.adapters[name].scaling = self.adapters[name].alpha / self.adapters[name].rank

    def merge_weights(self) -> None:
        if not self.is_lora_wrapped:
            return
        for name, adapter in self.adapters.items():
            if name in self.original_weights:
                lora_delta = (adapter.lora_A @ adapter.lora_B) * adapter.scaling
                merged_weight = self.original_weights[name].data + lora_delta.T
                self.original_weights[name].data.copy_(merged_weight)
                adapter.lora_A.data.zero_()
                adapter.lora_B.data.zero_()

    def _text_to_tensor(self, text: str) -> torch.Tensor:
        d_model = self.config.d_model
        vocab_size = self.config.vocab_size
        ids = [hash(c) % vocab_size for c in text[:d_model]]
        if len(ids) < d_model:
            ids.extend([0] * (d_model - len(ids)))
        values = [v / vocab_size for v in ids[:d_model]]
        return torch.tensor(values, dtype=torch.float32)
