#!/usr/bin/env python3
"""
NICTO Real AI — Hardware Setup
Detects available hardware and selects best base model.
"""
import json, os, sys, shutil
from pathlib import Path


def check_gpu():
    import subprocess, sys
    code = (
        "import sys; sys.path.insert(0, r'{}'); "
        "try:\n"
        "    import torch\n"
        "    if torch.cuda.is_available():\n"
        "        print(torch.cuda.get_device_name(0))\n"
        "        print(torch.cuda.get_device_properties(0).total_memory / 1e9)\n"
        "        print(torch.version.cuda)\n"
        "    else:\n"
        "        print('NONE')\n"
        "        print(0)\n"
        "        print('N/A')\n"
        "except ImportError:\n"
        "    print('NONE')\n"
        "    print(0)\n"
        "    print('N/A')\n"
    ).format(os.path.dirname(__file__))
    try:
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
        lines = r.stdout.strip().split('\n')
        name = lines[0].strip() if len(lines) > 0 else "NONE"
        vram = float(lines[1].strip()) if len(lines) > 1 else 0.0
        cuda = lines[2].strip() if len(lines) > 2 else "N/A"
        available = name != "NONE"
        return {"available": available, "name": name, "vram_gb": round(vram, 1), "cuda_version": cuda}
    except (subprocess.TimeoutExpired, Exception):
        return {"available": False, "name": "NONE", "vram_gb": 0.0, "cuda_version": "N/A"}


def check_unsloth():
    try:
        import unsloth
        try:
            _ = unsloth.__version__
            return {"installed": True, "version": unsloth.__version__}
        except Exception:
            return {"installed": True, "version": "unknown"}
    except (ImportError, NotImplementedError):
        return {"installed": False}


def check_disk():
    total, used, free = shutil.disk_usage("/")
    return {"free_gb": round(free / 1e9, 1), "total_gb": round(total / 1e9, 1)}


def check_ram():
    try:
        import psutil
        m = psutil.virtual_memory()
        return {"total_gb": round(m.total / 1e9, 1), "available_gb": round(m.available / 1e9, 1)}
    except ImportError:
        return {"total_gb": 0, "available_gb": 0}


def select_best_model(vram_gb: float, ram_gb: float, unsloth_ok: bool) -> dict:
    models = [
        {"name": "unsloth/Meta-Llama-3.1-405B-Instruct-bnb-4bit", "display": "LLaMA 3.1 405B (4-bit)", "params": "405B", "vram_gb": 200.0, "disk_gb": 220, "rank": 1, "requires_unsloth": True},
        {"name": "unsloth/Mixtral-8x22B-Instruct-v0.1-bnb-4bit", "display": "Mixtral 8x22B MoE (4-bit)", "params": "141B MoE", "vram_gb": 80.0, "disk_gb": 85, "rank": 2, "requires_unsloth": True},
        {"name": "unsloth/Meta-Llama-3.1-70B-Instruct-bnb-4bit", "display": "LLaMA 3.1 70B (4-bit)", "params": "70B", "vram_gb": 44.0, "disk_gb": 42, "rank": 3, "requires_unsloth": True},
        {"name": "unsloth/Qwen2.5-72B-Instruct-bnb-4bit", "display": "Qwen 2.5 72B (4-bit)", "params": "72B", "vram_gb": 44.0, "disk_gb": 43, "rank": 4, "requires_unsloth": True},
    ]

    cpu_models = [
        {"name": "Qwen/Qwen2.5-1.5B-Instruct", "display": "Qwen 2.5 1.5B (4-bit CPU)", "params": "1.5B", "ram_gb": 3.0, "disk_gb": 3.5, "rank": 5, "requires_unsloth": False},
        {"name": "meta-llama/Llama-3.2-1B-Instruct", "display": "Llama 3.2 1B (4-bit CPU)", "params": "1B", "ram_gb": 2.0, "disk_gb": 2.5, "rank": 6, "requires_unsloth": False},
        {"name": "microsoft/Phi-3-mini-4k-instruct", "display": "Phi-3-mini 3.8B (4-bit CPU)", "params": "3.8B", "ram_gb": 5.0, "disk_gb": 8.0, "rank": 7, "requires_unsloth": False},
    ]

    if vram_gb > 0:
        for m in models:
            if vram_gb >= m["vram_gb"] and (not m["requires_unsloth"] or unsloth_ok):
                return {**m, "mode": "gpu"}
        return {**models[-1], "mode": "gpu"} if unsloth_ok else {**models[-1], "mode": "gpu"}

    for m in cpu_models:
        if ram_gb >= m["ram_gb"]:
            return {**m, "mode": "cpu"}
    return {**cpu_models[-1], "mode": "cpu"}


def run():
    print("=" * 60)
    print("NICTO REAL AI — HARDWARE SETUP")
    print("=" * 60)

    gpu = check_gpu()
    unsloth = check_unsloth()
    disk = check_disk()
    ram = check_ram()

    print(f"\n  GPU:         {gpu.get('name', 'NONE')} ({gpu.get('vram_gb', 0)}GB VRAM)" if gpu["available"] else "\n  GPU:         NONE (CPU only)")
    print(f"  CUDA:        {gpu.get('cuda_version', 'N/A')}" if gpu["available"] else "")
    print(f"  Unsloth:     {unsloth.get('version', 'NOT INSTALLED')}")
    print(f"  RAM:         {ram['total_gb']}GB total ({ram['available_gb']}GB free)")
    print(f"  Disk:        {disk['total_gb']}GB total ({disk['free_gb']}GB free)")

    vram = gpu.get("vram_gb", 0.0)
    selected = select_best_model(vram, ram.get("available_gb", 0), unsloth["installed"])

    print(f"\n  Selected:    {selected['display']}")
    print(f"  Parameters:  {selected['params']}")
    print(f"  Mode:        {selected['mode']}")
    print(f"  Disk needed: {selected['disk_gb']}GB (free: {disk['free_gb']}GB)")

    config = {
        "base_model": selected["name"],
        "model_display": selected["display"],
        "model_params": selected["params"],
        "vram_gb": vram,
        "ram_gb": ram.get("available_gb", 0),
        "disk_gb": disk["free_gb"],
        "gpu_name": gpu.get("name", "NONE"),
        "unsloth_installed": unsloth["installed"],
        "mode": selected["mode"],
    }

    with open("nicto_neural/hardware_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n  Config saved to nicto_neural/hardware_config.json")

    if not gpu["available"]:
        print("\n  NOTE: No GPU detected. Training will need a cloud GPU.")
        print("  Run: python nicto_neural/build_training_data.py")
        print("  Then train on cloud and run locally with CPU mode.")
    else:
        print("\n  GPU detected! Ready for training.")
        print("  Run: python nicto_neural/train_nicto.py")

    return config


if __name__ == "__main__":
    run()
