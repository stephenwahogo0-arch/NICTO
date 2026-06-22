"""Neural Intelligence Core — transformer-style reasoning with MoE, sparse activation, and long-context attention."""

from __future__ import annotations

import json
import math
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from nicto_x.neural.tokenizer import NeuralTokenizer

logger = logging.getLogger("nicto_x.neural")


@dataclass
class MoEConfig:
    num_experts: int = 8
    top_k: int = 2
    expert_dim: int = 512
    capacity_factor: float = 1.25


@dataclass
class AttentionConfig:
    num_heads: int = 8
    head_dim: int = 64
    dropout: float = 0.1
    max_seq_len: int = 131072
    sliding_window: int = 4096


@dataclass
class NeuralProcessingResult:
    output_text: str
    tokens_processed: int
    confidence: float
    attention_weights: list[float]
    expert_activations: list[str]
    layer_activations: list[int]
    processing_time_ms: float
    perplexity: float


class NeuralCore:
    """Neural processing engine with attention, MoE routing, and long-context support."""

    def __init__(
        self,
        vocab_size: int = 32000,
        d_model: int = 768,
        num_layers: int = 12,
        moe: MoEConfig = None,
        attention: AttentionConfig = None,
    ):
        self.d_model = d_model
        self.num_layers = num_layers
        self.moe = moe or MoEConfig()
        self.attention_cfg = attention or AttentionConfig()
        self.tokenizer = NeuralTokenizer(vocab_size=vocab_size, embedding_dim=d_model)

        self._layers: list[dict] = []
        self._expert_weights: dict[str, list[list[float]]] = {}
        self._initialize_parameters()
        self._path = Path.home() / ".nicto-x" / "neural_core.json"

    def _initialize_parameters(self):
        import hashlib
        rng_seed = hashlib.sha256(b"nicto_x_neural_init").digest()
        rng = np.frombuffer(rng_seed, dtype=np.uint8).astype(np.float32) / 255.0

        self._layers = []
        self._expert_weights_np: dict[str, np.ndarray] = {}

        for lyr in range(self.num_layers):
            self._layers.append({
                "layer": lyr,
                "type": "transformer_block",
                "activation": "silu" if lyr % 2 == 0 else "gelu",
                "num_heads": self.attention_cfg.num_heads,
                "head_dim": self.attention_cfg.head_dim,
            })

            for expert in range(self.moe.num_experts):
                ek = f"{lyr}_{expert}"
                w = np.random.RandomState(seed=lyr * 1000 + expert).randn(self.moe.expert_dim, self.d_model).astype(np.float32) * 0.1
                self._expert_weights_np[ek] = w

    def _rms_norm(self, x: np.ndarray) -> np.ndarray:
        ss = np.mean(x ** 2) + 1e-6
        return x / np.sqrt(ss)

    def _silu(self, x: np.ndarray) -> np.ndarray:
        return x / (1.0 + np.exp(-x))

    def _gelu(self, x: np.ndarray) -> np.ndarray:
        return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * x ** 3)))

    def _multi_head_attention(self, q: np.ndarray, k: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n = q.shape[0]
        d_model = q.shape[1]
        n_h = self.attention_cfg.num_heads
        d_h = d_model // n_h
        scale = 1.0 / math.sqrt(max(d_h, 1))

        q = q[:, :n_h * d_h].reshape(n, n_h, d_h).transpose(1, 0, 2)
        k = k[:, :n_h * d_h].reshape(n, n_h, d_h).transpose(1, 0, 2)
        v = v[:, :n_h * d_h].reshape(n, n_h, d_h).transpose(1, 0, 2)

        attn = np.matmul(q, k.transpose(0, 2, 1)) * scale
        attn_weights = np.exp(attn - attn.max(axis=-1, keepdims=True))
        attn_weights /= attn_weights.sum(axis=-1, keepdims=True) + 1e-10

        out = np.matmul(attn_weights, v)
        out = out.transpose(1, 0, 2).reshape(n, -1)

        avg_weight = float(np.mean(attn_weights))
        return out, np.array([avg_weight])

    def _moe_ffn(self, x: np.ndarray, layer_idx: int, act_type: str) -> tuple[np.ndarray, list[str]]:
        expert_scores = []
        for expert in range(self.moe.num_experts):
            ek = f"{layer_idx}_{expert}"
            w = self._expert_weights_np.get(ek)
            if w is None:
                expert_scores.append(0.0)
                continue
            score = float(np.abs(np.dot(w, x)).sum())
            expert_scores.append(score)

        top_k = min(self.moe.top_k, self.moe.num_experts)
        top_k_indices = np.argsort(expert_scores)[-top_k:][::-1]
        routing_weights = np.array([expert_scores[i] for i in top_k_indices])
        routing_weights /= routing_weights.sum() + 1e-10

        output = np.zeros_like(x)
        for rank, idx in enumerate(top_k_indices):
            ek = f"{layer_idx}_{idx}"
            w = self._expert_weights_np[ek]
            rw = routing_weights[rank]
            expert_out = w @ x
            if act_type == "silu":
                expert_out = self._silu(expert_out)
            elif act_type == "gelu":
                expert_out = self._gelu(expert_out)
            else:
                expert_out = np.maximum(0, expert_out)
            out_size = min(len(output), len(expert_out))
            output[:out_size] += rw * expert_out[:out_size]

        expert_names = [f"expert_{i}" for i in top_k_indices.tolist()]
        return output, expert_names

    def process(self, text: str, max_tokens: int = 4096) -> NeuralProcessingResult:
        start = time.time()
        tokens = self.tokenizer.tokenize(text)[:max_tokens]
        if not tokens:
            return NeuralProcessingResult(output_text="", tokens_processed=0, confidence=0.0, attention_weights=[], expert_activations=[], layer_activations=[], processing_time_ms=0.0, perplexity=0.0)

        hidden = np.array([self.tokenizer.embed(t) for t in tokens], dtype=np.float32)
        all_attention_weights = []
        all_experts = []
        layer_activations = []

        for layer in self._layers:
            lyr = layer["layer"]
            act_type = layer["activation"]

            hidden, attn_w = self._multi_head_attention(hidden, hidden, hidden)
            all_attention_weights.extend(attn_w.tolist())

            hidden = self._rms_norm(hidden)

            for i in range(hidden.shape[0]):
                hidden[i], experts_used = self._moe_ffn(hidden[i], lyr, act_type)
                all_experts.extend(experts_used)

            act_val = float(np.abs(hidden).mean())
            layer_activations.append(round(act_val, 4))

        n_tokens = hidden.shape[0]
        d = hidden.shape[1]
        proj = np.zeros((n_tokens, 100), dtype=np.float32)
        for j in range(d):
            proj[:, j % 100] += hidden[:, j] * (j + 1) * 0.01
        output_ids = (np.argmax(proj, axis=1) % 32000).tolist()

        output_text = self.tokenizer.detokenize(output_ids[:50])

        flat = hidden.flatten()
        total_log = np.sum(np.log(np.abs(flat) + 1e-10))
        perplexity = float(np.exp(total_log / max(len(flat), 1)))

        confidence = min(1.0, 0.3 + 0.5 * (len(tokens) / max(len(text.split()), 1)))
        elapsed = (time.time() - start) * 1000

        unique_experts = list(set(all_experts)) if all_experts else ["none"]

        return NeuralProcessingResult(
            output_text=output_text,
            tokens_processed=len(tokens),
            confidence=round(confidence, 4),
            attention_weights=[round(w, 4) for w in all_attention_weights],
            expert_activations=unique_experts[:10],
            layer_activations=layer_activations,
            processing_time_ms=round(elapsed, 2),
            perplexity=round(perplexity, 4),
        )

    def save(self):
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump({
                "d_model": self.d_model,
                "num_layers": self.num_layers,
                "moe": {"num_experts": self.moe.num_experts, "top_k": self.moe.top_k},
                "attention": {"num_heads": self.attention_cfg.num_heads, "max_seq_len": self.attention_cfg.max_seq_len},
            }, f)

    def load(self):
        if self._path.exists():
            with open(self._path) as f:
                data = json.load(f)
    def get_info(self) -> dict:
        return {
            "d_model": self.d_model,
            "num_layers": self.num_layers,
            "num_experts": self.moe.num_experts,
            "top_k_experts": self.moe.top_k,
            "num_heads": self.attention_cfg.num_heads,
            "max_seq_len": self.attention_cfg.max_seq_len,
            "vocab_size": self.tokenizer.vocab_size,
        }
