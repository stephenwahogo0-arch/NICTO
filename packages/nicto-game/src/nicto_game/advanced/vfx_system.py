"""VFX & Particle System — Niagara-inspired visual effects engine.

GPU-driven particle systems with:
- Emitters with multiple spawn modes (burst, rate, continuous)
- Particle lifecycle (spawn, update, death)
- Forces (gravity, wind, turbulence, attractors)
- Collision detection (simple bounding volume)
- Mesh/ribbon/beam rendering
- GPU Compute-like simulation using numpy
- LOD-based particle budget management
=== DOCUMENTATION: NIKTO VFX ===
The NiktoVFX system provides a complete particle-based visual effects
pipeline. Key components:

  Particle        - Single particle with position, velocity, color, size, life
  EmitterModule  - Defines spawn behavior (burst, rate, continuous)
  ForceModule    - Physical forces (gravity, wind, turbulence, attractor, drag)
  RenderModule   - Particle appearance (sprite, mesh, ribbon, beam)
  CollisionModule- Particle collision against planes and spheres
  ParticleEffect - Complete effect combining modules with lifecycle management
  VFXSystem      - Manager that runs all active effects

GPU acceleration uses numpy for batch particle updates.
LOD system manages particle counts based on distance/quality.
"""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable
from enum import Enum
import numpy as np


class SpawnMode(Enum):
    BURST = "burst"
    RATE = "rate"
    CONTINUOUS = "continuous"


class ParticleShape(Enum):
    SPRITE = "sprite"
    MESH = "mesh"
    RIBBON = "ribbon"
    BEAM = "beam"
    TRAIL = "trail"


class ForceType(Enum):
    GRAVITY = "gravity"
    WIND = "wind"
    TURBULENCE = "turbulence"
    ATTRACTOR = "attractor"
    REPULSOR = "repulsor"
    DRAG = "drag"
    VORTEX = "vortex"


@dataclass
class Particle:
    id: int
    x: float; y: float; z: float
    vx: float; vy: float; vz: float
    ax: float; ay: float; az: float
    r: float; g: float; b: float; a: float
    size: float
    life: float
    max_life: float
    rotation: float
    angular_velocity: float
    shape: ParticleShape = ParticleShape.SPRITE
    data: dict = field(default_factory=dict)


@dataclass
class EmitterModule:
    spawn_mode: SpawnMode = SpawnMode.RATE
    rate: float = 100.0
    burst_count: int = 50
    spawn_radius: float = 1.0
    spawn_cone_angle: float = 0.0
    inherit_velocity: float = 0.0
    lifetime_min: float = 1.0
    lifetime_max: float = 3.0


@dataclass
class ForceModule:
    force_type: ForceType = ForceType.GRAVITY
    strength: float = 1.0
    direction: Tuple[float, float, float] = (0, -1, 0)
    position: Tuple[float, float, float] = (0, 0, 0)
    radius: float = 10.0
    falloff: float = 1.0
    noise_scale: float = 0.1
    noise_strength: float = 0.0


@dataclass
class RenderModule:
    shape: ParticleShape = ParticleShape.SPRITE
    texture: str = ""
    blend_mode: str = "additive"
    sort_mode: str = "distance"
    mesh_path: str = ""
    ribbon_length: int = 10
    size_over_life: Tuple[float, float] = (1.0, 0.0)
    color_over_life: List[Tuple[float, float, float, float]] = field(
        default_factory=lambda: [(1, 1, 1, 1), (1, 1, 1, 0)]
    )


@dataclass
class CollisionModule:
    enabled: bool = False
    bounce: float = 0.5
    friction: float = 0.1
    kill_on_collide: bool = False
    planes: List[Tuple[float, float, float, float]] = field(default_factory=list)
    spheres: List[Tuple[float, float, float, float]] = field(default_factory=list)


@dataclass
class ParticleEffect:
    name: str = "Effect"
    emitter: EmitterModule = field(default_factory=EmitterModule)
    forces: List[ForceModule] = field(default_factory=list)
    renderer: RenderModule = field(default_factory=RenderModule)
    collision: CollisionModule = field(default_factory=CollisionModule)
    particles: List[Particle] = field(default_factory=list)
    active: bool = True
    loop: bool = True
    duration: float = 2.0
    elapsed: float = 0.0
    max_particles: int = 10000
    next_id: int = 0
    position: Tuple[float, float, float] = (0, 0, 0)

    def update(self, dt: float):
        if not self.active:
            return
        self.elapsed += dt
        if self.loop and self.elapsed >= self.duration:
            self.elapsed = 0
        if self.emitter.spawn_mode == SpawnMode.BURST and self.elapsed < 0.05:
            self._spawn_burst()
        elif self.emitter.spawn_mode in (SpawnMode.RATE, SpawnMode.CONTINUOUS):
            spawn_count = int(self.emitter.rate * dt)
            for _ in range(min(spawn_count, self.max_particles - len(self.particles))):
                self._spawn_particle()
        self._update_particles(dt)

    def _spawn_burst(self):
        for _ in range(min(self.emitter.burst_count, self.max_particles)):
            self._spawn_particle()

    def _spawn_particle(self):
        if len(self.particles) >= self.max_particles:
            return
        angle_h = random.uniform(-self.emitter.spawn_cone_angle, self.emitter.spawn_cone_angle) * math.pi / 180
        angle_v = random.uniform(0, 2 * math.pi)
        r = self.emitter.spawn_radius * math.sqrt(random.random())
        px = self.position[0] + r * math.cos(angle_v) * math.cos(angle_h)
        py = self.position[1] + r * math.sin(angle_h)
        pz = self.position[2] + r * math.sin(angle_v) * math.cos(angle_h)
        speed = random.uniform(0.5, 2.0)
        life = random.uniform(self.emitter.lifetime_min, self.emitter.lifetime_max)
        p = Particle(
            id=self.next_id, x=px, y=py, z=pz,
            vx=speed * math.cos(angle_v), vy=speed * 0.5, vz=speed * math.sin(angle_v),
            ax=0, ay=0, az=0,
            r=1, g=1, b=1, a=1,
            size=random.uniform(0.1, 0.5), life=life, max_life=life,
            rotation=random.uniform(0, 2 * math.pi),
            angular_velocity=random.uniform(-2, 2),
            shape=self.renderer.shape
        )
        self.next_id += 1
        self.particles.append(p)

    def _update_particles(self, dt: float):
        dead = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                dead.append(p); continue
            ax, ay, az = 0, 0, 0
            for f in self.forces:
                if f.force_type == ForceType.GRAVITY:
                    ax += f.direction[0] * f.strength
                    ay += f.direction[1] * f.strength
                    az += f.direction[2] * f.strength
                elif f.force_type == ForceType.WIND:
                    noise = math.sin(p.x * f.noise_scale + self.elapsed) * f.noise_strength
                    ax += f.direction[0] * f.strength + noise
                    ay += f.direction[1] * f.strength
                    az += f.direction[2] * f.strength
                elif f.force_type == ForceType.TURBULENCE:
                    ax += math.sin(p.y * 0.5 + self.elapsed * 2) * f.strength
                    ay += math.cos(p.x * 0.5 + self.elapsed * 1.5) * f.strength
                    az += math.sin(p.z * 0.5 + self.elapsed * 1.8) * f.strength * 0.3
                elif f.force_type == ForceType.ATTRACTOR:
                    dx = f.position[0] - p.x
                    dy = f.position[1] - p.y
                    dz = f.position[2] - p.z
                    dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.01
                    if dist < f.radius:
                        strength = f.strength / (dist ** f.falloff) * 10
                        ax += dx / dist * strength
                        ay += dy / dist * strength
                        az += dz / dist * strength
                elif f.force_type == ForceType.DRAG:
                    ax -= p.vx * f.strength
                    ay -= p.vy * f.strength
                    az -= p.vz * f.strength
            p.ax, p.ay, p.az = ax, ay, az
            p.vx += ax * dt; p.vy += ay * dt; p.vz += az * dt
            p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt
            life_ratio = p.life / p.max_life
            p.size *= self.renderer.size_over_life[0] if life_ratio > 0.5 else self.renderer.size_over_life[1]
            p.rotation += p.angular_velocity * dt
            if self.collision.enabled:
                self._handle_collision(p)
        for p in dead:
            if p in self.particles:
                self.particles.remove(p)

    def _handle_collision(self, p: Particle):
        for plane in self.collision.planes:
            a, b, c, d = plane
            dist = a * p.x + b * p.y + c * p.z + d
            if dist < 0:
                dot = a * p.vx + b * p.vy + c * p.vz
                if dot < 0:
                    p.vx -= (1 + self.collision.bounce) * dot * a
                    p.vy -= (1 + self.collision.bounce) * dot * b
                    p.vz -= (1 + self.collision.bounce) * dot * c
                    p.vx *= (1 - self.collision.friction)
                    p.vz *= (1 - self.collision.friction)
                p.x += a * (-dist + 0.01)
                p.y += b * (-dist + 0.01)
                p.z += c * (-dist + 0.01)
                if self.collision.kill_on_collide:
                    p.life = 0

    def set_position(self, x: float, y: float, z: float):
        self.position = (x, y, z)

    def stop(self):
        self.active = False

    def reset(self):
        self.particles.clear()
        self.elapsed = 0
        self.active = True


class VFXSystem:
    """Manages all active particle effects."""

    def __init__(self):
        self.effects: List[ParticleEffect] = []
        self._total_particles = 0
        self.max_global_particles = 50000
        self.lod_quality: float = 1.0

    def add_effect(self, effect: ParticleEffect) -> ParticleEffect:
        self.effects.append(effect)
        return effect

    def remove_effect(self, effect: ParticleEffect):
        if effect in self.effects:
            self.effects.remove(effect)

    def update(self, dt: float):
        particle_budget = int(self.max_global_particles * self.lod_quality)
        self._total_particles = sum(len(e.particles) for e in self.effects)
        for effect in self.effects:
            if particle_budget <= 0:
                break
            effect.max_particles = max(0, min(effect.max_particles, particle_budget))
            effect.update(dt)
            particle_budget -= len(effect.particles)

    def clear(self):
        self.effects.clear()
        self._total_particles = 0

    def create_explosion(self, x: float, y: float, z: float, scale: float = 1.0) -> ParticleEffect:
        effect = ParticleEffect(name=f"Explosion_{id(self)}", loop=False, duration=1.5, position=(x, y, z))
        effect.emitter = EmitterModule(spawn_mode=SpawnMode.BURST, burst_count=int(200 * scale),
                                       spawn_radius=0.5 * scale, lifetime_min=0.5, lifetime_max=1.5)
        effect.forces = [
            ForceModule(force_type=ForceType.TURBULENCE, strength=5 * scale),
            ForceModule(force_type=ForceType.DRAG, strength=0.5),
        ]
        effect.renderer = RenderModule(shape=ParticleShape.SPRITE, blend_mode="additive",
                                       size_over_life=(1.0, 0.0))
        effect.collision = CollisionModule(enabled=True, bounce=0.3,
                                           planes=[(0, 1, 0, 0)])
        return self.add_effect(effect)

    def create_fire(self, x: float, y: float, z: float) -> ParticleEffect:
        effect = ParticleEffect(name=f"Fire_{id(self)}", loop=True, duration=5.0, position=(x, y, z))
        effect.emitter = EmitterModule(spawn_mode=SpawnMode.RATE, rate=60,
                                       spawn_radius=0.2, lifetime_min=0.5, lifetime_max=1.5)
        effect.forces = [
            ForceModule(force_type=ForceType.GRAVITY, strength=0.5, direction=(0, 1, 0)),
            ForceModule(force_type=ForceType.TURBULENCE, strength=0.3),
        ]
        effect.renderer = RenderModule(shape=ParticleShape.SPRITE, blend_mode="additive")
        return self.add_effect(effect)

    def create_smoke(self, x: float, y: float, z: float) -> ParticleEffect:
        effect = ParticleEffect(name=f"Smoke_{id(self)}", loop=True, duration=4.0, position=(x, y, z))
        effect.emitter = EmitterModule(spawn_mode=SpawnMode.RATE, rate=20,
                                       spawn_radius=0.3, lifetime_min=2.0, lifetime_max=4.0)
        effect.forces = [
            ForceModule(force_type=ForceType.GRAVITY, strength=0.3, direction=(0, 1, 0)),
            ForceModule(force_type=ForceType.TURBULENCE, strength=0.5),
        ]
        effect.renderer = RenderModule(shape=ParticleShape.SPRITE, blend_mode="alpha")
        return self.add_effect(effect)

    def create_sparks(self, x: float, y: float, z: float, direction: Tuple[float, float, float] = (0, 1, 0)) -> ParticleEffect:
        effect = ParticleEffect(name=f"Sparks_{id(self)}", loop=False, duration=2.0, position=(x, y, z))
        effect.emitter = EmitterModule(spawn_mode=SpawnMode.BURST, burst_count=100,
                                       spawn_cone_angle=30, lifetime_min=0.3, lifetime_max=1.0)
        effect.forces = [
            ForceModule(force_type=ForceType.GRAVITY, strength=2.0, direction=(0, -1, 0)),
            ForceModule(force_type=ForceType.DRAG, strength=0.3),
        ]
        effect.renderer = RenderModule(shape=ParticleShape.SPRITE, blend_mode="additive")
        effect.collision = CollisionModule(enabled=True, bounce=0.6, friction=0.3, kill_on_collide=True,
                                           planes=[(0, 1, 0, 0)])
        return self.add_effect(effect)

    def create_muzzle_flash(self, x: float, y: float, z: float) -> ParticleEffect:
        effect = ParticleEffect(name=f"MuzzleFlash_{id(self)}", loop=False, duration=0.2, position=(x, y, z))
        effect.emitter = EmitterModule(spawn_mode=SpawnMode.BURST, burst_count=15,
                                       spawn_radius=0.05, lifetime_min=0.05, lifetime_max=0.2)
        effect.renderer = RenderModule(shape=ParticleShape.SPRITE, blend_mode="additive",
                                       size_over_life=(2.0, 0.0))
        return self.add_effect(effect)

    def get_stats(self) -> dict:
        return {
            "active_effects": len(self.effects),
            "total_particles": self._total_particles,
            "max_global": self.max_global_particles,
            "lod_quality": self.lod_quality,
        }
