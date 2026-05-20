"""Desktop overlay renderer — smooth 60fps transparent always-on-top avatar window."""
import math
import os
import threading
import time
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter, ImageEnhance
from nikto.avatar.sprites import get_sprite, create_avatar_frame, AVATAR_WIDTH, AVATAR_HEIGHT
from nikto.avatar.animations import AnimationPlayer, Expression


FPS = 60
FRAME_DT = 1.0 / FPS
MOVE_SPEED = 400.0  # pixels per second


class AvatarRenderer:
    def __init__(self, width=AVATAR_WIDTH, height=AVATAR_HEIGHT):
        self.width = width
        self.height = height
        self.root = None
        self.canvas = None
        self.photo_image = None
        self.tk_images = {}  # Double buffer
        self.running = False
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        self._window = None
        self._thread = None
        self.anim_player = AnimationPlayer()
        self._lock = threading.Lock()
        self._last_time = 0.0
        self._frame_count = 0
        self._fps_display = 0

    def start(self, x=0, y=0):
        if self.running:
            return
        self.running = True
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self._thread = threading.Thread(target=self._run_tkinter, daemon=True)
        self._thread.start()
        time.sleep(0.5)

    def _run_tkinter(self):
        self.root = tk.Tk()
        self.root.title("NIKTO Avatar")
        self.root.geometry(f"{int(self.width)}x{int(self.height)}+{int(self.x)}+{int(self.y)}")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.configure(bg="black")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self.canvas.pack()
        self._last_time = time.time()
        self._update_loop()
        self.root.mainloop()

    def _update_loop(self):
        if not self.running:
            return
        now = time.time()
        dt = min(now - self._last_time, 0.1)
        self._last_time = now

        self.anim_player.update(dt)
        pose, expression, offset = self.anim_player.get_pose_and_expression()

        # Smooth movement with acceleration
        if abs(self.x - self.target_x) > 0.5 or abs(self.y - self.target_y) > 0.5:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            step = min(MOVE_SPEED * dt, dist)
            ratio = step / max(dist, 0.001)
            self.x += dx * ratio
            self.y += dy * ratio
            if self.anim_player.current_anim.value != "walking":
                self.anim_player.play(self.anim_player.current_anim)
            self.root.geometry(f"{self.width}x{self.height}+{int(self.x)}+{int(self.y)}")

        # Render with double buffering
        img = get_sprite(pose, expression)
        self.tk_images[0] = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(self.width // 2, self.height // 2, image=self.tk_images[0])

        # FPS counter (debug optional)
        self._frame_count += 1

        self.root.after(int(FRAME_DT * 1000), self._update_loop)

    def move_to(self, x, y):
        self.target_x = float(x)
        self.target_y = float(y)

    def set_animation(self, anim_type, loop=True):
        self.anim_player.play(anim_type, loop)

    def set_expression(self, expression: str):
        pass

    def stop(self):
        self.running = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass

    def speak_text(self, text: str, duration: float = None):
        import random as _r
        words = len(text.split())
        dur = duration or max(1.0, words * 0.2)
        self.set_animation(self.anim_player.current_anim)
        end_time = time.time() + dur
        while time.time() < end_time and self.running:
            _r.choice(["O", "o", "_", "o"])
            time.sleep(0.05)

    def is_visible(self):
        return self.running and self._window is not None