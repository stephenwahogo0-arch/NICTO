from __future__ import annotations

"""KYROS Core Engine — ECS-based real-time game engine with physics, rendering, audio.
Runs directly via Pygame CE. No external tools required."""

import math
import os
import random
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None


# ============================================================
# COMPONENTS
# ============================================================

class Component:
    def __init__(self):
        self._game_object: Optional["GameObject"] = None

    @property
    def transform(self) -> "Transform":
        return self._game_object.transform if self._game_object else None

    def awake(self): pass
    def start(self): pass
    def update(self, dt: float): pass
    def late_update(self, dt: float): pass
    def on_destroy(self): pass


class Transform(Component):
    def __init__(self, x=0.0, y=0.0, rotation=0.0, scale_x=1.0, scale_y=1.0):
        super().__init__()
        self.x = x
        self.y = y
        self.rotation = rotation
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.parent: Optional[Transform] = None
        self.children: list[Transform] = []

    @property
    def world_x(self) -> float:
        if self.parent:
            return self.parent.world_x + self.x
        return self.x

    @property
    def world_y(self) -> float:
        if self.parent:
            return self.parent.world_y + self.y
        return self.y

    @property
    def position(self) -> tuple:
        return (self.x, self.y)

    @position.setter
    def position(self, pos: tuple):
        self.x, self.y = pos

    def translate(self, dx: float, dy: float):
        self.x += dx
        self.y += dy

    def set_parent(self, parent_transform: "Transform"):
        if self.parent:
            self.parent.children.remove(self)
        self.parent = parent_transform
        if parent_transform:
            parent_transform.children.append(self)

    def look_at(self, target_x: float, target_y: float):
        self.rotation = math.atan2(target_y - self.y, target_x - self.x)


class SpriteRenderer(Component):
    def __init__(self, image_path: str = "", color=(255, 255, 255), width=32, height=32, alpha=255, flip_x=False, flip_y=False, pivot=(0.5, 0.5)):
        super().__init__()
        self.image_path = image_path
        self.color = color
        self.width = width
        self.height = height
        self.alpha = alpha
        self.flip_x = flip_x
        self.flip_y = flip_y
        self.pivot = pivot
        self._surface = None
        self._original = None
        self.visible = True
        self.layer = 0
        self._load_image()

    def _load_image(self):
        if self.image_path and os.path.exists(self.image_path):
            try:
                self._original = pygame.image.load(self.image_path).convert_alpha()
                self.width = self._original.get_width()
                self.height = self._original.get_height()
            except Exception:
                self._original = None
        if self._original is None:
            self._original = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._original.fill(self.color)

    def set_image(self, path: str):
        self.image_path = path
        self._load_image()

    def set_color(self, color: tuple):
        self.color = color
        if self._original and not self.image_path:
            self._original.fill(self.color)

    def get_render_surface(self) -> Optional[pygame.Surface]:
        if not self.visible or not PYGAME_AVAILABLE:
            return None
        surf = self._original
        if surf is None:
            return None
        if self.alpha < 255:
            surf = surf.copy()
            surf.set_alpha(self.alpha)
        if self.flip_x or self.flip_y:
            surf = pygame.transform.flip(surf, self.flip_x, self.flip_y)
        if self.transform and self.transform.rotation != 0:
            surf = pygame.transform.rotate(surf, math.degrees(self.transform.rotation))
        if self.transform and (self.transform.scale_x != 1.0 or self.transform.scale_y != 1.0):
            new_w = max(1, int(self.width * self.transform.scale_x))
            new_h = max(1, int(self.height * self.transform.scale_y))
            surf = pygame.transform.scale(surf, (new_w, new_h))
        return surf


class PhysicsBody(Component):
    def __init__(self, velocity_x=0.0, velocity_y=0.0, gravity=0.0, mass=1.0, friction=0.0, bounciness=0.0, max_speed=1000.0):
        super().__init__()
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.gravity = gravity
        self.mass = mass
        self.friction = friction
        self.bounciness = bounciness
        self.max_speed = max_speed
        self.use_gravity = False
        self.is_kinematic = False
        self.forces: list[tuple[float, float]] = []
        self.grounded = False

    def add_force(self, fx: float, fy: float):
        self.forces.append((fx, fy))

    def update(self, dt: float):
        if self.is_kinematic:
            return
        if self.use_gravity:
            self.velocity_y += self.gravity * dt * 60
        for fx, fy in self.forces:
            self.velocity_x += fx / self.mass * dt * 60
            self.velocity_y += fy / self.mass * dt * 60
        self.forces.clear()
        speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.velocity_x *= scale
            self.velocity_y *= scale
        if self.friction > 0 and self.grounded:
            self.velocity_x *= (1.0 - self.friction * dt * 60)
        if self.transform:
            self.transform.translate(self.velocity_x * dt * 60, self.velocity_y * dt * 60)


class BoxCollider(Component):
    def __init__(self, width=32, height=32, offset_x=0, offset_y=0, is_trigger=False, tag=""):
        super().__init__()
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.is_trigger = is_trigger
        self.tag = tag
        self.enabled = True

    @property
    def rect(self) -> tuple:
        if self.transform:
            return (self.transform.world_x + self.offset_x - self.width * self.transform.scale_x / 2,
                    self.transform.world_y + self.offset_y - self.height * self.transform.scale_y / 2,
                    self.width * self.transform.scale_x,
                    self.height * self.transform.scale_y)
        return (0, 0, self.width, self.height)

    def check_collision(self, other: "BoxCollider") -> bool:
        if not self.enabled or not other.enabled:
            return False
        x1, y1, w1, h1 = self.rect
        x2, y2, w2, h2 = other.rect
        return (x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2)

    def get_collision_normal(self, other: "BoxCollider") -> Optional[tuple]:
        x1, y1, w1, h1 = self.rect
        x2, y2, w2, h2 = other.rect
        overlap_left = (x1 + w1) - x2
        overlap_right = (x2 + w2) - x1
        overlap_top = (y1 + h1) - y2
        overlap_bottom = (y2 + h2) - y1
        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
        if min_overlap == overlap_left: return (-1, 0)
        elif min_overlap == overlap_right: return (1, 0)
        elif min_overlap == overlap_top: return (0, -1)
        else: return (0, 1)


class CircleCollider(Component):
    def __init__(self, radius=16, offset_x=0, offset_y=0, is_trigger=False, tag=""):
        super().__init__()
        self.radius = radius
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.is_trigger = is_trigger
        self.tag = tag
        self.enabled = True

    @property
    def center(self) -> tuple:
        if self.transform:
            return (self.transform.world_x + self.offset_x, self.transform.world_y + self.offset_y)
        return (0, 0)

    def check_collision(self, other: "CircleCollider") -> bool:
        if not self.enabled or not other.enabled:
            return False
        dx = self.center[0] - other.center[0]
        dy = self.center[1] - other.center[1]
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < self.radius + other.radius

    def check_collision_rect(self, rect_collider: BoxCollider) -> bool:
        rx, ry, rw, rh = rect_collider.rect
        cx, cy = self.center
        closest_x = max(rx, min(cx, rx + rw))
        closest_y = max(ry, min(cy, ry + rh))
        dx = cx - closest_x
        dy = cy - closest_y
        return (dx*dx + dy*dy) < self.radius * self.radius


class Camera(Component):
    def __init__(self, viewport_width=800, viewport_height=600, zoom=1.0, follow_target=None):
        super().__init__()
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.zoom = zoom
        self.follow_target = follow_target
        self.offset_x = 0
        self.offset_y = 0
        self.background_color = (10, 10, 30)
        self.is_primary = True

    def update(self, dt: float):
        if self.follow_target and self.follow_target.transform:
            target = self.follow_target.transform
            self.offset_x += (target.world_x - self.viewport_width/2 - self.offset_x) * min(1, dt * 8)
            self.offset_y += (target.world_y - self.viewport_height/2 - self.offset_y) * min(1, dt * 8)

    def world_to_screen(self, world_x: float, world_y: float) -> tuple:
        return ((world_x - self.offset_x) * self.zoom + self.viewport_width/2,
                (world_y - self.offset_y) * self.zoom + self.viewport_height/2)


class AudioSource(Component):
    def __init__(self, sound_path="", volume=1.0, loop=False, auto_play=False):
        super().__init__()
        self.sound_path = sound_path
        self.volume = volume
        self.loop = loop
        self.auto_play = auto_play
        self._sound = None
        self._playing = False
        if sound_path and PYGAME_AVAILABLE:
            self._load()

    def _load(self):
        if os.path.exists(self.sound_path):
            try:
                self._sound = pygame.mixer.Sound(self.sound_path)
                self._sound.set_volume(self.volume)
            except Exception:
                pass

    def play(self):
        if self._sound and PYGAME_AVAILABLE:
            self._sound.play(loops=-1 if self.loop else 0)
            self._playing = True

    def stop(self):
        if self._sound and PYGAME_AVAILABLE:
            self._sound.stop()
            self._playing = False

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))
        if self._sound:
            self._sound.set_volume(self.volume)


class ParticleSystem(Component):
    def __init__(self, rate=10, max_particles=100, lifetime=1.0, speed=50, start_color=(255,255,255), end_color=(255,255,255,0), start_size=4, end_size=1, gravity=0, spread=math.pi*2):
        super().__init__()
        self.rate = rate
        self.max_particles = max_particles
        self.lifetime = lifetime
        self.speed = speed
        self.start_color = start_color
        self.end_color = end_color
        self.start_size = start_size
        self.end_size = end_size
        self.gravity = gravity
        self.spread = spread
        self.emitting = True
        self.particles: list[dict] = []
        self._accumulator = 0

    def update(self, dt: float):
        if self.emitting:
            self._accumulator += dt * self.rate
            while self._accumulator >= 1 and len(self.particles) < self.max_particles:
                angle = random.uniform(-self.spread/2, self.spread/2)
                spd = random.uniform(self.speed * 0.5, self.speed * 1.5)
                self.particles.append({
                    "x": self.transform.world_x if self.transform else 0,
                    "y": self.transform.world_y if self.transform else 0,
                    "vx": math.cos(angle) * spd,
                    "vy": math.sin(angle) * spd,
                    "life": self.lifetime,
                    "max_life": self.lifetime,
                    "size": self.start_size,
                })
                self._accumulator -= 1
        dead = []
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["vy"] += self.gravity * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                dead.append(p)
        for p in dead:
            self.particles.remove(p)

    def render(self, surface: pygame.Surface, camera: Camera = None):
        if not PYGAME_AVAILABLE:
            return
        for p in self.particles:
            t = 1.0 - p["life"] / p["max_life"]
            size = self.start_size + (self.end_size - self.start_size) * t
            color = tuple(int(a + (b - a) * t) for a, b in zip(self.start_color[:3], self.end_color[:3]))
            alpha = int(self.start_color[3] if len(self.start_color) > 3 else 255 * (1 - t))
            sx, sy = p["x"], p["y"]
            if camera:
                sx, sy = camera.world_to_screen(sx, sy)
            s = pygame.Surface((max(1, int(size*2)), max(1, int(size*2))), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, min(255, max(0, alpha))), (size, size), size)
            surface.blit(s, (sx - size, sy - size))


class TextLabel(Component):
    def __init__(self, text="", font_size=16, color=(255, 255, 255), font_name=None, bold=False, italic=False, align="center"):
        super().__init__()
        self.text = text
        self.font_size = font_size
        self.color = color
        self.font_name = font_name
        self.bold = bold
        self.italic = italic
        self.align = align
        self.visible = True
        self.layer = 100
        self.background = None
        self.padding = (4, 2)
        self._font = None
        self._surface = None
        self._dirty = True
        if PYGAME_AVAILABLE:
            self._load_font()

    def _load_font(self):
        try:
            if self.font_name and os.path.exists(self.font_name):
                self._font = pygame.font.Font(self.font_name, self.font_size)
            else:
                self._font = pygame.font.Font(None, self.font_size)
            if self.bold:
                self._font.set_bold(True)
            if self.italic:
                self._font.set_italic(True)
        except Exception:
            self._font = pygame.font.Font(None, self.font_size)

    def set_text(self, text: str):
        if text != self.text:
            self.text = text
            self._dirty = True

    def get_surface(self) -> Optional[pygame.Surface]:
        if not PYGAME_AVAILABLE or not self.visible:
            return None
        if self._surface is None or self._dirty:
            if self._font is None:
                self._load_font()
            self._surface = self._font.render(self.text, True, self.color)
            if self.background:
                bg = pygame.Surface((self._surface.get_width() + self.padding[0]*2,
                                     self._surface.get_height() + self.padding[1]*2))
                bg.fill(self.background)
                bg.blit(self._surface, self.padding)
                self._surface = bg
            self._dirty = False
        return self._surface


class Button(Component):
    def __init__(self, text="Button", width=120, height=40, color=(60, 60, 180), hover_color=(80, 80, 220), text_color=(255, 255, 255), font_size=16, callback=None):
        super().__init__()
        self.text = text
        self.width = width
        self.height = height
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font_size = font_size
        self.callback = callback
        self.visible = True
        self.enabled = True
        self.layer = 200
        self._hovered = False
        self._pressed = False
        self._font = None
        if PYGAME_AVAILABLE:
            self._font = pygame.font.Font(None, self.font_size)

    @property
    def rect(self) -> tuple:
        if self.transform:
            return (self.transform.x - self.width/2, self.transform.y - self.height/2, self.width, self.height)
        return (0, 0, self.width, self.height)

    def handle_event(self, event) -> bool:
        if not self.enabled or not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            x, y = event.pos
            rx, ry, rw, rh = self.rect
            self._hovered = rx <= x <= rx + rw and ry <= y <= ry + rh
            return self._hovered
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            rx, ry, rw, rh = self.rect
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                self._pressed = True
                if self.callback:
                    self.callback()
                return True
        return False

    def render(self, surface: pygame.Surface):
        if not self.visible or not PYGAME_AVAILABLE:
            return
        rx, ry, rw, rh = self.rect
        color = self.hover_color if self._hovered else self.color
        pygame.draw.rect(surface, color, (int(rx), int(ry), int(rw), int(rh)), border_radius=4)
        if self._hovered:
            pygame.draw.rect(surface, (255, 255, 255, 60), (int(rx), int(ry), int(rw), int(rh)), 2, border_radius=4)
        if self._font:
            txt = self._font.render(self.text, True, self.text_color)
            tx = rx + rw/2 - txt.get_width()/2
            ty = ry + rh/2 - txt.get_height()/2
            surface.blit(txt, (int(tx), int(ty)))


class Light(Component):
    def __init__(self, radius=200, color=(255, 255, 200), intensity=0.5, light_type="point"):
        super().__init__()
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.light_type = light_type
        self.enabled = True

    def update(self, dt: float):
        pass


class AnimationController(Component):
    def __init__(self, frame_width=32, frame_height=32, total_frames=1, fps=12, loop=True):
        super().__init__()
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.total_frames = total_frames
        self.fps = fps
        self.loop = loop
        self.current_frame = 0
        self._timer = 0
        self._playing = True
        self.clips: dict[str, dict] = {}
        self.current_clip = "default"

    def add_clip(self, name: str, start_frame: int, end_frame: int, fps: int = 12, loop: bool = True):
        self.clips[name] = {"start": start_frame, "end": end_frame, "fps": fps, "loop": loop}

    def play(self, clip_name: str):
        if clip_name in self.clips and clip_name != self.current_clip:
            self.current_clip = clip_name
            self.current_frame = self.clips[clip_name]["start"]
            self._timer = 0

    def update(self, dt: float):
        if not self._playing or self.current_clip not in self.clips:
            return
        clip = self.clips[self.current_clip]
        self._timer += dt
        frame_duration = 1.0 / clip["fps"]
        if self._timer >= frame_duration:
            self._timer -= frame_duration
            self.current_frame += 1
            if self.current_frame > clip["end"]:
                if clip["loop"]:
                    self.current_frame = clip["start"]
                else:
                    self.current_frame = clip["end"]
                    self._playing = False

    def get_source_rect(self) -> Optional[tuple]:
        return (self.current_frame * self.frame_width, 0, self.frame_width, self.frame_height)


# ============================================================
# GAME OBJECT
# ============================================================

class GameObject:
    _next_id = 0

    def __init__(self, name="GameObject", x=0.0, y=0.0):
        self.id = GameObject._next_id
        GameObject._next_id += 1
        self.name = name
        self.tag = ""
        self.active = True
        self.transform = Transform(x, y)
        self.transform._game_object = self
        self.components: list[Component] = [self.transform]
        self.children: list[GameObject] = []
        self.parent: Optional[GameObject] = None
        self._component_types: dict[type, Component] = {Transform: self.transform}

    def add_component(self, component: Component) -> Component:
        component._game_object = self
        self.components.append(component)
        self._component_types[type(component)] = component
        return component

    def get_component(self, component_type: type) -> Optional[Component]:
        return self._component_types.get(component_type)

    def has_component(self, component_type: type) -> bool:
        return component_type in self._component_types

    def add_child(self, child: "GameObject"):
        child.parent = self
        child.transform.set_parent(self.transform)
        self.children.append(child)

    def remove_child(self, child: "GameObject"):
        if child in self.children:
            child.parent = None
            child.transform.set_parent(None)
            self.children.remove(child)

    def broadcast(self, method: str, *args, **kwargs):
        if not self.active:
            return
        for c in self.components:
            fn = getattr(c, method, None)
            if fn:
                fn(*args, **kwargs)
        for child in self.children:
            child.broadcast(method, *args, **kwargs)

    def find_by_tag(self, tag: str) -> list["GameObject"]:
        results = []
        if self.tag == tag:
            results.append(self)
        for child in self.children:
            results.extend(child.find_by_tag(tag))
        return results

    def find_by_name(self, name: str) -> Optional["GameObject"]:
        if self.name == name:
            return self
        for child in self.children:
            result = child.find_by_name(name)
            if result:
                return result
        return None

    def destroy(self):
        self.active = False
        self.broadcast("on_destroy")
        if self.parent:
            self.parent.remove_child(self)

    def world_position(self) -> tuple:
        return (self.transform.world_x, self.transform.world_y)

    def distance_to(self, other: "GameObject") -> float:
        dx = self.transform.x - other.transform.x
        dy = self.transform.y - other.transform.y
        return math.sqrt(dx*dx + dy*dy)


# ============================================================
# SCENE
# ============================================================

class GameScene:
    def __init__(self, name="Scene"):
        self.name = name
        self.root_objects: list[GameObject] = []
        self._all_objects: list[GameObject] = []
        self.is_loaded = False
        self.camera: Optional[Camera] = None
        self.ambient_color = (10, 10, 30)
        self.physics_gravity = 980.0
        self._pending_add: list[GameObject] = []
        self._pending_remove: list[GameObject] = []

    def add_object(self, obj: GameObject):
        self._pending_add.append(obj)

    def remove_object(self, obj: GameObject):
        self._pending_remove.append(obj)

    def _collect_all(self, obj: GameObject, output: list):
        output.append(obj)
        for child in obj.children:
            self._collect_all(child, output)

    def find_by_tag(self, tag: str) -> list[GameObject]:
        results = []
        for obj in self._all_objects:
            if obj.tag == tag and obj.active:
                results.append(obj)
        return results

    def find_by_name(self, name: str) -> Optional[GameObject]:
        for obj in self._all_objects:
            if obj.name == name and obj.active:
                return obj
        return None

    def get_objects_with(self, component_type: type) -> list[GameObject]:
        return [obj for obj in self._all_objects if obj.active and obj.has_component(component_type)]

    def load(self):
        for obj in self.root_objects:
            self._all_objects.append(obj)
            self._collect_all(obj, self._all_objects)
        self.is_loaded = True
        for obj in self._all_objects:
            obj.broadcast("awake")
        for obj in self._all_objects:
            obj.broadcast("start")
        if not self.camera and self._all_objects:
            for obj in self._all_objects:
                cam = obj.get_component(Camera)
                if cam and cam.is_primary:
                    self.camera = cam
                    break

    def process_pending(self):
        for obj in self._pending_add:
            self.root_objects.append(obj)
            self._collect_all(obj, self._all_objects)
            obj.broadcast("awake")
            obj.broadcast("start")
        self._pending_add.clear()
        for obj in self._pending_remove:
            if obj in self._all_objects:
                self._all_objects.remove(obj)
            if obj in self.root_objects:
                self.root_objects.remove(obj)
            self._collect_all(obj, [])
            obj.destroy()
        self._pending_remove.clear()

    def update(self, dt: float):
        self.process_pending()
        for obj in self._all_objects:
            if obj.active:
                obj.broadcast("update", dt)
        for obj in self._all_objects:
            if obj.active:
                obj.broadcast("late_update", dt)

    def handle_event(self, event):
        for obj in self._all_objects:
            if obj.active:
                for c in obj.components:
                    if hasattr(c, 'handle_event'):
                        if c.handle_event(event):
                            return True
        return False


# ============================================================
# MAIN ENGINE
# ============================================================

class KYROSCoreEngine:
    def __init__(self, title="KYROS Game", width=800, height=600, fps=60, fullscreen=False, vsync=True):
        self.title = title
        self.width = width
        self.height = height
        self.target_fps = fps
        self.fullscreen = fullscreen
        self.vsync = vsync
        self.scenes: dict[str, GameScene] = {}
        self.current_scene: Optional[GameScene] = None
        self.running = False
        self._clock = None
        self._screen = None
        self._dt = 0
        self._frame_count = 0
        self._fps_timer = 0
        self._current_fps = 0
        self._collision_pairs: set[tuple[int, int]] = set()
        self._keys_down: dict[int, bool] = {}
        self._keys_pressed: dict[int, bool] = {}
        self._mouse_pos = (0, 0)
        self._mouse_buttons = (False, False, False)
        self.debug_mode = False
        self.font_small = None

    def init(self):
        if not PYGAME_AVAILABLE:
            raise RuntimeError("Pygame CE is not installed. Run: pip install pygame-ce")
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        if self.vsync:
            flags |= pygame.HWSURFACE | pygame.DOUBLEBUF
        self._screen = pygame.display.set_mode((self.width, self.height), flags, vsync=self.vsync)
        pygame.display.set_caption(self.title)
        self._clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 14)
        self.running = True

    def add_scene(self, scene: GameScene, name: str = ""):
        name = name or scene.name
        self.scenes[name] = scene

    def switch_scene(self, name: str) -> bool:
        if name in self.scenes:
            self.current_scene = self.scenes[name]
            if not self.current_scene.is_loaded:
                self.current_scene.load()
            return True
        return False

    def quit(self):
        self.running = False
        if PYGAME_AVAILABLE:
            pygame.quit()

    @property
    def delta_time(self) -> float:
        return self._dt

    @property
    def fps(self) -> int:
        return self._current_fps

    @property
    def keys(self) -> dict[int, bool]:
        return self._keys_down

    @property
    def key_just_pressed(self) -> dict[int, bool]:
        return self._keys_pressed

    @property
    def mouse_pos(self) -> tuple:
        return self._mouse_pos

    @property
    def mouse_down(self) -> tuple:
        return self._mouse_buttons

    def _handle_input(self):
        self._keys_pressed.clear()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._keys_down[event.key] = True
                self._keys_pressed[event.key] = True
                if event.key == pygame.K_F3:
                    self.debug_mode = not self.debug_mode
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.KEYUP:
                self._keys_down[event.key] = False
            elif event.type == pygame.MOUSEMOTION:
                self._mouse_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                btn = event.button - 1
                if 0 <= btn < 3:
                    self._mouse_buttons = tuple(True if i == btn else self._mouse_buttons[i] for i in range(3))
            elif event.type == pygame.MOUSEBUTTONUP:
                btn = event.button - 1
                if 0 <= btn < 3:
                    self._mouse_buttons = tuple(False if i == btn else self._mouse_buttons[i] for i in range(3))

            if self.current_scene:
                self.current_scene.handle_event(event)

    def _update_physics(self):
        if not self.current_scene:
            return
        colliders = self.current_scene.get_objects_with(BoxCollider) + self.current_scene.get_objects_with(CircleCollider)
        new_pairs = set()
        for i, obj_a in enumerate(colliders):
            col_a = obj_a.get_component(BoxCollider) or obj_a.get_component(CircleCollider)
            if not col_a or not col_a.enabled:
                continue
            for j in range(i + 1, len(colliders)):
                obj_b = colliders[j]
                col_b = obj_b.get_component(BoxCollider) or obj_b.get_component(CircleCollider)
                if not col_b or not col_b.enabled:
                    continue
                pair_id = (obj_a.id, obj_b.id)
                new_pairs.add(pair_id)
                collides = False
                if isinstance(col_a, BoxCollider) and isinstance(col_b, BoxCollider):
                    collides = col_a.check_collision(col_b)
                elif isinstance(col_a, CircleCollider) and isinstance(col_b, CircleCollider):
                    collides = col_a.check_collision(col_b)
                elif isinstance(col_a, BoxCollider) and isinstance(col_b, CircleCollider):
                    collides = col_b.check_collision_rect(col_a)
                elif isinstance(col_a, CircleCollider) and isinstance(col_b, BoxCollider):
                    collides = col_a.check_collision_rect(col_b)
                if collides:
                    phy_a = obj_a.get_component(PhysicsBody)
                    phy_b = obj_b.get_component(PhysicsBody)
                    if phy_a and phy_b and not col_a.is_trigger and not col_b.is_trigger:
                        normal = (1, 0)
                        if isinstance(col_a, BoxCollider) and isinstance(col_b, BoxCollider):
                            n = col_a.get_collision_normal(col_b)
                            if n:
                                normal = n
                        v_rel = (phy_a.velocity_x - phy_b.velocity_x) * normal[0] + (phy_a.velocity_y - phy_b.velocity_y) * normal[1]
                        if v_rel < 0:
                            impulse = -(1 + min(phy_a.bounciness, phy_b.bounciness)) * v_rel / (1/phy_a.mass + 1/phy_b.mass)
                            phy_a.velocity_x += impulse / phy_a.mass * normal[0]
                            phy_a.velocity_y += impulse / phy_a.mass * normal[1]
                            phy_b.velocity_x -= impulse / phy_b.mass * normal[0]
                            phy_b.velocity_y -= impulse / phy_b.mass * normal[1]
                    if col_a.is_trigger or col_b.is_trigger:
                        obj_a.broadcast("on_trigger", obj_b)
                        obj_b.broadcast("on_trigger", obj_a)
                    else:
                        obj_a.broadcast("on_collision", obj_b)
                        obj_b.broadcast("on_collision", obj_a)
        self._collision_pairs = new_pairs

    def _render(self):
        if not PYGAME_AVAILABLE or not self._screen:
            return
        bg = self.current_scene.ambient_color if self.current_scene else (0, 0, 0)
        self._screen.fill(bg)
        if self.current_scene:
            camera = self.current_scene.camera
            sprites = sorted(self.current_scene.get_objects_with(SpriteRenderer), key=lambda o: o.get_component(SpriteRenderer).layer)
            for obj in sprites:
                sr = obj.get_component(SpriteRenderer)
                surf = sr.get_render_surface()
                if surf and camera:
                    sx, sy = camera.world_to_screen(obj.transform.world_x, obj.transform.world_y)
                    self._screen.blit(surf, (int(sx - surf.get_width() * sr.pivot[0]), int(sy - surf.get_height() * sr.pivot[1])))
                elif surf:
                    self._screen.blit(surf, (int(obj.transform.x), int(obj.transform.y)))
            for obj in self.current_scene.get_objects_with(ParticleSystem):
                ps = obj.get_component(ParticleSystem)
                ps.render(self._screen, camera)
            objects_with_buttons = self.current_scene.get_objects_with(Button)
            for obj in objects_with_buttons:
                btn = obj.get_component(Button)
                btn.render(self._screen)
            objects_with_text = sorted(self.current_scene.get_objects_with(TextLabel), key=lambda o: o.get_component(TextLabel).layer)
            for obj in objects_with_text:
                tl = obj.get_component(TextLabel)
                surf = tl.get_surface()
                if surf:
                    sx, sy = obj.transform.x, obj.transform.y
                    if tl.align == "center":
                        self._screen.blit(surf, (int(sx - surf.get_width()/2), int(sy - surf.get_height()/2)))
                    elif tl.align == "left":
                        self._screen.blit(surf, (int(sx), int(sy)))
                    else:
                        self._screen.blit(surf, (int(sx - surf.get_width()), int(sy)))
        if self.debug_mode and self.font_small:
            y = 5
            for line in [
                f"KYROS Engine | FPS: {self._current_fps}",
                f"Objects: {len(self.current_scene._all_objects) if self.current_scene else 0}",
                f"Scene: {self.current_scene.name if self.current_scene else 'None'}",
                f"Mouse: {self._mouse_pos}",
            ]:
                txt = self.font_small.render(line, True, (0, 255, 255))
                self._screen.blit(txt, (5, y))
                y += 16
        pygame.display.flip()

    def run_frame(self) -> float:
        self._handle_input()
        if not self.running:
            return 0
        self._dt = self._clock.tick(self.target_fps) / 1000.0
        if self._dt > 0.05:
            self._dt = 0.05
        self._frame_count += 1
        self._fps_timer += self._dt
        if self._fps_timer >= 0.5:
            self._current_fps = int(self._frame_count / self._fps_timer)
            self._frame_count = 0
            self._fps_timer = 0
        if self.current_scene:
            self.current_scene.update(self._dt)
            self._update_physics()
        self._render()
        return self._dt

    def run(self):
        self.init()
        while self.running:
            self.run_frame()
        self.quit()

    def create_object(self, name="GameObject", x=0.0, y=0.0) -> GameObject:
        obj = GameObject(name, x, y)
        if self.current_scene:
            self.current_scene.add_object(obj)
        return obj

    def destroy_object(self, obj: GameObject):
        if self.current_scene:
            self.current_scene.remove_object(obj)

    def screen_shake(self, intensity=5, duration=0.2):
        pass

    def get_screenshot(self) -> Optional[Any]:
        if self._screen:
            return self._screen.copy()
        return None

    def get_summary(self) -> dict:
        return {
            "title": self.title,
            "resolution": f"{self.width}x{self.height}",
            "fps": self._current_fps,
            "scene": self.current_scene.name if self.current_scene else None,
            "objects": len(self.current_scene._all_objects) if self.current_scene else 0,
            "running": self.running,
            "pygame_available": PYGAME_AVAILABLE,
        }
