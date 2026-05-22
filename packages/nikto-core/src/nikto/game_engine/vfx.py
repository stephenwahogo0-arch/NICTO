"""NIKTO VFX Engine — Niagara-like particle system with emitters, modules, collisions."""

import math
import random
from typing import Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class Particle:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 1.0
        self.max_life = 1.0
        self.size = 4.0
        self.start_size = 4.0
        self.end_size = 1.0
        self.color = (255, 255, 255)
        self.start_color = (255, 255, 255)
        self.end_color = (0, 0, 0)
        self.alpha = 255
        self.rotation = 0.0
        self.angular_velocity = 0.0
        self.shape = "circle"
        self.trail = []
        self.max_trail = 5
        self.active = True
        self.drag = 0.99
        self.gravity = 0.0
        self.turbulence = 0.0

    def update(self, dt):
        if not self.active:
            return
        self.life -= dt
        if self.life <= 0:
            self.active = False
            return
        t = 1.0 - (self.life / self.max_life)
        self.vx += random.uniform(-1, 1) * self.turbulence * dt
        self.vy += self.gravity * dt
        self.vx *= self.drag
        self.vy *= self.drag
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.angular_velocity * dt
        self.size = self.start_size + (self.end_size - self.start_size) * t
        self.alpha = int(255 * (1.0 - t))
        self.color = (
            int(self.start_color[0] + (self.end_color[0] - self.start_color[0]) * t),
            int(self.start_color[1] + (self.end_color[1] - self.start_color[1]) * t),
            int(self.start_color[2] + (self.end_color[2] - self.start_color[2]) * t),
        )
        if len(self.trail) < self.max_trail:
            self.trail.append((self.x, self.y))
        if len(self.trail) >= self.max_trail:
            self.trail.pop(0)

    def render(self, surface, camera=None):
        if not self.active or not PYGAME_AVAILABLE:
            return
        sx, sy = int(self.x), int(self.y)
        if camera:
            sx, sy = camera.world_to_screen(sx, sy)
        color = (*self.color[:3], max(0, min(255, self.alpha)))
        sz = max(1, int(self.size))
        if self.shape == "circle":
            s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (sz, sz), sz)
            surface.blit(s, (sx - sz, sy - sz))
        elif self.shape == "square":
            s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            s.fill(color)
            surface.blit(s, (sx - sz, sy - sz))
        elif self.shape == "star":
            pts = []
            for i in range(10):
                a = math.radians(i * 36 - 90)
                r = sz if i % 2 == 0 else sz * 0.4
                pts.append((sx + math.cos(a) * r, sy + math.sin(a) * r))
            if len(pts) >= 3:
                pygame.draw.polygon(surface, color, pts)
        if self.trail:
            for i, (tx, ty) in enumerate(self.trail):
                trail_alpha = int(255 * i / len(self.trail))
                trail_sz = max(1, int(self.size * i / len(self.trail)))
                trail_color = (*self.color[:3], trail_alpha)
                s = pygame.Surface((trail_sz * 2, trail_sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, trail_color, (trail_sz, trail_sz), trail_sz)
                surface.blit(s, (int(tx) - trail_sz - (sx - int(self.x)), int(ty) - trail_sz - (sy - int(self.y))))


class EmitterModule:
    def __init__(self):
        self.rate = 50
        self.lifetime = 1.0
        self.lifetime_variance = 0.3
        self.speed = 100.0
        self.speed_variance = 50.0
        self.spread = 0.5
        self.start_size = 4.0
        self.end_size = 1.0
        self.start_color = (255, 255, 255)
        self.end_color = (0, 0, 0)
        self.gravity = 0.0
        self.drag = 0.99
        self.turbulence = 0.0
        self.shape = "circle"
        self.burst_count = 0
        self.burst_timer = 0.0
        self.burst_interval = 0.5
        self.max_particles = 500
        self.direction_mode = "outward"  # outward, cone, random, target
        self.target_x = 0.0
        self.target_y = 0.0


class Emitter:
    def __init__(self, x=0, y=0, module=None):
        self.x = x
        self.y = y
        self.module = module or EmitterModule()
        self.particles = []
        self.accumulator = 0.0
        self.burst_timer = 0.0
        self.active = True
        self.one_shot = False
        self.emission_angle = 0.0

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def emit_burst(self, count=None):
        count = count or self.module.burst_count
        for _ in range(count):
            self._spawn_particle()

    def update(self, dt):
        if not self.active:
            for p in self.particles:
                p.update(dt)
            self.particles = [p for p in self.particles if p.active]
            return
        self.accumulator += dt * self.module.rate
        self.burst_timer += dt
        if self.module.burst_count > 0 and self.burst_timer >= self.module.burst_interval:
            self.burst_timer -= self.module.burst_interval
            self.emit_burst()
        while self.accumulator >= 1.0 and len(self.particles) < self.module.max_particles:
            self.accumulator -= 1.0
            self._spawn_particle()
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.active]

        if self.one_shot and self.particles:
            self.active = False

    def _spawn_particle(self):
        p = Particle()
        lifetime = self.module.lifetime + random.uniform(-1, 1) * self.module.lifetime_variance
        p.life = max(0.1, lifetime)
        p.max_life = p.life
        speed = self.module.speed + random.uniform(-1, 1) * self.module.speed_variance
        if self.module.direction_mode == "outward":
            angle = random.uniform(0, math.pi * 2)
        elif self.module.direction_mode == "cone":
            half = self.module.spread / 2
            angle = self.emission_angle + random.uniform(-half, half)
        elif self.module.direction_mode == "target":
            dx = self.module.target_x - self.x
            dy = self.module.target_y - self.y
            angle = math.atan2(dy, dx) + random.uniform(-self.module.spread, self.module.spread)
        else:
            angle = random.uniform(0, math.pi * 2)
        p.vx = math.cos(angle) * speed
        p.vy = math.sin(angle) * speed
        p.x = self.x + random.uniform(-2, 2)
        p.y = self.y + random.uniform(-2, 2)
        p.start_size = self.module.start_size + random.uniform(-1, 1) * 0.5
        p.end_size = self.module.end_size
        p.size = p.start_size
        p.start_color = self.module.start_color
        p.end_color = self.module.end_color
        p.color = self.module.start_color
        p.gravity = self.module.gravity
        p.drag = self.module.drag
        p.turbulence = self.module.turbulence
        p.shape = self.module.shape
        self.particles.append(p)

    def render(self, surface, camera=None, sort=False):
        if sort:
            self.particles.sort(key=lambda p: p.y)
        for p in self.particles:
            p.render(surface, camera)


class VFXPresets:
    FIRE = {
        "rate": 60,
        "lifetime": 0.8,
        "lifetime_variance": 0.3,
        "speed": 80,
        "speed_variance": 30,
        "spread": 0.3,
        "start_size": 5,
        "end_size": 1,
        "start_color": (255, 200, 50),
        "end_color": (255, 50, 0),
        "gravity": -30,
        "drag": 0.95,
        "turbulence": 50,
        "shape": "circle",
        "direction_mode": "cone",
    }
    SMOKE = {
        "rate": 20,
        "lifetime": 2.0,
        "lifetime_variance": 0.5,
        "speed": 30,
        "speed_variance": 15,
        "spread": 0.8,
        "start_size": 8,
        "end_size": 20,
        "start_color": (100, 100, 100),
        "end_color": (50, 50, 50),
        "gravity": -10,
        "drag": 0.97,
        "turbulence": 20,
        "shape": "circle",
        "direction_mode": "outward",
    }
    EXPLOSION = {
        "rate": 0,
        "lifetime": 0.6,
        "speed": 200,
        "speed_variance": 100,
        "spread": 1.0,
        "start_size": 6,
        "end_size": 1,
        "start_color": (255, 255, 200),
        "end_color": (255, 100, 0),
        "gravity": 0,
        "drag": 0.9,
        "shape": "star",
        "direction_mode": "outward",
        "burst_count": 50,
    }
    SPARK = {
        "rate": 100,
        "lifetime": 0.4,
        "lifetime_variance": 0.2,
        "speed": 150,
        "speed_variance": 80,
        "spread": 0.2,
        "start_size": 2,
        "end_size": 0,
        "start_color": (255, 255, 255),
        "end_color": (255, 200, 100),
        "gravity": 100,
        "drag": 0.85,
        "shape": "square",
        "direction_mode": "cone",
    }
    MAGIC = {
        "rate": 40,
        "lifetime": 1.5,
        "lifetime_variance": 0.5,
        "speed": 60,
        "speed_variance": 40,
        "spread": 0.5,
        "start_size": 3,
        "end_size": 0,
        "start_color": (100, 200, 255),
        "end_color": (200, 100, 255),
        "gravity": -20,
        "drag": 0.98,
        "turbulence": 30,
        "shape": "circle",
        "direction_mode": "outward",
    }
    RAIN = {
        "rate": 200,
        "lifetime": 2.0,
        "speed": 400,
        "speed_variance": 100,
        "spread": 0.05,
        "start_size": 1,
        "end_size": 1,
        "start_color": (150, 180, 255),
        "end_color": (100, 140, 255),
        "gravity": 200,
        "drag": 1.0,
        "shape": "square",
        "direction_mode": "cone",
        "emission_angle": math.pi / 2,
    }
    SNOW = {
        "rate": 80,
        "lifetime": 4.0,
        "lifetime_variance": 1.0,
        "speed": 30,
        "speed_variance": 10,
        "spread": 1.0,
        "start_size": 2,
        "end_size": 2,
        "start_color": (255, 255, 255),
        "end_color": (220, 220, 255),
        "gravity": 20,
        "drag": 0.99,
        "turbulence": 40,
        "shape": "circle",
        "direction_mode": "outward",
    }

    @staticmethod
    def apply(preset, module):
        for k, v in preset.items():
            setattr(module, k, v)


class VFXSystem:
    def __init__(self):
        self.emitters = []

    def add_emitter(self, x, y, preset=None, one_shot=False):
        module = EmitterModule()
        if preset:
            VFXPresets.apply(preset, module)
        emitter = Emitter(x, y, module)
        emitter.one_shot = one_shot
        self.emitters.append(emitter)
        return emitter

    def remove_emitter(self, emitter):
        if emitter in self.emitters:
            self.emitters.remove(emitter)

    def update(self, dt):
        for emitter in self.emitters:
            emitter.update(dt)
        self.emitters = [e for e in self.emitters if e.active or e.particles]

    def render(self, surface, camera=None):
        all_particles = []
        for emitter in self.emitters:
            for p in emitter.particles:
                all_particles.append(p)
        all_particles.sort(key=lambda p: p.y)
        for p in all_particles:
            p.render(surface, camera)
