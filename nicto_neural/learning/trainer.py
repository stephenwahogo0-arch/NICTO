import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import time
import json
import os
import copy
from typing import Dict, List, Optional


class NeuralTrainer:
    def __init__(self, config, model: nn.Module, device: str = "cpu"):
        self.config = config
        self.model = model
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.model.to(self.device)
        self.optimizer = None
        self.scheduler = None
        self.history = {"loss": [], "accuracy": [], "val_loss": [], "val_accuracy": [], "epochs": 0}

    def train(self, dataset: List[Dict], mode: str = "supervised", epochs: int = 10, batch_size: int = 32) -> Dict:
        if mode == "supervised":
            return self.train_supervised(dataset, epochs, batch_size)
        elif mode == "rl":
            return self.train_rl(dataset, epochs)
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def train_supervised(self, dataset: List[Dict], epochs: int = 10, batch_size: int = 32, lr: float = 1e-4) -> Dict:
        if not dataset:
            return {"loss": float("inf"), "accuracy": 0.0, "epochs": 0}
        input_ids_list = []
        output_ids_list = []
        for example in dataset:
            inp = example.get("input", "")
            out = example.get("output", example.get("expected", ""))
            inp_ids = self._text_to_ids(str(inp), self.config.vocab_size, self.config.d_model)
            out_ids = self._text_to_ids(str(out), self.config.vocab_size, self.config.d_model)
            input_ids_list.append(inp_ids)
            output_ids_list.append(out_ids)
        if not input_ids_list:
            raw_dataset = dataset
            input_ids_list = list(range(min(len(raw_dataset), 100)))
            output_ids_list = list(range(min(len(raw_dataset), 100)))
            input_tensor = torch.stack([torch.randn(self.config.d_model) for _ in range(len(input_ids_list))])
            output_tensor = torch.stack([torch.randn(self.config.d_model) for _ in range(len(output_ids_list))])
        else:
            input_tensor = torch.stack([torch.tensor(ids, dtype=torch.float32) for ids in input_ids_list])
            output_tensor = torch.stack([torch.tensor(ids, dtype=torch.float32) for ids in output_ids_list])

        tensor_dataset = TensorDataset(input_tensor, output_tensor)
        dataloader = DataLoader(tensor_dataset, batch_size=min(batch_size, len(tensor_dataset)), shuffle=True)

        self.optimizer = optim.AdamW(self.model.parameters(), lr=lr)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=epochs)
        criterion = nn.MSELoss()
        scaler = torch.cuda.amp.GradScaler() if self.device == "cuda" else None
        accumulation_steps = max(1, min(4, len(dataloader)))
        epoch_history = []
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0
            correct = 0
            total = 0
            self.optimizer.zero_grad()
            for batch_idx, (inputs, targets) in enumerate(dataloader):
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                if scaler:
                    with torch.cuda.amp.autocast():
                        outputs = self.model(inputs)
                        loss = criterion(outputs, targets)
                    scaler.scale(loss).backward()
                    if (batch_idx + 1) % accumulation_steps == 0:
                        scaler.step(self.optimizer)
                        scaler.update()
                        self.optimizer.zero_grad()
                else:
                    outputs = self.model(inputs)
                    loss = criterion(outputs, targets)
                    loss.backward()
                    if (batch_idx + 1) % accumulation_steps == 0:
                        self.optimizer.step()
                        self.optimizer.zero_grad()
                total_loss += loss.item()
                pred_classes = outputs.argmax(dim=-1) if outputs.shape[-1] > 1 else (outputs > 0.5).float()
                target_classes = targets.argmax(dim=-1) if targets.shape[-1] > 1 else (targets > 0.5).float()
                correct += (pred_classes == target_classes).sum().item() if pred_classes.numel() > 0 else 0
                total += targets.numel()
            avg_loss = total_loss / len(dataloader)
            accuracy = correct / max(total, 1)
            self.scheduler.step()
            epoch_history.append({"loss": avg_loss, "accuracy": accuracy})
            self.history["loss"].append(avg_loss)
            self.history["accuracy"].append(accuracy)
            self.history["epochs"] += 1
        self.history["epochs"] = epochs
        return {"loss": avg_loss, "accuracy": accuracy, "epochs": epochs, "history": epoch_history}

    def train_rl(self, dataset: List[Dict], epochs: int = 10, lr: float = 3e-5) -> Dict:
        if not dataset:
            return {"loss": float("inf"), "policy_loss": 0.0, "value_loss": 0.0, "epochs": 0}
        self.optimizer = optim.AdamW(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()
        epoch_history = []
        for epoch in range(epochs):
            self.model.train()
            total_policy_loss = 0.0
            total_value_loss = 0.0
            count = 0
            for example in dataset:
                state = torch.randn(self.config.d_model, device=self.device)
                advantage = torch.tensor(example.get("score", 1.0) - 0.5, device=self.device)
                return_val = torch.tensor(example.get("score", 1.0), device=self.device)
                action_logit = self.model(state.unsqueeze(0))
                if hasattr(self.model, "forward") and action_logit.dim() > 1 and action_logit.shape[-1] >= 2:
                    log_probs = torch.log_softmax(action_logit, dim=-1)
                    action = torch.randint(0, log_probs.shape[-1], (1,), device=self.device)
                    selected_log_prob = log_probs[0, action[0]]
                    policy_loss = -(selected_log_prob * advantage.detach())
                    value_pred = action_logit[0, :1].mean()
                    value_loss = criterion(value_pred.unsqueeze(0), return_val.unsqueeze(0).unsqueeze(0))
                else:
                    policy_loss = torch.tensor(0.0, device=self.device)
                    value_loss = criterion(action_logit.squeeze(), return_val)
                loss = policy_loss + value_loss
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                count += 1
            avg_policy = total_policy_loss / max(count, 1)
            avg_value = total_value_loss / max(count, 1)
            epoch_history.append({"policy_loss": avg_policy, "value_loss": avg_value})
            self.history["loss"].append(avg_policy + avg_value)
            self.history["epochs"] += 1
        return {"policy_loss": avg_policy, "value_loss": avg_value, "epochs": epochs, "history": epoch_history}

    def evaluate(self, dataset: List[Dict]) -> Dict:
        if not dataset:
            return {"loss": float("inf"), "accuracy": 0.0}
        self.model.eval()
        criterion = nn.MSELoss()
        total_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for example in dataset:
                inp = example.get("input", "")
                out = example.get("output", example.get("expected", ""))
                inp_t = torch.tensor(self._text_to_ids(str(inp), self.config.vocab_size, self.config.d_model), dtype=torch.float32, device=self.device)
                out_t = torch.tensor(self._text_to_ids(str(out), self.config.vocab_size, self.config.d_model), dtype=torch.float32, device=self.device)
                prediction = self.model(inp_t.unsqueeze(0)).squeeze(0)
                loss = criterion(prediction, out_t)
                total_loss += loss.item()
                pred_classes = prediction.argmax(dim=-1) if prediction.dim() > 0 and prediction.shape[-1] > 1 else (prediction > 0.5).float()
                target_classes = out_t.argmax(dim=-1) if out_t.dim() > 0 and out_t.shape[-1] > 1 else (out_t > 0.5).float()
                if pred_classes.numel() == target_classes.numel():
                    correct += (pred_classes == target_classes).sum().item()
                    total += target_classes.numel()
        avg_loss = total_loss / max(len(dataset), 1)
        accuracy = correct / max(total, 1)
        return {"loss": avg_loss, "accuracy": accuracy}

    def checkpoint(self, path: str) -> None:
        state = {
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict() if self.optimizer else None,
            "scheduler_state": self.scheduler.state_dict() if self.scheduler else None,
            "history": self.history,
            "config": {"d_model": self.config.d_model, "vocab_size": self.config.vocab_size},
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        torch.save(state, path)

    def load_checkpoint(self, path: str) -> None:
        state = torch.load(path, map_location=self.device)
        self.model.load_state_dict(state["model_state"])
        if state.get("optimizer_state") and self.optimizer:
            self.optimizer.load_state_dict(state["optimizer_state"])
        if state.get("scheduler_state") and self.scheduler:
            self.scheduler.load_state_dict(state["scheduler_state"])
        self.history = state.get("history", self.history)

    def save(self, path: str) -> None:
        self.checkpoint(path)

    def load(self, path: str) -> None:
        self.load_checkpoint(path)

    def _text_to_ids(self, text: str, vocab_size: int, d_model: int) -> List[float]:
        ids = [hash(c) % vocab_size for c in text[:d_model]]
        if len(ids) < d_model:
            ids.extend([0] * (d_model - len(ids)))
        return [v / vocab_size for v in ids[:d_model]]
