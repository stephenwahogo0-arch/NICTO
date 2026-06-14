"""Neural tokenizer with configurable vocabulary and embeddings."""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Optional


class NeuralTokenizer:
    """Tokenizes text into tokens with configurable vocabulary size and embedding support."""

    def __init__(self, vocab_size: int = 32000, embedding_dim: int = 768):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self._vocab: dict[str, int] = {}
        self._reverse_vocab: dict[int, str] = {}
        self._embeddings: dict[int, list[float]] = {}
        self._path = Path.home() / ".nicto-x" / "tokenizer.json"
        self._load()

    def _hash_token(self, token: str) -> int:
        h = hashlib.md5(token.encode()).hexdigest()
        return int(h[:8], 16) % (self.vocab_size - 1) + 1

    def tokenize(self, text: str) -> list[int]:
        words = text.lower().split()
        ids = []
        for word in words:
            if word in self._vocab:
                ids.append(self._vocab[word])
            else:
                tid = self._hash_token(word)
                self._vocab[word] = tid
                self._reverse_vocab[tid] = word
                ids.append(tid)
        return ids

    def detokenize(self, ids: list[int]) -> str:
        words = []
        for tid in ids:
            if tid in self._reverse_vocab:
                words.append(self._reverse_vocab[tid])
            elif tid == 0:
                words.append("[PAD]")
            else:
                words.append("[UNK]")
        return " ".join(words)

    def embed(self, token_id: int) -> list[float]:
        if token_id not in self._embeddings:
            seed = str(token_id).encode()
            rng = hashlib.sha256(seed).digest()
            while len(rng) < self.embedding_dim:
                seed = hashlib.sha256(seed).digest()
                rng += seed
            vec = [(rng[i] / 255.0 - 0.5) * 2 for i in range(self.embedding_dim)]
            norm = math.sqrt(sum(x * x for x in vec))
            self._embeddings[token_id] = [x / norm for x in vec] if norm > 0 else vec
        return self._embeddings[token_id]

    def encode(self, text: str) -> list[list[float]]:
        ids = self.tokenize(text)
        return [self.embed(tid) for tid in ids]

    def vocab_size(self) -> int:
        return len(self._vocab)

    def _save(self):
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump({
                "vocab": self._vocab,
                "reverse_vocab": {str(k): v for k, v in self._reverse_vocab.items()},
            }, f)

    def _load(self):
        if self._path.exists():
            with open(self._path) as f:
                data = json.load(f)
            self._vocab = data.get("vocab", {})
            self._reverse_vocab = {int(k): v for k, v in data.get("reverse_vocab", {}).items()}
