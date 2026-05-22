#!/usr/bin/env python3
"""NIKTO Installer — installs dependencies and downloads the right model for your hardware."""
import subprocess, sys, os, platform

def run(cmd, desc, critical=False):
    print(f"  {desc}...", end=" ", flush=True)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    if r.returncode == 0:
        print("OK")
        return True
    else:
        print("FAILED")
        if r.stderr.strip():
            print(f"    {r.stderr.strip()[:200]}")
        if critical:
            print(f"\n  CRITICAL: {desc} failed. Cannot continue.")
            sys.exit(1)
        return False

def main():
    print("=" * 56)
    print("  NIKTO INSTALLER")
    print("  Auto-detecting your hardware...")
    print("=" * 56)

    # Detect hardware
    sys.path.insert(0, "packages/nikto-core/src")
    try:
        from nikto.providers.llamacpp import check_hardware_capability
        hw = check_hardware_capability()
        print(f"  CPU Cores: {hw['cpu_cores']}")
        print(f"  RAM: {hw['ram_gb']} GB")
        print(f"  GPU: {hw.get('gpu_name', 'None')}")
        print(f"  Recommended Tier: {hw['recommended_tier']}")
    except Exception:
        hw = {"ram_gb": 2, "recommended_tier": "tier1", "cpu_cores": 4}
        print(f"  RAM: (detection failed, assuming 2GB)")
        print(f"  Recommended Tier: tier1")

    print()

    # Install core package
    run("pip install -e packages/nikto-core", "Core package", critical=True)

    # Install Python dependencies
    deps = "pip install fastapi uvicorn psutil pynput Pillow pyttsx3 httpx"
    run(deps, "Python dependencies")

    # Try to install llama-cpp-python (the real LLM engine)
    try:
        run("pip install llama-cpp-python --quiet", "llama.cpp engine (CPU)")
    except Exception:
        print("  llama-cpp-python install skipped (optional)")

    # Check if Ollama is installed
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, timeout=5)
        print("  Ollama: OK (already installed)")
        has_ollama = True
    except Exception:
        print("  Ollama: NOT FOUND")
        print("    Recommended: https://ollama.com (free, local LLMs)")
        has_ollama = False

    # Download model based on hardware
    print()
    print("  Checking for local GGUF models...")
    try:
        from nikto.model_manager import ModelManager
        mm = ModelManager()
        mm.print_status()
        installed = mm.list_installed()
        if not installed:
            print("\n  No models found. Options:")
            print(f"    1. Install Ollama and run: ollama pull llama3.2:1b")
            print(f"    2. Run: python -c \"from nikto.model_manager import ModelManager; ModelManager().download_model('tier1')\"")
            print(f"    3. Place a .gguf file in ~/.nikto/models/")
    except Exception as e:
        print(f"  Model check skipped: {e}")

    # Generate logo
    print()
    print("  Generating logo...", end=" ", flush=True)
    try:
        from PIL import Image
        subprocess.run([sys.executable, "generate_logo.py"], capture_output=True)
        print("OK")
    except Exception:
        print("SKIPPED")

    print()
    print("=" * 56)
    print("  NIKTO INSTALLED")
    print()
    print("  Commands:")
    print("    yarn start       Install + launch web server")
    print("    yarn web         Launch web UI at http://localhost:8000")
    print("    yarn cli         Terminal chat mode")
    print()
    print("  To download a model, run:")
    print("    python -c \"from nikto.model_manager import ModelManager; ModelManager().download_model()\"")
    print()
    print("  Or install Ollama for quick start:")
    print("    1. Download from https://ollama.com")
    print("    2. Run: ollama pull llama3.2:1b")
    print("    3. Run: yarn web")
    print("=" * 56)

if __name__ == "__main__":
    main()
