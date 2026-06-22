import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import json
import os
import time
import random
from collections import deque
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from .super_config import SuperConfig
from .super_core import SuperNeuralCore


@dataclass
class Experience:
    input_ids: List[int]
    labels: List[int]
    task_type: str = "general"
    difficulty: float = 0.5
    reward: float = 0.0
    timestamp: float = 0.0
    importance: float = 1.0


class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: List[Experience] = []
        self.position = 0

    def add(self, exp: Experience):
        if len(self.buffer) < self.capacity:
            self.buffer.append(exp)
        else:
            self.buffer[self.position] = exp
        self.position = (self.position + 1) % self.capacity

    def add_batch(self, experiences: List[Experience]):
        for exp in experiences:
            self.add(exp)

    def sample(self, batch_size: int, strategy: str = "mixed") -> List[Experience]:
        if not self.buffer:
            return []

        if strategy == "recent":
            return self.buffer[-batch_size:]

        elif strategy == "priority":
            weights = np.array([exp.importance for exp in self.buffer])
            weights = weights / weights.sum()
            indices = np.random.choice(len(self.buffer), size=min(batch_size, len(self.buffer)), p=weights, replace=False)
            return [self.buffer[i] for i in indices]

        else:
            return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self) -> int:
        return len(self.buffer)

    def save(self, path: str):
        data = [(e.input_ids, e.labels, e.task_type, e.difficulty, e.reward, e.timestamp, e.importance) for e in self.buffer]
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, path: str):
        if not os.path.exists(path):
            return
        with open(path) as f:
            data = json.load(f)
        self.buffer = [Experience(*d) for d in data]
        self.position = len(self.buffer) % self.capacity


class EWC:
    def __init__(self, model: SuperNeuralCore, importance: float = 1000.0):
        self.importance = importance
        self.params = {n: p.clone().detach() for n, p in model.named_parameters() if p.requires_grad}
        self.fisher = {n: torch.zeros_like(p) for n, p in model.named_parameters() if p.requires_grad}

    def update_fisher(self, model: SuperNeuralCore, data_loader: List[torch.Tensor]):
        for param in model.parameters():
            param.requires_grad_(True)

        for batch in data_loader:
            model.zero_grad()
            output = model(batch)
            logits = output["logits"]
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                batch.view(-1),
                ignore_index=-100,
                reduction="sum",
            )
            loss.backward()

            for n, p in model.named_parameters():
                if p.grad is not None and n in self.fisher:
                    self.fisher[n] += p.grad.detach() ** 2 / len(data_loader)

    def penalty(self, model: SuperNeuralCore) -> torch.Tensor:
        loss = 0.0
        for n, p in model.named_parameters():
            if n in self.params and n in self.fisher:
                loss += (self.fisher[n] * (p - self.params[n]) ** 2).sum()
        return self.importance * loss / 2.0


class KnowledgeDistillation:
    def __init__(self, temperature: float = 4.0, alpha: float = 0.5):
        self.temperature = temperature
        self.alpha = alpha

    def distill_loss(
        self,
        student_logits: torch.Tensor,
        teacher_logits: torch.Tensor,
        labels: torch.Tensor,
    ) -> torch.Tensor:
        student_soft = F.log_softmax(student_logits / self.temperature, dim=-1)
        teacher_soft = F.softmax(teacher_logits / self.temperature, dim=-1)

        kd_loss = F.kl_div(
            student_soft.view(-1, student_soft.size(-1)),
            teacher_soft.view(-1, teacher_soft.size(-1)),
            reduction="batchmean",
        ) * (self.temperature ** 2)

        ce_loss = F.cross_entropy(
            student_logits.view(-1, student_logits.size(-1)),
            labels.view(-1),
            ignore_index=-100,
        )

        return self.alpha * kd_loss + (1 - self.alpha) * ce_loss


class ContinualLearning:
    def __init__(
        self,
        config: SuperConfig,
        replay_capacity: int = 10000,
        ewc_importance: float = 1000.0,
        distill_temperature: float = 4.0,
        state_dir: Optional[str] = None,
    ):
        self.config = config
        self.replay_buffer = ReplayBuffer(capacity=replay_capacity)
        self.distillation = KnowledgeDistillation(temperature=distill_temperature, alpha=0.5)
        self.state_dir = state_dir or os.path.expanduser("~/.nicto/continual")
        os.makedirs(self.state_dir, exist_ok=True)

        self.ewc: Optional[EWC] = None
        self.student: Optional[SuperNeuralCore] = None
        self.teacher: Optional[SuperNeuralCore] = None
        self.teacher_stale = False

        self.optimizer: Optional[torch.optim.Optimizer] = None
        self.task_count = 0
        self.session_count = 0
        self.total_experiences = 0

    def register_student(self, model: SuperNeuralCore, lr: float = 1e-5):
        self.student = model
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    def register_teacher(self, model: SuperNeuralCore):
        self.teacher = model
        for p in self.teacher.parameters():
            p.requires_grad = False
        self.teacher_stale = False

    def init_ewc(self, model: SuperNeuralCore):
        self.ewc = EWC(model, importance=self.config.moe_aux_loss_coef * 1000)

    def add_experience(self, input_ids: List[int], labels: List[int], task_type: str = "general", reward: float = 0.0):
        exp = Experience(
            input_ids=input_ids,
            labels=labels,
            task_type=task_type,
            difficulty=0.5,
            reward=reward,
            timestamp=time.time(),
            importance=1.0 + reward * 0.5,
        )
        self.replay_buffer.add(exp)
        self.total_experiences += 1

    def replay_train_step(self, batch_size: int = 32, strategy: str = "mixed") -> Dict[str, float]:
        if self.student is None or self.optimizer is None:
            return {"status": "no_model"}

        experiences = self.replay_buffer.sample(batch_size, strategy)
        if not experiences:
            return {"status": "empty_buffer"}

        max_len = max(len(e.input_ids) for e in experiences)
        device = next(self.student.parameters()).device

        input_ids = torch.zeros(len(experiences), max_len, dtype=torch.long, device=device)
        labels = torch.full((len(experiences), max_len), -100, dtype=torch.long, device=device)

        for i, exp in enumerate(experiences):
            seq_len = len(exp.input_ids)
            input_ids[i, :seq_len] = torch.tensor(exp.input_ids[:max_len], device=device)
            labels[i, :seq_len] = torch.tensor(exp.labels[:max_len], device=device)

        self.student.train()
        self.optimizer.zero_grad()

        output = self.student(input_ids)
        logits = output["logits"]

        loss = F.cross_entropy(
            logits.view(-1, logits.size(-1)),
            labels.view(-1),
            ignore_index=-100,
        )

        if self.teacher is not None and not self.teacher_stale:
            with torch.no_grad():
                teacher_output = self.teacher(input_ids)
            kd_loss = self.distillation.distill_loss(logits, teacher_output["logits"], labels)
            loss = loss + kd_loss

        if self.ewc is not None:
            ewc_loss = self.ewc.penalty(self.student)
            loss = loss + ewc_loss

        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.student.parameters(), 1.0)
        self.optimizer.step()

        return {
            "loss": loss.item(),
            "buffer_size": len(self.replay_buffer),
            "batch_size": len(experiences),
            "has_distillation": self.teacher is not None and not self.teacher_stale,
            "has_ewc": self.ewc is not None,
        }

    def consolidate_knowledge(self, num_steps: int = 100, batch_size: int = 32):
        stats = []
        for _ in range(num_steps):
            result = self.replay_train_step(batch_size)
            if result.get("status") == "empty_buffer":
                break
            stats.append(result)

        if self.teacher is not None and not self.teacher_stale:
            self.teacher.load_state_dict(self.student.state_dict())

        self.session_count += 1

        return {
            "steps_completed": len(stats),
            "avg_loss": np.mean([s.get("loss", 0) for s in stats]) if stats else 0,
            "session": self.session_count,
        }

    def on_task_complete(self, model: SuperNeuralCore, task_data: List[torch.Tensor]):
        self.task_count += 1

        if self.ewc is not None:
            self.ewc.update_fisher(model, task_data)
            self.ewc.params = {n: p.clone().detach() for n, p in model.named_parameters() if p.requires_grad}

        if self.teacher is None:
            self.register_teacher(model)
        else:
            self.teacher.load_state_dict(model.state_dict())

        self.teacher_stale = False

    def save_state(self, path: Optional[str] = None):
        save_path = path or os.path.join(self.state_dir, "continual_state.json")
        self.replay_buffer.save(os.path.join(self.state_dir, "replay_buffer.json"))
        state = {
            "task_count": self.task_count,
            "session_count": self.session_count,
            "total_experiences": self.total_experiences,
        }
        with open(save_path, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self, path: Optional[str] = None):
        load_path = path or os.path.join(self.state_dir, "continual_state.json")
        if os.path.exists(load_path):
            with open(load_path) as f:
                state = json.load(f)
            self.task_count = state.get("task_count", 0)
            self.session_count = state.get("session_count", 0)
            self.total_experiences = state.get("total_experiences", 0)
        replay_path = os.path.join(self.state_dir, "replay_buffer.json")
        if os.path.exists(replay_path):
            self.replay_buffer.load(replay_path)

    def status(self) -> Dict:
        return {
            "buffer_size": len(self.replay_buffer),
            "task_count": self.task_count,
            "session_count": self.session_count,
            "total_experiences": self.total_experiences,
            "has_teacher": self.teacher is not None,
            "has_ewc": self.ewc is not None,
            "capacity": self.replay_buffer.capacity,
        }
