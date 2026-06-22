import torch
import pytest
from ..neural.config import NeuralConfig
from ..neural.attention import MultiHeadAttention, CausalSelfAttention, CrossAttention
from ..neural.transformer import TransformerBlock, TransformerCore, TransformerWithLMHead


def test_mha():
    config = NeuralConfig(d_model=64, n_heads=2)
    mha = MultiHeadAttention(config)
    x = torch.randn(2, 8, 64)
    out = mha(x)
    assert out.shape == (2, 8, 64)


def test_causal_mha():
    config = NeuralConfig(d_model=64, n_heads=2)
    mha = CausalSelfAttention(config)
    x = torch.randn(2, 8, 64)
    out = mha(x)
    assert out.shape == (2, 8, 64)


def test_cross_attn():
    config = NeuralConfig(d_model=64, n_heads=2)
    ca = CrossAttention(config)
    q = torch.randn(2, 4, 64)
    kv = torch.randn(2, 8, 64)
    out = ca(q, kv)
    assert out.shape == (2, 4, 64)


def test_transformer_block():
    config = NeuralConfig(d_model=64, n_heads=2, d_ff=128)
    block = TransformerBlock(config)
    x = torch.randn(2, 8, 64)
    out = block(x)
    assert out.shape == (2, 8, 64)


def test_transformer_core():
    config = NeuralConfig(d_model=64, n_heads=2, n_layers=2, vocab_size=100)
    core = TransformerCore(config)
    input_ids = torch.randint(0, 100, (2, 8))
    out = core(input_ids)
    assert out.shape == (2, 8, 64)


def test_lm_head():
    config = NeuralConfig(d_model=64, n_heads=2, n_layers=2, vocab_size=100)
    model = TransformerWithLMHead(config)
    input_ids = torch.randint(0, 100, (2, 8))
    out = model(input_ids)
    assert out.shape == (2, 8, 100)
