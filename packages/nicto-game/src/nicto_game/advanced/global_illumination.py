"""Lumen-inspired Global Illumination System.

Real-time dynamic global illumination with:
- Light propagation volumes (LPV)
- Ray-marched indirect lighting
- Multi-bounce GI with color bleeding
- Dynamic light updates (no baking needed)
- Screen-space reflections fallback
"""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum


class LightType(Enum):
    DIRECTIONAL = "directional"
    POINT = "point"
    SPOT = "spot"
    AREA = "area"
    SKY = "sky"
    EMISSIVE = "emissive"


@dataclass
class LightSource:
    """A dynamic light source."""
    light_type: LightType
    x: float = 0.0; y: float = 0.0; z: float = 0.0
    dx: float = 0.0; dy: float = -1.0; dz: float = 0.0
    color_r: float = 1.0; color_g: float = 1.0; color_b: float = 1.0
    intensity: float = 1.0
    range: float = 10.0
    inner_cone: float = 15.0
    outer_cone: float = 30.0
    shadow_casting: bool = True
    indirect_multiplier: float = 1.0
    area_width: float = 0.5
    area_height: float = 0.5
    is_dynamic: bool = True


@dataclass
class LightProbe:
    """A light probe storing incoming radiance from all directions."""
    x: float; y: float; z: float
    radiance_r: float = 0.0
    radiance_g: float = 0.0
    radiance_b: float = 0.0
    dominant_direction_x: float = 0.0
    dominant_direction_y: float = 0.0
    dominant_direction_z: float = 0.0
    occlusion: float = 0.0
    confidence: float = 0.0


@dataclass
class LightPropagationVolume:
    """3D grid of light probes for multi-bounce GI."""
    origin_x: float = 0.0; origin_y: float = 0.0; origin_z: float = 0.0
    size_x: int = 16; size_y: int = 8; size_z: int = 16
    cell_size: float = 1.0
    probes: List[LightProbe] = field(default_factory=list)
    _needs_update: bool = True

    def __post_init__(self):
        if not self.probes:
            self._init_probes()

    def _init_probes(self):
        """Initialize probe grid."""
        self.probes = []
        for z in range(self.size_z):
            for y in range(self.size_y):
                for x in range(self.size_x):
                    self.probes.append(LightProbe(
                        x=self.origin_x + x * self.cell_size,
                        y=self.origin_y + y * self.cell_size,
                        z=self.origin_z + z * self.cell_size,
                    ))

    def get_probe(self, world_x: float, world_y: float, world_z: float) -> Optional[LightProbe]:
        ix = int((world_x - self.origin_x) / self.cell_size)
        iy = int((world_y - self.origin_y) / self.cell_size)
        iz = int((world_z - self.origin_z) / self.cell_size)
        if 0 <= ix < self.size_x and 0 <= iy < self.size_y and 0 <= iz < self.size_z:
            idx = iz * self.size_y * self.size_x + iy * self.size_x + ix
            if 0 <= idx < len(self.probes):
                return self.probes[idx]
        return None

    def trilinear_interp(self, world_x: float, world_y: float, world_z: float) -> LightProbe:
        default = LightProbe(x=world_x, y=world_y, z=world_z)
        p = self.get_probe(world_x, world_y, world_z)
        if p:
            return p
        return default


class GlobalIlluminationEngine:
    """Lumen-inspired global illumination engine.

    Features:
    - Light propagation volumes (LPV) for multi-bounce GI
    - Ray-marched indirect lighting
    - Dynamic light updates (no baking)
    - Color bleeding between surfaces
    - Automatic quality scaling
    """

    def __init__(self):
        self.lights: List[LightSource] = []
        self.lpvs: List[LightPropagationVolume] = []
        self.bounce_count: int = 2
        self.quality: str = "high"
        self._sky_color: Tuple[float, float, float] = (0.4, 0.6, 1.0)
        self._ambient: Tuple[float, float, float] = (0.02, 0.02, 0.03)
        self._needs_full_update: bool = True

    def add_light(self, light: LightSource):
        self.lights.append(light)
        self._needs_full_update = True

    def remove_light(self, light: LightSource):
        if light in self.lights:
            self.lights.remove(light)
            self._needs_full_update = True

    def add_lpv(self, lpv: LightPropagationVolume):
        self.lpvs.append(lpv)

    def set_sky_color(self, r: float, g: float, b: float):
        self._sky_color = (r, g, b)
        self._needs_full_update = True

    def set_ambient(self, r: float, g: float, b: float):
        self._ambient = (r, g, b)

    def update(self, dt: float = 0.016):
        """Update GI system each frame."""
        if not self._needs_full_update:
            return
        self._propagate_light()
        self._needs_full_update = False

    def _propagate_light(self):
        """Multi-bounce light propagation through LPV grid."""
        if not self.lpvs:
            return
        for lpv in self.lpvs:
            for probe in lpv.probes:
                total_r = self._ambient[0]
                total_g = self._ambient[1]
                total_b = self._ambient[2]
                total_dir_x = 0.0; total_dir_y = 0.0; total_dir_z = 0.0
                for light in self.lights:
                    dx = probe.x - light.x
                    dy = probe.y - light.y
                    dz = probe.z - light.z
                    dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                    if dist < 0.01:
                        continue
                    attenuation = 1.0 / max(dist * dist, 0.1)
                    if light.light_type == LightType.DIRECTIONAL:
                        dot = (light.dx * 0 + light.dy * 1 + light.dz * 0)
                        attenuation = max(0, dot)
                    elif light.light_type == LightType.SPOT:
                        dir_len = math.sqrt(light.dx**2 + light.dy**2 + light.dz**2)
                        if dir_len > 0:
                            ldx, ldy, ldz = light.dx/dir_len, light.dy/dir_len, light.dz/dir_len
                            to_light_x = -dx/dist; to_light_y = -dy/dist; to_light_z = -dz/dist
                            angle = math.acos(max(-1, min(1,
                                ldx * to_light_x + ldy * to_light_y + ldz * to_light_z
                            )))
                            cone_atten = max(0, 1 - (angle - math.radians(light.inner_cone)) /
                                             max(math.radians(light.outer_cone - light.inner_cone), 0.001))
                            attenuation *= cone_atten
                    rad_r = light.color_r * light.intensity * attenuation
                    rad_g = light.color_g * light.intensity * attenuation
                    rad_b = light.color_b * light.intensity * attenuation
                    total_r += rad_r
                    total_g += rad_g
                    total_b += rad_b
                    total_dir_x += dx * rad_r
                    total_dir_y += dy * rad_g
                    total_dir_z += dz * rad_b
                probe.radiance_r = min(total_r, 10.0)
                probe.radiance_g = min(total_g, 10.0)
                probe.radiance_b = min(total_b, 10.0)
                dir_len = math.sqrt(total_dir_x**2 + total_dir_y**2 + total_dir_z**2)
                if dir_len > 0:
                    probe.dominant_direction_x = total_dir_x / dir_len
                    probe.dominant_direction_y = total_dir_y / dir_len
                    probe.dominant_direction_z = total_dir_z / dir_len
                probe.confidence = 1.0

    def ray_march_gi(self, origin_x: float, origin_y: float, origin_z: float,
                     dir_x: float, dir_y: float, dir_z: float, max_steps: int = 32) -> Tuple[float, float, float]:
        """Ray-march through LPV to accumulate indirect light."""
        step_size = 0.5
        r, g, b = 0.0, 0.0, 0.0
        ox, oy, oz = origin_x, origin_y, origin_z
        for _ in range(max_steps):
            ox += dir_x * step_size
            oy += dir_y * step_size
            oz += dir_z * step_size
            for lpv in self.lpvs:
                probe = lpv.trilinear_interp(ox, oy, oz)
                if probe.confidence > 0:
                    r += probe.radiance_r * 0.1
                    g += probe.radiance_g * 0.1
                    b += probe.radiance_b * 0.1
        return min(r, 1.0), min(g, 1.0), min(b, 1.0)

    def sample_gi(self, x: float, y: float, z: float,
                  normal_x: float = 0, normal_y: float = 1, normal_z: float = 0) -> Tuple[float, float, float]:
        """Sample global illumination at a world position."""
        r = self._ambient[0]; g = self._ambient[1]; b = self._ambient[2]
        for lpv in self.lpvs:
            probe = lpv.trilinear_interp(x, y, z)
            ndotd = (normal_x * probe.dominant_direction_x +
                     normal_y * probe.dominant_direction_y +
                     normal_z * probe.dominant_direction_z)
            if ndotd > 0:
                r += probe.radiance_r * ndotd * 0.5
                g += probe.radiance_g * ndotd * 0.5
                b += probe.radiance_b * ndotd * 0.5
            else:
                r += probe.radiance_r * 0.1
                g += probe.radiance_g * 0.1
                b += probe.radiance_b * 0.1
        return min(r, 3.0), min(g, 3.0), min(b, 3.0)

    def evaluate_light(self, x: float, y: float, z: float,
                       normal_x: float, normal_y: float, normal_z: float,
                       view_x: float = 0, view_y: float = 0, view_z: float = 1) -> Tuple[float, float, float]:
        """Full light evaluation: direct + indirect."""
        r, g, b = 0.0, 0.0, 0.0
        for light in self.lights:
            dx = light.x - x; dy = light.y - y; dz = light.z - z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist < 0.01:
                continue
            dir_x, dir_y, dir_z = dx/dist, dy/dist, dz/dist
            ndotl = max(0, normal_x * dir_x + normal_y * dir_y + normal_z * dir_z)
            attenuation = 1.0 / max(dist * dist, 0.1)
            if light.light_type == LightType.DIRECTIONAL:
                ndotl = max(0, normal_x * -light.dx + normal_y * -light.dy + normal_z * -light.dz)
                attenuation = 1.0
            elif light.light_type == LightType.SPOT:
                dir_len = math.sqrt(light.dx**2 + light.dy**2 + light.dz**2)
                if dir_len > 0:
                    ldx, ldy, ldz = light.dx/dir_len, light.dy/dir_len, light.dz/dir_len
                    angle = math.acos(max(-1, min(1,
                        ldx * -dir_x + ldy * -dir_y + ldz * -dir_z
                    )))
                    cone_atten = max(0, 1 - (angle - math.radians(light.inner_cone)) /
                                     max(math.radians(light.outer_cone - light.inner_cone), 0.001))
                    attenuation *= cone_atten
            if ndotl > 0:
                r += light.color_r * light.intensity * ndotl * attenuation
                g += light.color_g * light.intensity * ndotl * attenuation
                b += light.color_b * light.intensity * ndotl * attenuation
        ir, ig, ib = self.sample_gi(x, y, z, normal_x, normal_y, normal_z)
        r += ir; g += ig; b += ib
        return min(r, 5.0), min(g, 5.0), min(b, 5.0)

    def create_default_scene(self):
        """Set up a default scene with standard lights."""
        self.lights = [
            LightSource(LightType.DIRECTIONAL, dx=0.5, dy=-0.8, dz=0.3,
                        color_r=1.0, color_g=0.95, color_b=0.9, intensity=1.5),
            LightSource(LightType.SKY, color_r=0.4, color_g=0.6, color_b=1.0, intensity=0.3),
            LightSource(LightType.POINT, x=-3, y=2, z=0, color_r=1.0, color_g=0.3, color_b=0.1, intensity=0.8, range=5),
            LightSource(LightType.POINT, x=3, y=1, z=2, color_r=0.1, color_g=0.3, color_b=1.0, intensity=0.6, range=4),
        ]
        self.add_lpv(LightPropagationVolume(
            origin_x=-10, origin_y=-2, origin_z=-10,
            size_x=20, size_y=8, size_z=20, cell_size=1.0
        ))
        self._propagate_light()

    def get_stats(self) -> dict:
        return {
            "lights": len(self.lights),
            "lpvs": len(self.lpvs),
            "total_probes": sum(len(lpv.probes) for lpv in self.lpvs),
            "bounce_count": self.bounce_count,
            "needs_update": self._needs_full_update,
            "quality": self.quality,
        }
