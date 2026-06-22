"""Desktop overlay renderer using PyQt6 — adaptive framerate for 365-day thermal safety.

Framerate tiers:
  IDLE   (4 FPS)  — avatar static, same frame, no movement
  ACTIVE (30 FPS) — animation playing, expression changing
  MOVING (60 FPS) — smooth motion across screen

Cache-hit path skips all QPainter work when nothing changed.
"""
import math
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from kyros.avatar.sprites import get_sprite, AVATAR_WIDTH, AVATAR_HEIGHT
from kyros.avatar.animations import AnimationPlayer, Expression


# Framerate tiers (Hz)
FPS_MOVING = 60
FPS_ACTIVE = 30
FPS_IDLE   = 4

MOVEMENT_THRESHOLD = 0.5
IDLE_FRAME_TIMEOUT = 2.0  # seconds before dropping to IDLE framerate


class QtAvatarRenderer:
    def __init__(self, width=AVATAR_WIDTH, height=AVATAR_HEIGHT):
        self.width = width
        self.height = height
        self.app = None
        self.window = None
        self.label = None
        self.timer = None
        self.running = False
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.anim_player = AnimationPlayer()
        self._last_render_time = 0.0

        # Frame-change detection (skip re-render when nothing changed)
        self._last_pose = None
        self._last_expression = None
        self._last_hologram_text = ""
        self._cached_pixmap = None
        self._hologram_cache = None

        # Movement parameters
        self.MOVE_SPEED = 400.0

        # Idle -> active tracking
        self._last_activity_time = time.time()
        self._current_tier = FPS_IDLE

        # Movement detection
        self._was_moving = False

    def start(self, x=0, y=0):
        if self.running:
            return

        self.running = True
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y

        try:
            self.app = QApplication.instance() or QApplication([])
            self.window = QMainWindow()
            self.window.setWindowTitle("KYROS Avatar")
            self.window.setGeometry(x, y, self.width, self.height)

            self.window.setWindowFlag(Qt.WindowType.FramelessWindowHint)
            self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

            self.label = QLabel()
            self.label.setFixedSize(self.width, self.height)
            self.window.setCentralWidget(self.label)
            self.window.show()

            self.timer = QTimer()
            self.timer.timeout.connect(self._update_loop)
            self._set_framerate(FPS_ACTIVE)  # start at active to init

        except Exception as e:
            print(f"Failed to initialize Qt avatar: {e}")
            self.running = False

    def _set_framerate(self, fps):
        """Dynamically adjust timer interval. Clamped to sane range."""
        fps = max(FPS_IDLE, min(FPS_MOVING, fps))
        if self.timer:
            self.timer.setInterval(int(1000 / fps))
        self._current_tier = fps

    def _update_loop(self):
        if not self.running or not self.window:
            return

        now = time.time()
        dt = min(now - self._last_render_time, 0.1)
        self._last_render_time = now

        self.anim_player.update(dt)
        pose, expression, offset = self.anim_player.get_pose_and_expression()

        # --- Movement ---
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        is_moving = dist > MOVEMENT_THRESHOLD

        if is_moving:
            step = min(self.MOVE_SPEED * dt, dist)
            ratio = step / max(dist, 0.001)
            self.x += dx * ratio
            self.y += dy * ratio

            if self.window:
                self.window.move(int(self.x), int(self.y))

            if dist > 5.0 and self.anim_player.current_anim.value != "walking":
                self.anim_player.play("walking")
            elif dist <= 5.0 and self.anim_player.current_anim.value == "walking":
                self.anim_player.play("idle")

        # --- Adaptive framerate ---
        frame_changed = (pose != self._last_pose or expression != self._last_expression)

        if is_moving:
            self._set_framerate(FPS_MOVING)
            self._last_activity_time = now
        elif frame_changed or self._hologram_text != self._last_hologram_text:
            self._set_framerate(FPS_ACTIVE)
            self._last_activity_time = now
        else:
            idle_seconds = now - self._last_activity_time
            if idle_seconds > IDLE_FRAME_TIMEOUT:
                self._set_framerate(FPS_IDLE)
            else:
                self._set_framerate(FPS_ACTIVE)

        # --- Render (only when something changed) ---
        if frame_changed or is_moving or self._hologram_text != self._last_hologram_text:
            self._render_frame(pose, expression)
            self._last_pose = pose
            self._last_expression = expression
            self._last_hologram_text = self._hologram_text

    def _render_frame(self, pose, expression):
        if not self.label:
            return

        try:
            img = get_sprite(pose, expression)
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qim = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)

            if self._hologram_text:
                qim = self._render_hologram(qim, img.width, img.height)

            pixmap = QPixmap.fromImage(qim)
            self.label.setPixmap(pixmap)

        except Exception as e:
            print(f"Error rendering frame: {e}")

    def _render_hologram(self, base_image, base_w, base_h):
        """Hologram overlay — cached when text unchanged to avoid QPainter every frame."""
        if self._hologram_cache and self._last_hologram_text == self._hologram_text:
            return self._hologram_cache

        canvas_w = base_w * 2
        canvas_h = base_h
        canvas = QImage(canvas_w, canvas_h, QImage.Format.Format_RGBA8888)
        canvas.fill(QColor(0, 0, 0, 0))

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawImage(0, 0, base_image)

        hx, hy = base_w + 10, 20
        hw, hh = 150, 80

        painter.setPen(QColor(0, 180, 255, 150))
        painter.setBrush(QColor(0, 180, 255, 40))
        painter.drawRoundedRect(hx, hy, hw, hh, 10, 10)

        painter.setPen(QColor(0, 255, 255, 150))
        painter.setBrush(QColor(0, 0, 0, 0))
        painter.drawRect(hx, hy, hw, hh)

        painter.setPen(QColor(0, 255, 255, 200))
        font = QFont()
        font.setPixelSize(14)
        painter.setFont(font)
        painter.drawText(hx + 10, hy + 25, f"TASK: {self._hologram_text[:50]}")

        painter.setPen(QColor(0, 255, 0, 255))
        painter.drawText(10, 25, "NET: ACTIVE")

        painter.end()

        self._hologram_cache = canvas
        return canvas

    def move_to(self, x, y):
        self.target_x = x
        self.target_y = y

    def set_animation(self, anim_type, loop=True):
        self.anim_player.play(anim_type, loop)

    def set_expression(self, expression: str):
        if expression in [e.value for e in Expression]:
            self.anim_player.set_expression(Expression(expression))

    def set_hologram(self, text: str):
        self._hologram_text = text

    def speak_text(self, text: str, duration: float = None):
        from kyros.avatar.animations import PHONEME_MAP
        words = text.lower().split()
        dur_per_word = (duration or max(1.0, len(words) * 0.3)) / max(1, len(words))
        old_expr = self.anim_player.current_expression
        self.set_expression("speaking")

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.stop()
        if self.window:
            self.window.close()
        if self.app:
            self.app.quit()

    def is_visible(self):
        return self.running and self.window is not None and not self.window.isHidden()
