import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple


class NeuralConfig:
    def __init__(self, d_model: int = 512, device: str = "cpu"):
        self.d_model = d_model
        self.device = device


class BoostStage(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, learning_rate: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
        self.weight = nn.Parameter(torch.tensor(learning_rate))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x) * self.weight


class BrainBoost:
    def __init__(self, n_stages: int = 5, learning_rate: float = 0.3):
        self.n_stages = n_stages
        self.learning_rate = learning_rate
        self.max_depth = 3
        self.min_child_weight = 1.0
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._stages: List[BoostStage] = []
        self._stage_weights: List[float] = [1.0 / n_stages] * n_stages
        self._trained = False
        self._input_dim = 512

    def predict(self, task_vector: np.ndarray, brain_outputs: Dict[str, torch.Tensor], mode: str = "fixed") -> torch.Tensor:
        if mode == "trained" and self._trained:
            return self.trained_forward(task_vector, brain_outputs)
        return self.fixed_forward(brain_outputs)

    def train_weights(self, task_vectors: np.ndarray, brain_outputs_list: List[Dict], targets: np.ndarray) -> None:
        if len(brain_outputs_list) == 0:
            return

        sample_key = list(brain_outputs_list[0].keys())[0]
        sample_tensor = brain_outputs_list[0][sample_key]
        if isinstance(sample_tensor, torch.Tensor):
            self._input_dim = sample_tensor.shape[-1]
        elif isinstance(sample_tensor, np.ndarray):
            self._input_dim = sample_tensor.shape[-1]
        else:
            self._input_dim = 512

        hidden_dim = max(16, self._input_dim // 2)
        self._stages = []
        for i in range(self.n_stages):
            stage = BoostStage(self._input_dim, hidden_dim, self.learning_rate)
            self._stages.append(stage.to(self.device))

        all_optimizer_params = []
        for stage in self._stages:
            all_optimizer_params.extend(stage.parameters())

        weight_params = [torch.tensor(w, requires_grad=True, device=self.device) for w in self._stage_weights]
        all_optimizer_params.extend(weight_params)

        optimizer = torch.optim.Adam(all_optimizer_params, lr=0.01)

        targets_tensor = torch.tensor(targets, dtype=torch.float32, device=self.device)
        if targets_tensor.dim() == 1:
            targets_tensor = targets_tensor.unsqueeze(-1)
        if targets_tensor.shape[-1] != self._input_dim:
            targets_tensor = targets_tensor.expand(-1, self._input_dim)

        n_iterations = min(100, len(brain_outputs_list) * 10)
        for iteration in range(n_iterations):
            optimizer.zero_grad()
            total_pred = None
            for i, bo_dict in enumerate(brain_outputs_list):
                merged = self._merge_brain_outputs(bo_dict)
                pred = merged
                for stage in self._stages:
                    residual = stage(pred)
                    pred = pred + residual
                if total_pred is None:
                    total_pred = pred * self._stage_weights[i]
                else:
                    total_pred = total_pred + pred * self._stage_weights[i]

            loss = nn.MSELoss()(total_pred, targets_tensor)
            reg = self.regularization_loss()
            total_loss = loss + 0.01 * reg
            total_loss.backward()
            optimizer.step()

            with torch.no_grad():
                for i, w in enumerate(weight_params):
                    self._stage_weights[i] = w.item()

        self._trained = True

    def _merge_brain_outputs(self, outputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        tensors = []
        for brain_name, tensor in outputs.items():
            if isinstance(tensor, torch.Tensor):
                t = tensor.to(self.device)
            elif isinstance(tensor, np.ndarray):
                t = torch.tensor(tensor, device=self.device, dtype=torch.float32)
            else:
                t = torch.tensor([float(tensor)], device=self.device)
            if t.dim() == 0:
                t = t.unsqueeze(0)
            if t.dim() == 1:
                t = t.unsqueeze(0)
            tensors.append(t)

        if len(tensors) == 0:
            return torch.zeros(self._input_dim, device=self.device)

        max_dim = max(t.shape[-1] for t in tensors)
        padded = []
        for t in tensors:
            if t.shape[-1] < max_dim:
                pad = torch.zeros(*t.shape[:-1], max_dim - t.shape[-1], device=self.device)
                t = torch.cat([t, pad], dim=-1)
            padded.append(t)

        merged = torch.stack(padded, dim=0).mean(dim=0)
        if merged.shape[-1] != self._input_dim:
            if merged.shape[-1] < self._input_dim:
                pad = torch.zeros(*merged.shape[:-1], self._input_dim - merged.shape[-1], device=self.device)
                merged = torch.cat([merged, pad], dim=-1)
            else:
                merged = merged[..., :self._input_dim]
        return merged

    def fixed_forward(self, brain_outputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        merged = self._merge_brain_outputs(brain_outputs)
        pred = merged
        for stage in self._stages:
            residual = stage(pred)
            pred = pred + residual
        return pred

    def trained_forward(self, task_vector: np.ndarray, brain_outputs: Dict[str, torch.Tensor]) -> torch.Tensor:
        if not self._trained:
            return self.fixed_forward(brain_outputs)
        merged = self._merge_brain_outputs(brain_outputs)
        pred = merged
        for stage in self._stages:
            residual = stage(pred)
            pred = pred + residual

        tv = torch.tensor(task_vector, device=self.device, dtype=torch.float32)
        if tv.dim() == 0:
            tv = tv.unsqueeze(0)
        if tv.dim() == 1:
            tv = tv.unsqueeze(0)
        if tv.shape[-1] != self._input_dim:
            if tv.shape[-1] < self._input_dim:
                pad = torch.zeros(*tv.shape[:-1], self._input_dim - tv.shape[-1], device=self.device)
                tv = torch.cat([tv, pad], dim=-1)
            else:
                tv = tv[..., :self._input_dim]

        weights_t = torch.tensor(self._stage_weights, device=self.device)
        weighted = pred * weights_t.mean()
        return weighted + 0.1 * tv.mean(dim=-1, keepdim=True)

    def compute_residual(self, output: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        if not isinstance(output, torch.Tensor):
            output = torch.tensor(output, device=self.device, dtype=torch.float32)
        if not isinstance(target, torch.Tensor):
            target = torch.tensor(target, device=self.device, dtype=torch.float32)
        output = output.to(self.device)
        target = target.to(self.device)

        if output.shape != target.shape:
            if output.dim() > target.dim():
                target = target.unsqueeze(-1)
            elif target.dim() > output.dim():
                output = output.unsqueeze(-1)
            max_dim = max(output.shape[-1], target.shape[-1])
            if output.shape[-1] < max_dim:
                pad = torch.zeros(*output.shape[:-1], max_dim - output.shape[-1], device=self.device)
                output = torch.cat([output, pad], dim=-1)
            if target.shape[-1] < max_dim:
                pad = torch.zeros(*target.shape[:-1], max_dim - target.shape[-1], device=self.device)
                target = torch.cat([target, pad], dim=-1)

        return target - output

    def regularization_loss(self) -> torch.Tensor:
        loss = torch.tensor(0.0, device=self.device)
        for stage in self._stages:
            for param in stage.parameters():
                loss = loss + torch.sum(param ** 2)
        return loss
