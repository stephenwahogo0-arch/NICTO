import math
import os
import json
import time
from typing import Dict, List, Optional
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset


class TextDataset(Dataset):
    def __init__(self, texts: List[str], vocab_size: int, max_length: int = 512):
        self.encodings = []
        for t in texts:
            ids = [hash(c) % vocab_size for c in t]
            for i in range(0, max(1, len(ids) - max_length), max_length // 2):
                chunk = ids[i:i + max_length]
                if len(chunk) < max_length:
                    chunk = chunk + [0] * (max_length - len(chunk))
                self.encodings.append(torch.tensor(chunk, dtype=torch.long))

    def __len__(self):
        return len(self.encodings)

    def __getitem__(self, idx):
        x = self.encodings[idx]
        return x[:-1], x[1:]


class TransformerTrainer:
    def __init__(self, model: nn.Module, device: str = "auto"):
        self.model = model
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self.model.to(self.device)
        self.optimizer = None
        self.scheduler = None
        self.history = {"loss": [], "perplexity": [], "epochs": 0}
        self.best_loss = float("inf")

    def train(
        self, texts: List[str], epochs: int = 3, batch_size: int = 8,
        lr: float = 3e-4, max_length: int = 512, warmup_steps: int = 100,
        grad_clip: float = 1.0, log_interval: int = 10,
    ) -> Dict:
        vocab_size = self.model.config.vocab_size
        dataset = TextDataset(texts, vocab_size, max_length)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=True)

        self.optimizer = optim.AdamW(self.model.parameters(), lr=lr, betas=(0.9, 0.95), weight_decay=0.1)
        total_steps = len(loader) * epochs
        self.scheduler = optim.lr_scheduler.OneCycleLR(
            self.optimizer, max_lr=lr, total_steps=total_steps,
            pct_start=warmup_steps / total_steps,
        )
        criterion = nn.CrossEntropyLoss()

        global_step = 0
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0
            start_time = time.time()

            for batch_idx, (inputs, targets) in enumerate(loader):
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                self.optimizer.zero_grad()
                logits = self.model(inputs)
                loss = criterion(logits.view(-1, vocab_size), targets.view(-1))
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), grad_clip)
                self.optimizer.step()
                self.scheduler.step()

                total_loss += loss.item()
                global_step += 1

                if batch_idx % log_interval == 0:
                    lr_current = self.scheduler.get_last_lr()[0]
                    print(f"Epoch {epoch+1}/{epochs} | Step {batch_idx}/{len(loader)} | Loss: {loss.item():.4f} | LR: {lr_current:.2e}")

            avg_loss = total_loss / len(loader)
            perplexity = math.exp(avg_loss)
            self.history["loss"].append(avg_loss)
            self.history["perplexity"].append(perplexity)
            self.history["epochs"] += 1
            elapsed = time.time() - start_time
            print(f"Epoch {epoch+1} done | Avg Loss: {avg_loss:.4f} | PPL: {perplexity:.2f} | Time: {elapsed:.1f}s")

            if avg_loss < self.best_loss:
                self.best_loss = avg_loss

        return {"loss": avg_loss, "perplexity": perplexity, "epochs": epochs}

    @torch.no_grad()
    def generate(self, prompt: str, max_new_tokens: int = 100, temperature: float = 0.8) -> str:
        self.model.eval()
        vocab_size = self.model.config.vocab_size
        ids = [hash(c) % vocab_size for c in prompt]
        input_tensor = torch.tensor([ids], dtype=torch.long, device=self.device)
        generated = list(ids)

        for _ in range(max_new_tokens):
            if input_tensor.size(1) > 512:
                input_tensor = input_tensor[:, -512:]
            logits = self.model(input_tensor)
            next_logits = logits[0, -1, :] / temperature
            probs = torch.softmax(next_logits, dim=-1)
            next_id = torch.multinomial(probs, 1).item()
            generated.append(next_id)
            input_tensor = torch.cat([input_tensor, torch.tensor([[next_id]], device=self.device)], dim=1)

        id_to_char = {hash(c) % vocab_size: c for c in set(prompt + " ")}
        chars = [id_to_char.get(i, chr(32 + (i % 94))) for i in generated]
        return "".join(chars)

    def checkpoint(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        state = {
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict() if self.optimizer else None,
            "scheduler_state": self.scheduler.state_dict() if self.scheduler else None,
            "history": self.history,
            "best_loss": self.best_loss,
            "config": {
                "d_model": self.model.config.d_model,
                "vocab_size": self.model.config.vocab_size,
                "n_layers": self.model.config.n_layers,
            },
        }
        torch.save(state, path)
        return path

    def load_checkpoint(self, path: str) -> None:
        state = torch.load(path, map_location=self.device)
        self.model.load_state_dict(state["model_state"])
        if state.get("optimizer_state") and self.optimizer:
            self.optimizer.load_state_dict(state["optimizer_state"])
        if state.get("scheduler_state") and self.scheduler:
            self.scheduler.load_state_dict(state["scheduler_state"])
        self.history = state.get("history", self.history)
        self.best_loss = state.get("best_loss", float("inf"))
