"""Desktop overlay renderer — transparent always-on-top avatar window using tkinter."""
import math
import os
import threading
import time
import tkinter as tk
from PIL import Image, ImageTk
from nikto.avatar.sprites import get_sprite, create_avatar_frame
from nikto.avatar.animations import AnimationPlayer, Expression


class AvatarRenderer:
    def __init__(self, width=200, height=300):
        self.width = width
        self.height = height
        self.root = None
        self.canvas = None
        self.photo_image = None
        self.tk_image = None
        self.running = False
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self._window = None
        self._thread = None
        self.anim_player = AnimationPlayer()
        self._lock = threading.Lock()

    def start(self, x=0, y=0):
        if self.running:
            return
        self.running = True
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self._thread = threading.Thread(target=self._run_tkinter, daemon=True)
        self._thread.start()
        time.sleep(0.3)

    def _run_tkinter(self):
        self.root = tk.Tk()
        self.root.title("NIKTO Avatar")
        self.root.geometry(f"{self.width}x{self.height}+{int(self.x)}+{int(self.y)}")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.configure(bg="black")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self.canvas.pack()
        self._update_loop()
        self.root.mainloop()

    def _update_loop(self):
        if not self.running:
            return
        dt = 0.05
        self.anim_player.update(dt)
        pose, expression, offset = self.anim_player.get_pose_and_expression()
        if abs(self.x - self.target_x) > 1 or abs(self.y - self.target_y) > 1:
            speed = 8.0
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            step = min(speed, dist)
            ratio = step / dist
            self.x += dx * ratio
            self.y += dy * ratio
            if pose != "walking":
                self.anim_player.play(self.anim_player.current_anim)
            self.root.geometry(f"{self.width}x{self.height}+{int(self.x)}+{int(self.y)}")
        img = get_sprite(pose, expression)
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(self.width // 2, self.height // 2, image=self.tk_image)
        self.root.after(int(dt * 1000), self._update_loop)

    def move_to(self, x, y):
        self.target_x = x
        self.target_y = y

    def set_animation(self, anim_type, loop=True):
        self.anim_player.play(anim_type, loop)

    def set_expression(self, expression: str):
        if self.anim_player.current_anim in (self.anim_player.current_anim,):
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
            mouth_shapes = ["O", "o", "_", "o"]
            shape = _r.choice(mouth_shapes)
            time.sleep(0.1)
        self.set_animation(self.anim_player.current_anim)

    def is_visible(self):
        return self.running and self._window is not None