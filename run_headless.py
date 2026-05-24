#!/usr/bin/env python3
"""KYROS Headless Mode — Desktop avatar with hotkey activation."""
from kyros.avatar.engine import AvatarEngine
from kyros.avatar.hotkeys import HotkeyManager

def on_activate():
    print("[KYROS] Headless mode activated! (Space double-tap)")

engine = AvatarEngine()
print("=" * 56)
print("  KYROS HEADLESS MODE")
print("  Keyboard Shortcuts:")
print("    Space (double-tap)  Activate KYROS")
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
    print("\n[KYROS] Shutting down...")
    hm.stop()
