#!/usr/bin/env python3
"""NIKTO Installer — Run: python install.py  or  yarn start"""
import subprocess, sys, os

def run(cmd, desc):
    print(f"  {desc}...", end=" ", flush=True)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode == 0:
        print("OK")
    else:
        print("FAILED")
        if r.stderr.strip():
            print(f"    {r.stderr.strip()[:200]}")
    return r.returncode == 0

def main():
    print("=" * 50)
    print("  NIKTO INSTALLER")
    print("  Just type what you know in English.")
    print("=" * 50)
    
    steps = [
        ("pip install -e packages/nikto-core", "Core package"),
        ("pip install fastapi uvicorn psutil pynput Pillow pyttsx3", "Dependencies"),
    ]
    for cmd, desc in steps:
        run(cmd, desc)
    
    # Generate logo
    print("  Generating logo...", end=" ", flush=True)
    try:
        from PIL import Image
        subprocess.run([sys.executable, "generate_logo.py"], capture_output=True)
        print("OK")
    except:
        print("SKIPPED")
    
    print("\n  NIKTO installed!")
    print("  Commands:")
    print("    yarn start       Install + launch web server")
    print("    yarn web         Launch web UI at http://localhost:8000")
    print("    yarn cli         Terminal chat mode")
    print("    yarn headless    Desktop avatar with voice chat")
    print()

if __name__ == "__main__":
    main()
