"""Tests for transformer core."""

import torch

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.neural.transformer import TransformerBlock, TransformerCore


def test_forward_pass():
    config = NeuralConfig()
    model = TransformerCore(config)
    x = torch.randint(0, config.vocab_size, (2, 32))
    output = model(x)
    assert output.shape == (2, 32, config.d_model)


def test_causal_mask():
    config = NeuralConfig()
    model = TransformerCore(config)
    seq_len = 16
    mask = torch.tril(torch.ones(seq_len, seq_len)).unsqueeze(0).unsqueeze(0)
    x = torch.randint(0, config.vocab_size, (1, seq_len))
    output = model(x, mask)
    assert output.shape == (1, seq_len, config.d_model)


def test_gradient_flow():
    config = NeuralConfig()
    model = TransformerCore(config)
    x = torch.randint(0, config.vocab_size, (1, 8))
    output = model(x)
    loss = output.sum()
    loss.backward()
    for param in model.parameters():
        if param.requires_grad:
            assert param.grad is not None


def test_moe_routing():
    from nicto_neural.neural.moe_router import MoERouter
    config = NeuralConfig()
    router = MoERouter(config)
    x = torch.randn(2, 8, config.d_model)
    output, balance_loss = router(x)
    assert output.shape == x.shape
    assert balance_loss.item() >= 0


def test_brain_heads_output():
    from nicto_neural.neural.brain_heads import BrainHeads
    config = NeuralConfig()
    heads = BrainHeads(config)
    x = torch.randn(2, 8, config.d_model)
    outputs = heads(x)
    assert len(outputs) == 6
    for name, result in outputs.items():
        assert result["logits"].shape == (2, 8, config.vocab_size)
        assert result["confidence"].shape == (2,)
