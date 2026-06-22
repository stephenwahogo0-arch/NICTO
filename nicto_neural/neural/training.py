import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time
import random
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from .super_config import SuperConfig
from .super_core import SuperNeuralCore


@dataclass
class TrainingBatch:
    input_ids: torch.Tensor
    labels: torch.Tensor
    attention_mask: Optional[torch.Tensor] = None
    rewards: Optional[torch.Tensor] = None
    advantages: Optional[torch.Tensor] = None
    task_types: Optional[List[str]] = None


class SFTTrainer:
    def __init__(self, model: SuperNeuralCore, config: SuperConfig, lr: float = 3e-4):
        self.model = model
        self.config = config
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=lr, betas=(0.9, 0.95), weight_decay=0.1)
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=1000, eta_min=lr * 0.1)

    def train_step(self, batch: TrainingBatch) -> Dict[str, float]:
        self.model.train()
        self.optimizer.zero_grad()

        output = self.model(batch.input_ids)
        logits = output["logits"]

        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch.labels[..., 1:].contiguous()

        loss = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=-100,
        )

        aux_losses = []
        for layer in self.model.layers:
            if hasattr(layer.moe, '_last_aux_loss'):
                aux_losses.append(layer.moe._last_aux_loss)
                aux_losses.append(layer.moe._last_z_loss)

        total_loss = loss + sum(aux_losses)
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()
        self.scheduler.step()

        with torch.no_grad():
            preds = shift_logits.argmax(dim=-1)
            acc = (preds == shift_labels).float().mean().item()

        return {
            "loss": loss.item(),
            "accuracy": acc,
            "perplexity": math.exp(min(loss.item(), 20)),
            "lr": self.scheduler.get_last_lr()[0],
        }


class PPOTrainer:
    def __init__(
        self,
        model: SuperNeuralCore,
        config: SuperConfig,
        reward_model: Optional[Callable] = None,
        lr: float = 1e-5,
        kl_coef: float = 0.1,
        clip_epsilon: float = 0.2,
    ):
        self.model = model
        self.config = config
        self.reward_model = reward_model
        self.kl_coef = kl_coef
        self.clip_epsilon = clip_epsilon
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
        self.ref_model = None

    def set_reference(self, ref_model: SuperNeuralCore):
        self.ref_model = ref_model
        for p in self.ref_model.parameters():
            p.requires_grad = False

    def train_step(self, batch: TrainingBatch, old_logprobs: torch.Tensor) -> Dict[str, float]:
        self.model.train()
        self.optimizer.zero_grad()

        output = self.model(batch.input_ids)
        logits = output["logits"]

        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch.labels[..., 1:].contiguous()

        log_probs = -F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=-100,
            reduction="none",
        )

        if batch.advantages is not None:
            advantages = batch.advantages
        else:
            advantages = torch.ones_like(log_probs)

        ratio = torch.exp(log_probs - old_logprobs)
        pg_loss1 = -advantages * ratio
        pg_loss2 = -advantages * torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon)
        pg_loss = torch.max(pg_loss1, pg_loss2).mean()

        if self.ref_model is not None:
            with torch.no_grad():
                ref_output = self.ref_model(batch.input_ids)
                ref_logits = ref_output["logits"]
                ref_log_probs = -F.cross_entropy(
                    ref_logits[..., :-1, :].contiguous().view(-1, ref_logits.size(-1)),
                    shift_labels.view(-1),
                    ignore_index=-100,
                    reduction="none",
                )
            kl_div = (old_logprobs - ref_log_probs).mean()
        else:
            kl_div = torch.tensor(0.0)

        loss = pg_loss + self.kl_coef * kl_div
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

        return {
            "pg_loss": pg_loss.item(),
            "kl_div": kl_div.item() if isinstance(kl_div, torch.Tensor) else 0.0,
            "total_loss": loss.item(),
        }


class GRPOTrainer:
    def __init__(
        self,
        model: SuperNeuralCore,
        config: SuperConfig,
        lr: float = 3e-5,
        group_size: int = 8,
        clip_epsilon: float = 0.2,
    ):
        self.model = model
        self.config = config
        self.group_size = group_size
        self.clip_epsilon = clip_epsilon
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
        self.ref_model = None

    def set_reference(self, ref_model: SuperNeuralCore):
        self.ref_model = ref_model
        for p in self.ref_model.parameters():
            p.requires_grad = False

    def train_step(
        self, prompts: torch.Tensor, reward_fn: Callable
    ) -> Dict[str, float]:
        self.model.train()

        all_outputs = []
        all_logprobs = []
        all_rewards = []

        for _ in range(self.group_size):
            output = self.model(prompts)
            logits = output["logits"]
            probs = F.softmax(logits, dim=-1)
            log_probs = torch.log(probs + 1e-8)
            all_outputs.append(output)
            all_logprobs.append(log_probs)

            if self.ref_model is not None:
                with torch.no_grad():
                    ref_out = self.ref_model(prompts)
                    ref_logits = ref_out["logits"]
                    ref_probs = F.softmax(ref_logits, dim=-1)
                    ref_log_probs = torch.log(ref_probs + 1e-8)

        if reward_fn is not None:
            for i in range(self.group_size):
                full_text = all_outputs[i]["logits"].argmax(dim=-1)
                reward = reward_fn(full_text)
                all_rewards.append(reward)

        if all_rewards:
            rewards_t = torch.tensor(all_rewards, device=prompts.device)
            mean_r = rewards_t.mean()
            std_r = rewards_t.std() + 1e-8
            advantages = (rewards_t - mean_r) / std_r
        else:
            advantages = torch.zeros(self.group_size, device=prompts.device)

        self.optimizer.zero_grad()

        total_loss = 0.0
        for i in range(self.group_size):
            log_probs = all_logprobs[i]
            shift_logits = all_outputs[i]["logits"][..., :-1, :].contiguous()
            shift_labels = prompts[..., 1:].contiguous()

            per_token_logp = -F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100,
                reduction="none",
            )

            if self.ref_model is not None:
                ref_log_probs_i = ref_log_probs[..., :-1, :].contiguous()
                ratio = torch.exp(per_token_logp - ref_log_probs_i.view(-1)[:per_token_logp.size(0)])
            else:
                ratio = torch.exp(per_token_logp - per_token_logp.detach())

            adv = advantages[i] if i < len(advantages) else 0.0
            pg_loss1 = -ratio * adv
            pg_loss2 = -torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * adv
            loss = torch.max(pg_loss1, pg_loss2).mean()
            total_loss = total_loss + loss

        total_loss = total_loss / self.group_size
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

        return {
            "grpo_loss": total_loss.item(),
            "mean_reward": float(np.mean(all_rewards)) if all_rewards else 0.0,
            "group_size": self.group_size,
        }


class CurriculumTrainer:
    def __init__(
        self,
        model: SuperNeuralCore,
        config: SuperConfig,
        lr: float = 3e-4,
        n_levels: int = 10,
    ):
        self.model = model
        self.config = config
        self.n_levels = n_levels
        self.current_level = 1
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.1)

        self.difficulty_thresholds = [0.3 + 0.65 * (i / n_levels) for i in range(1, n_levels + 1)]
        self.performance_history: List[float] = []

    def get_current_difficulty(self) -> float:
        return self.difficulty_thresholds[min(self.current_level - 1, self.n_levels - 1)]

    def train_step(self, batch: TrainingBatch) -> Dict[str, float]:
        self.model.train()
        self.optimizer.zero_grad()

        output = self.model(batch.input_ids)
        logits = output["logits"]

        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch.labels[..., 1:].contiguous()

        loss = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=-100,
        )

        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

        with torch.no_grad():
            acc = (shift_logits.argmax(dim=-1) == shift_labels).float().mean().item()
            self.performance_history.append(acc)

        if len(self.performance_history) >= 50:
            recent_perf = np.mean(self.performance_history[-50:])
            if recent_perf > self.difficulty_thresholds[min(self.current_level - 1, self.n_levels - 1)]:
                self.current_level = min(self.n_levels, self.current_level + 1)

        return {
            "loss": loss.item(),
            "accuracy": acc,
            "curriculum_level": self.current_level,
            "difficulty": self.get_current_difficulty(),
        }


class SuperTrainer:
    def __init__(self, config: SuperConfig):
        self.config = config
        self.sft_trainers: Dict[str, SFTTrainer] = {}
        self.ppo_trainers: Dict[str, PPOTrainer] = {}
        self.grpo_trainers: Dict[str, GRPOTrainer] = {}
        self.curriculum_trainers: Dict[str, CurriculumTrainer] = {}
        self.training_history: List[Dict] = []

    def register_model(self, name: str, model: SuperNeuralCore):
        self.sft_trainers[name] = SFTTrainer(model, self.config)
        self.curriculum_trainers[name] = CurriculumTrainer(model, self.config)

    def train_sft(self, model_name: str, batch: TrainingBatch) -> Dict[str, float]:
        if model_name not in self.sft_trainers:
            raise ValueError(f"Model '{model_name}' not registered")
        result = self.sft_trainers[model_name].train_step(batch)
        result["mode"] = "sft"
        result["model"] = model_name
        result["timestamp"] = time.time()
        self.training_history.append(result)
        return result

    def train_ppo(
        self, model_name: str, batch: TrainingBatch, old_logprobs: torch.Tensor
    ) -> Dict[str, float]:
        if model_name not in self.ppo_trainers:
            raise ValueError(f"PPO trainer for '{model_name}' not initialized")
        result = self.ppo_trainers[model_name].train_step(batch, old_logprobs)
        result["mode"] = "ppo"
        result["model"] = model_name
        result["timestamp"] = time.time()
        self.training_history.append(result)
        return result

    def train_grpo(
        self, model_name: str, prompts: torch.Tensor, reward_fn: Callable
    ) -> Dict[str, float]:
        if model_name not in self.grpo_trainers:
            raise ValueError(f"GRPO trainer for '{model_name}' not initialized")
        result = self.grpo_trainers[model_name].train_step(prompts, reward_fn)
        result["mode"] = "grpo"
        result["model"] = model_name
        result["timestamp"] = time.time()
        self.training_history.append(result)
        return result

    def train_curriculum(self, model_name: str, batch: TrainingBatch) -> Dict[str, float]:
        if model_name not in self.curriculum_trainers:
            raise ValueError(f"Curriculum trainer for '{model_name}' not initialized")
        result = self.curriculum_trainers[model_name].train_step(batch)
        result["mode"] = "curriculum"
        result["model"] = model_name
        result["timestamp"] = time.time()
        self.training_history.append(result)
        return result

    def get_history(self, n_last: int = 100) -> List[Dict]:
        return self.training_history[-n_last:]

    def get_stats(self) -> Dict:
        if not self.training_history:
            return {"total_steps": 0}
        return {
            "total_steps": len(self.training_history),
            "modes_used": list(set(h["mode"] for h in self.training_history)),
            "avg_loss": np.mean([h.get("loss", 0) for h in self.training_history[-100:]]),
        }
