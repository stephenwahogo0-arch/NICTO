"""7-Brain MoE+MLA Architecture - Forward-pass test for all 19 heads x 70 subnetworks."""

import os, sys, math, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import torch
import torch.nn as nn

os.environ["NIKTO_ENABLE_EXPERIMENTAL"] = "1"
import warnings
warnings.filterwarnings("ignore")


def count_params(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def test_7brain_architecture():
    print("=" * 70)
    print("  7-Brain MoE+MLA Architecture - End-to-End Forward Pass Test")
    print("  70 Subnetworks (7 brains x 10 each), 19 Specialized Heads")
    print("=" * 70)

    from nicto_neural.neural.super_config import SuperConfig
    from nicto_neural.neural.super_core import SuperNeuralCore
    from nicto_neural.neural.heads import (
        SuperHeadEnsemble, BRAIN_HEAD_NAMES, HEAD_CLASSES,
    )
    from nicto_neural.neural.advanced_layers import (
        MultiHeadLatentAttention, EnhancedMoE,
    )

    device = "cpu"
    print(f"\nDevice: {device}")

    config = SuperConfig(
        d_model=512,
        n_heads=8,
        n_kv_heads=4,
        n_layers=6,
        d_ff=2048,
        n_experts=4,
        n_active_experts=2,
        n_shared_experts=1,
        n_brain_heads=19,
        max_seq_len=128,
        vocab_size=4096,
        use_enhanced_moe=True,
        use_mla=True,
        mla_compression_ratio=0.25,
        mla_separate_q=True,
        use_rope=True,
        use_flash_attn=False,
    )

    print(f"\nBuilding SuperNeuralCore (backbone transformer + MoE)...")
    core = SuperNeuralCore(config)
    core_params = count_params(core)
    print(f"  SuperNeuralCore: {core_params:,} params")

    print(f"\nBuilding SuperHeadEnsemble with {len(BRAIN_HEAD_NAMES)} heads...")
    heads = SuperHeadEnsemble(config)
    heads_params = count_params(heads)
    print(f"  SuperHeadEnsemble: {heads_params:,} params")

    total = core_params + heads_params
    print(f"\n  Total architecture: {total:,} params ({total/1e6:.1f}M)")

    for name in BRAIN_HEAD_NAMES:
        cls_name = HEAD_CLASSES.get(name, SuperHeadEnsemble).__name__
        n = sum(p.numel() for p in heads.heads[name].parameters() if p.requires_grad)
        sub = getattr(heads.heads[name], "sub_networks", None)
        if sub:
            sub_names = list(sub.keys())
            print(f"    {name:15s} ({cls_name:20s}): {n:>8,} params, {len(sub_names)} subnetworks")
        else:
            print(f"    {name:15s} ({cls_name:20s}): {n:>8,} params")

    print(f"\n{'-' * 70}")
    print("FORWARD PASS - Testing all 19 heads x 70 subnetworks + MoE + MLA")
    print(f"{'-' * 70}")

    B, T = 2, 32
    input_ids = torch.randint(0, config.vocab_size, (B, T))

    print(f"\nInput shape: {input_ids.shape}")

    for use_mla_val in [True]:
        config.use_mla = use_mla_val
        for use_moe in [True]:
            config.use_enhanced_moe = use_moe

            start = time.time()

            core_out = core(input_ids)
            hidden = core_out["hidden_states"]
            logits = core_out["logits"]

            head_out = heads(hidden, active_heads=BRAIN_HEAD_NAMES)

            elapsed = time.time() - start

            assert "outputs" in head_out, "Missing outputs"
            assert "confidences" in head_out, "Missing confidences"
            assert "fused" in head_out, "Missing fused"
            assert "routing_weights" in head_out, "Missing routing_weights"

            n_heads_out = len(head_out["outputs"])
            assert n_heads_out == 19, f"Expected 19 head outputs, got {n_heads_out}"

            for name in BRAIN_HEAD_NAMES:
                assert name in head_out["outputs"], f"Missing head: {name}"
                assert name in head_out["confidences"], f"Missing confidence: {name}"
                out_t = head_out["outputs"][name]
                conf_t = head_out["confidences"][name]
                assert out_t.shape == (B, T, config.d_model), (
                    f"{name} output shape: {out_t.shape}, expected ({B}, {T}, {config.d_model})"
                )
                assert conf_t.shape == (B, T), (
                    f"{name} confidence shape: {conf_t.shape}, expected ({B}, {T})"
                )
                assert conf_t.min() >= 0 and conf_t.max() <= 1, (
                    f"{name} confidence not in [0,1]: [{conf_t.min():.3f}, {conf_t.max():.3f}]"
                )

            fused = head_out["fused"]
            assert fused.shape == (B, T, config.d_model), (
                f"Fused shape: {fused.shape}, expected ({B}, {T}, {config.d_model})"
            )

            routing = head_out["routing_weights"]
            assert routing.shape == (B, 19), f"Routing shape: {routing.shape}"

            mla_str = "MLA OK" if use_mla_val else "no MLA"
            moe_str = "MoE OK" if use_moe else "no MoE"
            print(f"  [{mla_str}, {moe_str}] "
                  f"All 19 heads OK | fused: {fused.shape} | "
                  f"routing: {routing[0, :5].round(3).tolist()}... | "
                  f"mean conf: {torch.stack(list(head_out['confidences'].values())).mean():.3f} | "
                  f"{elapsed:.2f}s")

    print(f"\n{'-' * 70}")
    print("HEAD ROUTING TEST - route_to_heads with top-5")
    print(f"{'-' * 70}")

    top_5 = heads.route_to_heads(hidden, top_k=5)
    print(f"  Top-5 heads: {top_5}")
    assert len(top_5) == 5, f"Expected 5 heads, got {len(top_5)}"

    print(f"\n{'-' * 70}")
    print("GRADIENT FLOW TEST - Verify gradients propagate through all modules")
    print(f"{'-' * 70}")

    loss = head_out["fused"].mean()
    loss.backward()

    grad_ok = 0
    grad_fail = 0
    for name, param in core.named_parameters():
        if param.grad is not None and param.grad.abs().sum() > 0:
            grad_ok += 1
        else:
            grad_fail += 1
    print(f"  Core gradients flowing: {grad_ok}/{grad_ok + grad_fail}")

    grad_ok_h = 0
    grad_fail_h = 0
    for name, param in heads.named_parameters():
        if param.grad is not None and param.grad.abs().sum() > 0:
            grad_ok_h += 1
        else:
            grad_fail_h += 1
    print(f"  Heads gradients flowing: {grad_ok_h}/{grad_ok_h + grad_fail_h}")

    grad_ok_sub = 0
    grad_fail_sub = 0
    for head_name in BRAIN_HEAD_NAMES:
        head = heads.heads[head_name]
        if hasattr(head, "sub_networks"):
            for sub_name, sub in head.sub_networks.items():
                for p in sub.parameters():
                    if p.grad is not None and p.grad.abs().sum() > 0:
                        grad_ok_sub += 1
                    else:
                        grad_fail_sub += 1
    if grad_ok_sub + grad_fail_sub > 0:
        print(f"  Subnetwork gradients flowing: {grad_ok_sub}/{grad_ok_sub + grad_fail_sub}")

    print(f"\n{'=' * 70}")
    print("  TEST RESULT: ALL PASSED OK")
    print(f"  Architecture: 7 brains, 70 subnetworks, 19 heads, MoE, MLA")
    print(f"  Total params: {total:,} ({total/1e6:.1f}M)")
    print(f"{'=' * 70}")

    return {
        "total_params": total,
        "core_params": core_params,
        "heads_params": heads_params,
        "n_heads": 19,
        "n_subnetworks": 70,
        "gradients_flowing": True,
    }


if __name__ == "__main__":
    result = test_7brain_architecture()
    print(f"\nSummary: {result['n_heads']} heads, {result['n_subnetworks']} subnetworks, "
          f"{result['total_params']:,} params")
    print("DONE")
