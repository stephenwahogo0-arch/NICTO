import torch
import json
import re
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter


class Tokenizer:
    def __init__(self, vocab_size: int = 32768):
        self.vocab_size = vocab_size
        self.special_tokens = {"<pad>": 0, "<bos>": 1, "<eos>": 2, "<unk>": 3}
        self.token_to_id: Dict[str, int] = dict(self.special_tokens)
        self.id_to_token: Dict[int, str] = {v: k for k, v in self.special_tokens.items()}
        self.merges: Dict[Tuple[str, str], str] = {}
        self.merge_priority: Dict[Tuple[str, str], int] = {}
        self._next_id = len(self.special_tokens)
        self._word_pattern = re.compile(r"\S+")

    def _get_next_id(self) -> int:
        idx = self._next_id
        self._next_id += 1
        return idx

    def _add_token(self, token: str) -> int:
        if token not in self.token_to_id:
            idx = self._get_next_id()
            self.token_to_id[token] = idx
            self.id_to_token[idx] = token
            return idx
        return self.token_to_id[token]

    def _get_pair_stats(self, word_counts: Dict[str, int]) -> Counter:
        pair_counts: Counter = Counter()
        for word, freq in word_counts.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pair_counts[(symbols[i], symbols[i + 1])] += freq
        return pair_counts

    def _merge_word(self, word: str, pair: Tuple[str, str], merged: str) -> str:
        symbols = word.split()
        i = 0
        result = []
        while i < len(symbols):
            if i < len(symbols) - 1 and symbols[i] == pair[0] and symbols[i + 1] == pair[1]:
                result.append(merged)
                i += 2
            else:
                result.append(symbols[i])
                i += 1
        return " ".join(result)

    def train(self, texts: List[str]) -> None:
        word_counts: Dict[str, int] = defaultdict(int)
        for text in texts:
            for word in self._word_pattern.findall(text):
                word_counts[word.lower()] += 1

        for word in word_counts:
            chars = " ".join(list(word))
            self._add_token(word)
            for ch in set(word):
                self._add_token(ch)

        initial_tokens = set(self.token_to_id.keys())
        base_vocab = {t for t in initial_tokens if len(t) == 1 or t in self.special_tokens}

        word_splits: Dict[str, str] = {}
        for word in word_counts:
            word_splits[word] = " ".join(list(word))

        current_vocab_size = len(self.token_to_id)
        target_size = self.vocab_size - len(self.special_tokens)

        for _ in range(target_size):
            pair_counts: Counter = Counter()
            for word, freq in word_counts.items():
                symbols = word_splits[word].split()
                for i in range(len(symbols) - 1):
                    pair_counts[(symbols[i], symbols[i + 1])] += freq

            if not pair_counts:
                break

            best_pair = max(pair_counts, key=pair_counts.get)
            merged_token = "".join(best_pair)
            if merged_token in self.token_to_id:
                continue

            self.merges[best_pair] = merged_token
            self.merge_priority[best_pair] = len(self.merges)
            self._add_token(merged_token)

            for word in word_counts:
                word_splits[word] = self._merge_word(word_splits[word], best_pair, merged_token)

    def encode(self, text: str) -> torch.Tensor:
        tokens = [self.special_tokens["<bos>"]]
        for word in self._word_pattern.findall(text):
            word_lower = word.lower()
            if word_lower in self.token_to_id:
                tokens.append(self.token_to_id[word_lower])
            else:
                chars = list(word_lower)
                merged = False
                for (a, b), merged_token in sorted(self.merges.items(), key=lambda x: x[0][0]):
                    word_str = " ".join(chars)
                    if a in word_str and b in word_str:
                        segments = word_str.split()
                        i = 0
                        result = []
                        while i < len(segments):
                            if i < len(segments) - 1 and segments[i] == a and segments[i + 1] == b:
                                if merged_token in self.token_to_id:
                                    result.append(merged_token)
                                else:
                                    result.append(segments[i])
                                    result.append(segments[i + 1])
                                i += 2
                            else:
                                result.append(segments[i])
                                i += 1
                        tokens.extend(self.token_to_id.get(s, self.special_tokens["<unk>"]) for s in result)
                        merged = True
                        break
                if not merged:
                    for ch in chars:
                        tokens.append(self.token_to_id.get(ch, self.special_tokens["<unk>"]))
        tokens.append(self.special_tokens["<eos>"])
        return torch.tensor(tokens, dtype=torch.long)

    def decode(self, tokens: torch.Tensor) -> str:
        parts = []
        for t in tokens.tolist():
            token = self.id_to_token.get(t, "<unk>")
            if token in self.special_tokens:
                if token == "<eos>":
                    break
                if token == "<pad>" or token == "<bos>":
                    continue
            parts.append(token)
        return "".join(parts)

    @property
    def vocab_size(self) -> int:
        return self._vocab_size

    @vocab_size.setter
    def vocab_size(self, value: int):
        self._vocab_size = value

    def save(self, path: str) -> None:
        state = {
            "token_to_id": self.token_to_id,
            "id_to_token": {str(k): v for k, v in self.id_to_token.items()},
            "merges": {f"{a}|{b}": c for (a, b), c in self.merges.items()},
            "merge_priority": {f"{a}|{b}": p for (a, b), p in self.merge_priority.items()},
            "next_id": self._next_id,
            "vocab_size": self._vocab_size,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.token_to_id = state["token_to_id"]
        self.id_to_token = {int(k): v for k, v in state["id_to_token"].items()}
        self.merges = {}
        for key, val in state["merges"].items():
            a, b = key.split("|")
            self.merges[(a, b)] = val
        self.merge_priority = {}
        for key, val in state["merge_priority"].items():
            a, b = key.split("|")
            self.merge_priority[(a, b)] = val
        self._next_id = state["next_id"]
        self._vocab_size = state["vocab_size"]
