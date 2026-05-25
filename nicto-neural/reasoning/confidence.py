import torch
import torch.nn.functional as F
from typing import Dict, List, Optional


class NeuralConfig:
    def __init__(self, d_model: int = 512, device: str = "cpu"):
        self.d_model = d_model
        self.device = device


class TemperatureScaling(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.temperature = torch.nn.Parameter(torch.tensor(1.0))

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        return logits / self.temperature

    def get_temperature(self) -> float:
        return self.temperature.item()


class ConfidenceCalibrator:
    def __init__(self, config: Optional[NeuralConfig] = None):
        self.config = config if config is not None else NeuralConfig()
        self.device = torch.device(self.config.device)
        self._scalers: Dict[str, TemperatureScaling] = {}
        self._default_scaler = TemperatureScaling().to(self.device)

    def calibrate(self, logits: torch.Tensor, temperature: float = 1.0) -> torch.Tensor:
        if not isinstance(logits, torch.Tensor):
            logits = torch.tensor(logits, device=self.device)
        logits = logits.to(self.device)
        if temperature <= 0:
            temperature = 1e-6
        return F.softmax(logits / temperature, dim=-1)

    def confidence(self, probs: torch.Tensor) -> torch.Tensor:
        if not isinstance(probs, torch.Tensor):
            probs = torch.tensor(probs, device=self.device)
        probs = probs.to(self.device)
        if probs.dim() == 1:
            return probs.max()
        return probs.max(dim=-1).values

    def expected_calibration_error(self, confidences: List[float], accuracies: List[float], n_bins: int = 10) -> float:
        if len(confidences) != len(accuracies) or len(confidences) == 0:
            return 0.0

        confs = torch.tensor(confidences, device=self.device)
        accs = torch.tensor(accuracies, device=self.device)

        bin_boundaries = torch.linspace(0, 1, n_bins + 1, device=self.device)
        ece = 0.0

        for i in range(n_bins):
            in_bin = (confs > bin_boundaries[i]) & (confs <= bin_boundaries[i + 1])
            prop_in_bin = in_bin.float().mean()
            if prop_in_bin.item() > 0:
                avg_conf_in_bin = confs[in_bin].mean()
                avg_acc_in_bin = accs[in_bin].mean()
                ece += torch.abs(avg_conf_in_bin - avg_acc_in_bin).item() * prop_in_bin.item()

        return ece

    def temperature_scale(self, logits: torch.Tensor, labels: torch.Tensor) -> float:
        if not isinstance(logits, torch.Tensor):
            logits = torch.tensor(logits, device=self.device)
        if not isinstance(labels, torch.Tensor):
            labels = torch.tensor(labels, device=self.device)
        logits = logits.to(self.device)
        labels = labels.to(self.device)

        scaler = TemperatureScaling().to(self.device)
        optimizer = torch.optim.LBFGS([scaler.temperature], lr=0.01, max_iter=50)

        def eval():
            optimizer.zero_grad()
            scaled_logits = scaler(logits)
            loss = F.nll_loss(F.log_softmax(scaled_logits, dim=-1), labels)
            loss.backward()
            return loss

        optimizer.step(eval)
        return scaler.get_temperature()

    def fit_temperature(self, val_logits: List[torch.Tensor], val_labels: List[torch.Tensor]) -> float:
        if len(val_logits) == 0 or len(val_labels) == 0:
            return 1.0

        logits_list = []
        labels_list = []
        for logits, lbls in zip(val_logits, val_labels):
            if isinstance(logits, torch.Tensor) and isinstance(lbls, torch.Tensor):
                logits_list.append(logits.to(self.device))
                labels_list.append(lbls.to(self.device))

        if len(logits_list) == 0:
            return 1.0

        all_logits = torch.cat(logits_list, dim=0) if len(logits_list) > 1 else logits_list[0]
        all_labels = torch.cat(labels_list, dim=0) if len(labels_list) > 1 else labels_list[0]

        if all_logits.dim() == 1:
            all_logits = all_logits.unsqueeze(-1)
        if all_labels.dim() == 0:
            all_labels = all_labels.unsqueeze(-1)
        if all_labels.dim() > 1:
            all_labels = all_labels.squeeze(-1)

        self._default_scaler = TemperatureScaling().to(self.device)
        optimizer = torch.optim.LBFGS([self._default_scaler.temperature], lr=0.01, max_iter=100)

        def closure():
            optimizer.zero_grad()
            scaled = self._default_scaler(all_logits)
            loss = F.nll_loss(F.log_softmax(scaled, dim=-1), all_labels.long())
            loss.backward()
            return loss

        optimizer.step(closure)
        return self._default_scaler.get_temperature()
