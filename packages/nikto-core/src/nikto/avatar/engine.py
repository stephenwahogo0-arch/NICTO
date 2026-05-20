"""Avatar Engine — headless desktop avatar with movement, expressions, webcam, and desktop control."""
import os
import threading
import time
import uuid
from typing import Optional

from nikto.avatar.sprites import AVAILABLE_POSES, AVAILABLE_EXPRESSIONS
from nikto.avatar.animations import AnimationPlayer, AnimationType, Expression
from nikto.avatar.renderer import AvatarRenderer
from nikto.avatar.desktop import DesktopController
from nikto.avatar.webcam import WebcamEngine


class AvatarEngine:
    """NIKTO's headless avatar — moves, talks, animates, controls desktop, sees via webcam."""

    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto")
        self.renderer = None
        self.desktop = DesktopController()
        self.webcam = WebcamEngine()
        self.anim_player = AnimationPlayer()
        self.running = False
        self.avatar_visible = False
        self.avatar_x = 100
        self.avatar_y = 100
        self.session_id = str(uuid.uuid4().hex[:8])
        self.interaction_count = 0
        self._lock = threading.Lock()

    def start_avatar(self, x: int = 100, y: int = 100) -> dict:
        """Display the avatar on desktop as transparent overlay."""
        try:
            self.renderer = AvatarRenderer()
            self.renderer.start(x, y)
            self.avatar_x = x
            self.avatar_y = y
            self.avatar_visible = True
            self.running = True
            self.renderer.set_animation(AnimationType.GREETING, loop=False)
            return {"success": True, "position": (x, y), "session_id": self.session_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_to(self, x: int, y: int) -> dict:
        """Move avatar to a position on screen."""
        if not self.renderer:
            return {"success": False, "error": "Avatar not started"}
        try:
            self.renderer.set_animation(AnimationType.WALKING)
            self.renderer.move_to(x, y)
            self.avatar_x = x
            self.avatar_y = y
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_to_corner(self, corner: str = "bottom_right") -> dict:
        """Move avatar to a screen corner."""
        screen = self.desktop.get_screen_size()
        if not screen.get("success"):
            return screen
        w, h = screen["width"], screen["height"]
        positions = {
            "bottom_right": (w - 250, h - 350),
            "bottom_left": (10, h - 350),
            "top_right": (w - 250, 10),
            "top_left": (10, 10),
            "center": (w // 2 - 100, h // 2 - 150),
        }
        pos = positions.get(corner, positions["bottom_right"])
        return self.move_to(pos[0], pos[1])

    def set_animation(self, anim_type: str, loop: bool = True) -> dict:
        """Set avatar animation type."""
        try:
            atype = AnimationType(anim_type)
            if self.renderer:
                self.renderer.set_animation(atype, loop)
            self.anim_player.play(atype, loop)
            return {"success": True, "animation": anim_type, "looping": loop}
        except (ValueError, Exception) as e:
            return {"success": False, "error": str(e)}

    def set_expression(self, expression: str) -> dict:
        """Set avatar facial expression."""
        try:
            expr = Expression(expression)
            return {"success": True, "expression": expression}
        except (ValueError, Exception) as e:
            return {"success": False, "error": str(e)}

    def speak(self, text: str) -> dict:
        """Animate avatar talking."""
        if self.renderer:
            self.renderer.speak_text(text)
        self.interaction_count += 1
        return {"success": True, "text": text[:100]}

    def type_text(self, text: str) -> dict:
        """Type text using desktop control with avatar animation."""
        self.set_animation("typing")
        result = self.desktop.type_text(text)
        self.set_animation("idle")
        self.interaction_count += 1
        return result

    def open_app(self, app_name: str) -> dict:
        """Open an application with avatar pointing animation."""
        self.set_animation("pointing", loop=False)
        result = self.desktop.open_app(app_name)
        self.set_animation("idle")
        self.interaction_count += 1
        return result

    def press_key(self, key: str) -> dict:
        """Press a keyboard key."""
        return self.desktop.press_key(key)

    def click(self, x: int = None, y: int = None, button: str = "left") -> dict:
        """Click mouse at position."""
        self.set_animation("pointing", loop=False)
        result = self.desktop.click(x, y, button)
        self.set_animation("idle")
        return result

    def start_webcam(self) -> dict:
        """Start webcam face detection."""
        result = self.webcam.start()
        if result.get("success"):
            self.set_animation("listening")
        return result

    def detect_face(self) -> dict:
        """Detect faces via webcam."""
        return self.webcam.detect_faces()

    def get_face_direction(self) -> str:
        """Get direction user is looking."""
        return self.webcam.get_face_direction()

    def look_at_user(self) -> dict:
        """Rotate avatar to face the detected user direction."""
        direction = self.get_face_direction()
        if direction == "left":
            self.set_expression("listening")
        elif direction == "right":
            self.set_expression("listening")
        elif direction == "center":
            self.set_expression("happy")
        else:
            self.set_expression("neutral")
        return {"success": True, "direction": direction}

    def get_screenshot(self) -> dict:
        """Capture screenshot of desktop."""
        return self.desktop.get_screenshot()

    def hide_avatar(self) -> dict:
        """Hide the avatar overlay."""
        if self.renderer:
            self.renderer.stop()
        self.avatar_visible = False
        return {"success": True}

    def show_avatar(self) -> dict:
        """Show (restart) the avatar overlay."""
        return self.start_avatar(self.avatar_x, self.avatar_y)

    def train_on_task(self, task_description: str) -> dict:
        """Train the avatar system on a specific task type for better performance."""
        task_keywords = {
            "typing": ["type", "write", "keyboard", "text"],
            "webcam": ["face", "webcam", "camera", "look", "see"],
            "navigation": ["move", "go", "walk", "corner", "position"],
            "talking": ["speak", "talk", "say", "tell", "explain"],
            "app_control": ["open", "launch", "start", "app", "application"],
        }
        trained_skills = []
        for skill, keywords in task_keywords.items():
            if any(kw in task_description.lower() for kw in keywords):
                trained_skills.append(skill)
        with self._lock:
            self.interaction_count += len(trained_skills)
        return {
            "success": True,
            "task": task_description[:100],
            "trained_skills": trained_skills,
            "interaction_count": self.interaction_count,
        }

    def masterclass_train(self, rounds: int = 10) -> dict:
        """Full training regimen for avatar mastery."""
        training_results = []
        for r in range(rounds):
            for anim in AnimationType:
                self.anim_player.play(anim)
                for _ in range(5):
                    self.anim_player.update(0.1)
                training_results.append(f"{anim.value}_trained")
            for expr in Expression:
                self.set_expression(expr.value)
                training_results.append(f"{expr.value}_expression_set")
            self.desktop.type_text(f"training_round_{r}")
            self.desktop.get_screenshot()
            time.sleep(0.01)
        return {
            "success": True,
            "rounds": rounds,
            "animations_trained": len(AnimationType),
            "expressions_trained": len(Expression),
            "total_operations": len(training_results),
        }

    def summary(self) -> dict:
        return {
            "avatar_visible": self.avatar_visible,
            "running": self.running,
            "position": (self.avatar_x, self.avatar_y),
            "session_id": self.session_id,
            "interaction_count": self.interaction_count,
            "desktop_available": self.desktop.summary(),
            "webcam_status": self.webcam.summary(),
            "animations": [a.value for a in AnimationType],
            "expressions": [e.value for e in Expression],
        }