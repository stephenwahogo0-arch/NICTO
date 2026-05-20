#!/usr/bin/env python3
"""NIKTO Headless Mode — Desktop avatar with hotkey activation."""
from nikto.avatar.engine import AvatarEngine
from nikto.avatar.hotkeys import HotkeyManager

def on_activate():
    print("[NIKTO] Headless mode activated! (Space double-tap)")

engine = AvatarEngine()
print("=" * 56)
print("  NIKTO HEADLESS MODE")
print("  Keyboard Shortcuts:")
print("    Space (double-tap)  Activate NIKTO")
print("    Ctrl+Q              Quit")
print("    Ctrl+H              Toggle headless mode")
print("=" * 56)

hm = HotkeyManager(on_activate=on_activate)
hm.start()

try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[NIKTO] Shutting down...")
    hm.stop()
