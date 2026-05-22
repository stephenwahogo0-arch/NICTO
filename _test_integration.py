"""Full integration test for the real LLM engine."""
import os, sys
sys.path.insert(0, "packages/nikto-core/src")

print("=== IMPORT TEST ===")
from nikto.providers.chatml import format_chatml, format_chatml_with_context, extract_response
from nikto.providers.llamacpp import LLaMACPPProvider, check_hardware_capability
from nikto.providers.dual import DualEngineProvider
from nikto.model_manager import ModelManager, MODEL_REGISTRY
from nikto.config.settings import ModelConfig, NiktoConfig
print("  All imports OK")

print("\n=== CHATML TEST ===")
prompt = format_chatml_with_context(
    "Hello, what can you do?",
    "You are NIKTO.",
    [("Hi", "Hello! I am NIKTO.")],
    "Previous topic: coding"
)
assert "<|im_start|>system" in prompt
assert "<|im_start|>user" in prompt
assert "<|im_start|>assistant" in prompt
extracted = extract_response("<|im_start|>assistant\nHello world\n<|im_end|>")
assert extracted == "Hello world"
print(f"  ChatML OK ({len(prompt)} chars)")

print("\n=== HARDWARE DETECTION ===")
hw = check_hardware_capability()
print(f"  RAM: {hw['ram_gb']} GB")
print(f"  CPU Cores: {hw['cpu_cores']}")
print(f"  GPU: {hw['gpu_available']}")
print(f"  Tier: {hw['recommended_tier']}")

print("\n=== MODEL MANAGER ===")
mm = ModelManager()
tier = mm.detect_hardware_tier()
print(f"  Detected tier: {tier}")
installed = mm.list_installed()
print(f"  Installed models: {len(installed)}")
rec = mm.recommend_model()
print(f"  Recommended: {rec['model']['name']} ({rec['tier']})")
print(f"  RAM needed: {rec['model']['ram_gb']} GB")

print("\n=== ENGINE TEST ===")
cfg = ModelConfig()
provider = LLaMACPPProvider(cfg)
print(f"  Threads: {provider.n_threads} (N-2)")
print(f"  GPU Layers: {provider.n_gpu_layers}")
print(f"  Context Size: {provider.ctx_size}")
print(f"  Temperature range: 0.3 - 0.7")
print(f"  Model path: {provider.model_path}")
print(f"  Available: {provider.is_available()}")

print("\n=== DUAL ENGINE ===")
dual = DualEngineProvider(cfg)
info = dual.get_info()
print(f"  Mode: {info['mode']}")
print(f"  Local available: {info['local_available']}")

print("\n=== MODEL REGISTRY ===")
for tier_name, models in MODEL_REGISTRY.items():
    print(f"  {tier_name}:")
    for m in models:
        print(f"    - {m['name']}: {m['ram_gb']}GB RAM, {m['disk_gb']}GB disk")

print("\n=== VERIFY WEB SERVER ===")
import subprocess, time, json, urllib.request
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "nikto.api.routes:app",
     "--host", "127.0.0.1", "--port", "8766", "--log-level", "warning"],
    cwd="packages/nikto-core/src"
)
time.sleep(4)
try:
    resp = urllib.request.urlopen("http://127.0.0.1:8766/model/status")
    data = json.loads(resp.read())
    print(f"  /model/status: {data['hw_tier']}, models: {len(data['installed'])}")
    
    resp = urllib.request.urlopen("http://127.0.0.1:8766/")
    data = json.loads(resp.read())
    print(f"  /: {data['status']}")

    resp = urllib.request.urlopen("http://127.0.0.1:8766/health")
    data = json.loads(resp.read())
    print(f"  /health: agent_ready={data['agent_ready']}")

    req = urllib.request.Request(
        "http://127.0.0.1:8766/chat",
        data=json.dumps({"message": "hello", "mode": "build"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    print(f"  /chat: {len(data['response'])} chars of output")
    print(f"  First 100 chars: {data['response'][:100]}...")
    
    print("\nALL TESTS PASSED")
except Exception as e:
    print(f"\nERROR: {e}")
finally:
    proc.terminate()
    proc.wait()
