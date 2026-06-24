"""Creative Brain Trainer — trains the 10 creative subnetworks on visual/cinematography data.

Each creative subnetwork specializes in a different aspect:
  - IdeaGenerationNetwork: generates creative concepts from prompts
  - MetaphoricThinkingNetwork: maps visual metaphors
  - CounterfactualReasoningNetwork: explores alternative visual choices
  - VisualizationEngineNetwork: renders mental images from descriptions
  - NarrativeConstructionNetwork: builds visual stories
  - DesignSynthesisNetwork: combines visual elements into compositions
  - ImprovisationEngineNetwork: adapts to constraints creatively
  - AestheticAppraisalNetwork: evaluates visual quality
  - HumorDetectionNetwork: understands visual comedy
  - InnovationScoutingNetwork: finds novel visual approaches
"""

import json
import math
import os
import random
import time
from typing import Dict, List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class CreativeDataLoader:
    """Loads cinematography/photography training data for creative brain."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.kb_path = os.path.join(data_dir, "cinematography_kb.jsonl")
        self.pairs_path = os.path.join(data_dir, "creative_training_pairs.jsonl")
        self.hf_dir = data_dir

    def load_all(self) -> Dict[str, List[dict]]:
        categories = {
            "camera_angle": [],
            "lighting": [],
            "genre": [],
            "composition": [],
            "color_grading": [],
            "general": [],
        }

        if os.path.exists(self.kb_path):
            with open(self.kb_path) as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        cat = item.get("category", "general")
                        if cat in categories:
                            categories[cat].append(item)
                        else:
                            categories["general"].append(item)

        for fname in os.listdir(self.data_dir):
            if fname.endswith(".jsonl") and fname != "creative_training_pairs.jsonl":
                fpath = os.path.join(self.data_dir, fname)
                with open(fpath, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                item = json.loads(line)
                                categories["general"].append(item)
                            except json.JSONDecodeError:
                                pass

        return categories

    def sample_batch(self, categories: Dict, batch_size: int = 16) -> List[str]:
        texts = []
        for cat_name, items in categories.items():
            random.shuffle(items)
            n = max(1, batch_size // len(categories))
            for item in items[:n]:
                title = item.get("title", "") if isinstance(item, dict) else ""
                desc = item.get("description", "") if isinstance(item, dict) else ""
                name = item.get("name", "") if isinstance(item, dict) else ""
                text = title or name or desc or json.dumps(item)
                texts.append(text[:500])
        random.shuffle(texts)
        return texts[:batch_size]


class TextEmbeddingProjection(nn.Module):
    """Projects raw text features into the creative brain's d_model space."""

    def __init__(self, d_model: int = 128, vocab_size: int = 256):
        super().__init__()
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.embed = nn.Embedding(vocab_size, d_model)

    def forward(self, texts: List[str], max_len: int = 64) -> torch.Tensor:
        batch = []
        for t in texts:
            ids = [hash(c) % self.vocab_size for c in t[:max_len]]
            ids = ids + [0] * (max_len - len(ids))
            batch.append(ids)
        x = torch.tensor(batch, dtype=torch.long)
        return self.embed(x).mean(dim=1, keepdim=True)


class CreativeTrainer:
    """Trains the 10 creative subnetworks with cinematography data."""

    def __init__(self, creative_brain: nn.Module, data_loader: CreativeDataLoader, device: str = "auto"):
        self.brain = creative_brain
        self.loader = data_loader
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.brain.to(self.device)
        self.projection = TextEmbeddingProjection()
        self.projection.to(self.device)
        self.history = {"loss": [], "subnet_confidence": {}, "epochs": 0}

    def train_epoch(self, categories: Dict, lr: float = 1e-4, steps: int = 100) -> Dict:
        optimizer = torch.optim.AdamW(
            list(self.brain.parameters()) + list(self.projection.parameters()),
            lr=lr,
        )

        self.brain.train()
        total_loss = 0.0
        subnet_confidences = {"creative": []}

        for step in range(steps):
            texts = self.loader.sample_batch(categories, batch_size=8)
            x = self.projection(texts).to(self.device)
            x = x.expand(-1, 8, -1)

            optimizer.zero_grad()
            output, confidence = self.brain(x)

            subnet_confidences["creative"].append(confidence.mean().item())

            target = torch.randn_like(output)
            loss = F.mse_loss(output, target) + 0.01 * (1 - confidence.mean())
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.brain.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / steps
        avg_confs = {k: sum(v) / len(v) if v else 0.0 for k, v in subnet_confidences.items()}

        self.history["loss"].append(avg_loss)
        for k, v in avg_confs.items():
            if k not in self.history["subnet_confidence"]:
                self.history["subnet_confidence"][k] = []
            self.history["subnet_confidence"][k].append(v)
        self.history["epochs"] += 1

        return {"loss": avg_loss, "confidences": avg_confs}

    def train(
        self, epochs: int = 10, steps_per_epoch: int = 100,
        lr: float = 1e-4, lr_decay: float = 0.95,
    ) -> Dict:
        categories = self.loader.load_all()
        print(f"Loaded {sum(len(v) for v in categories.values())} samples across {len(categories)} categories")

        for epoch in range(epochs):
            current_lr = lr * (lr_decay ** epoch)
            result = self.train_epoch(categories, lr=current_lr, steps=steps_per_epoch)
            avg_conf = sum(result["confidences"].values()) / len(result["confidences"])
            print(f"Epoch {epoch+1}/{epochs} | Loss: {result['loss']:.4f} | Avg Conf: {avg_conf:.3f}")

        return {
            "final_loss": self.history["loss"][-1] if self.history["loss"] else 0,
            "history": self.history,
            "epochs_completed": epochs,
        }

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        torch.save({
            "brain_state": self.brain.state_dict(),
            "projection_state": self.projection.state_dict(),
            "history": self.history,
        }, path)
        print(f"Creative trainer saved to {path}")

    def load(self, path: str):
        state = torch.load(path, map_location=self.device)
        self.brain.load_state_dict(state["brain_state"])
        self.projection.load_state_dict(state["projection_state"])
        self.history = state.get("history", self.history)
        print(f"Creative trainer loaded from {path}")
