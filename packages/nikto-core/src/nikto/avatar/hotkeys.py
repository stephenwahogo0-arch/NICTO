"""Global hotkey listener for NIKTO activation."""
import time
import threading
from typing import Callable

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class HotkeyManager:
    def __init__(self, on_activate: Callable):
        self.on_activate = on_activate
        self.last_space_time = 0
        self.running = False
        self._thread = None

    def start(self):
        if not PYNPUT_AVAILABLE:
            return
        self.running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        with keyboard.Listener(on_press=self._on_press) as listener:
            while self.running:
                time.sleep(0.1)
            listener.stop()

    def _on_press(self, key):
        if key == keyboard.Key.space:
            now = time.time()
            if now - self.last_space_time < 0.3:
                self.on_activate()
                self.last_space_time = 0
            else:
                self.last_space_time = now

    def stop(self):
        self.running = False
