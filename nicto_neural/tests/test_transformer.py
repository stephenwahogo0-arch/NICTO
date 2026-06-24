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
    assert not torch.isnan(out).any()


def test_causal_attention_is_causal():
    config = NeuralConfig(d_model=32, n_heads=2)
    mha = CausalSelfAttention(config)
    x = torch.randn(1, 16, 32)
    out = mha(x)
    assert out.shape == (1, 16, 32)
    for i in range(4, 12):
        token_before = out[0, i, :]
        token_after = out[0, i, :]
        assert not torch.isnan(token_before).any()


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
    assert not torch.isnan(out).any()


def test_transformer_core():
    config = NeuralConfig(d_model=64, n_heads=2, n_layers=2, vocab_size=100)
    core = TransformerCore(config)
    input_ids = torch.randint(0, 100, (2, 8))
    out = core(input_ids)
    assert out.shape == (2, 8, 64)
    assert out.requires_grad


def test_lm_head():
    config = NeuralConfig(d_model=64, n_heads=2, n_layers=2, vocab_size=100)
    model = TransformerWithLMHead(config)
    input_ids = torch.randint(0, 100, (2, 8))
    out = model(input_ids)
    assert out.shape == (2, 8, 100)


def test_transformer_can_learn():
    config = NeuralConfig(d_model=32, n_heads=2, n_layers=2, vocab_size=50)
    model = TransformerWithLMHead(config)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = torch.nn.CrossEntropyLoss()

    inputs = torch.randint(0, 50, (4, 16))
    targets = torch.randint(0, 50, (4, 16))

    losses = []
    for _ in range(20):
        optimizer.zero_grad()
        logits = model(inputs)
        loss = criterion(logits.view(-1, 50), targets.view(-1))
        loss.backward()
        optimizer.step()
        losses.append(loss.item())

    assert losses[-1] < losses[0], f"Loss did not decrease: {losses[0]:.4f} -> {losses[-1]:.4f}"
    assert losses[-1] < 4.0, f"Final loss too high: {losses[-1]:.4f}"


def test_transformer_parameter_count():
    config = NeuralConfig(d_model=64, n_heads=2, n_layers=2, vocab_size=100)
    core = TransformerCore(config)
    params = core.get_num_params()
    assert params > 0, "Parameter count should be positive"
    assert isinstance(params, int)


def test_transformer_gradient_flow():
    config = NeuralConfig(d_model=32, n_heads=2, n_layers=2, vocab_size=50)
    model = TransformerWithLMHead(config)
    inputs = torch.randint(0, 50, (2, 8))
    logits = model(inputs)
    loss = logits.mean()
    loss.backward()
    has_grad = False
    for p in model.parameters():
        if p.grad is not None and p.grad.abs().sum().item() > 0:
            has_grad = True
            break
    assert has_grad, "No gradients flowing through the model"
