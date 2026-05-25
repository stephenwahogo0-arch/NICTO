"""Simple character-level tokenizer with BPE-style vocabulary."""

import torch


class NictoTokenizer:
    """Character-level tokenizer with special tokens."""

    def __init__(self, vocab_size: int = 32000):
        self.vocab_size = vocab_size
        self._vocab: dict[str, int] = {}
        self._inv_vocab: dict[int, str] = {}
        self._build_basic_vocab()

    def _build_basic_vocab(self) -> None:
        specials = ["[PAD]", "[UNK]", "[BOS]", "[EOS]", "[SEP]"]
        for i, t in enumerate(specials):
            self._vocab[t] = i
            self._inv_vocab[i] = t
        for i in range(32, 127):
            ch = chr(i)
            idx = len(self._vocab)
            self._vocab[ch] = idx
            self._inv_vocab[idx] = ch

    def encode(self, text: str) -> list[int]:
        tokens = [self._vocab["[BOS]"]]
        for char in text:
            tokens.append(self._vocab.get(char, self._vocab["[UNK]"]))
        tokens.append(self._vocab["[EOS]"])
        return tokens

    def decode(self, ids: list[int]) -> str:
        result = []
        for i in ids:
            token = self._inv_vocab.get(i, "")
            if token not in ("[PAD]", "[BOS]", "[EOS]", "[UNK]"):
                result.append(token)
        return "".join(result)

    def batch_encode(
        self,
        texts: list[str],
        max_len: int = 512,
        pad: bool = True,
    ) -> torch.Tensor:
        encoded = [self.encode(t)[:max_len] for t in texts]
        if pad:
            max_actual = max(len(e) for e in encoded)
            pad_id = self._vocab["[PAD]"]
            encoded = [e + [pad_id] * (max_actual - len(e)) for e in encoded]
        return torch.tensor(encoded, dtype=torch.long)

    @property
    def pad_id(self) -> int:
        return self._vocab["[PAD]"]

    @property
    def bos_id(self) -> int:
        return self._vocab["[BOS]"]

    @property
    def eos_id(self) -> int:
        return self._vocab["[EOS]"]
