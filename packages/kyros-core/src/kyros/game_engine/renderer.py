"""KYROS Renderer — advanced lighting, shadows, materials, post-processing."""

import math
import random
from typing import Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


def gaussian_blur(surface, radius=4):
    """Fast box-blur approximation of Gaussian blur."""
    if not PYGAME_AVAILABLE or radius < 1:
        return surface
    w, h = surface.get_size()
    result = surface.copy()
    for _ in range(3):
        temp = result.copy()
        for x in range(w):
            r, g, b, a = 0, 0, 0, 0
            count = 0
            for bx in range(-radius, radius + 1):
                px = x + bx
                if 0 <= px < w:
                    pr, pg, pb, pa = temp.get_at((px, 0))
                    r += pr; g += pg; b += pb; a += pa
                    count += 1
            if count > 0:
                result.set_at((x, 0), (r // count, g // count, b // count, a // count))
        for y in range(h):
            r, g, b, a = 0, 0, 0, 0
            count = 0
            for by in range(-radius, radius + 1):
                py = y + by
                if 0 <= py < h:
                    pr, pg, pb, pa = temp.get_at((0, py))
                    r += pr; g += pg; b += pb; a += pa
                    count += 1
            if count > 0:
                result.set_at((0, y), (r // count, g // count, b // count, a // count))
    return result


class RenderLayer:
    def __init__(self, width, height, name="default"):
        self.width = width
        self.height = height
        self.name = name
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA) if PYGAME_AVAILABLE else None
        self.lights = []
        self.visible = True
        self.opacity = 255
        self.blend_mode = pygame.BLEND_ALPHA_SDL2 if PYGAME_AVAILABLE else 0

    def clear(self, color=(0, 0, 0, 0)):
        if self.surface:
            self.surface.fill(color)

    def draw_light(self, x, y, radius, color=(255, 255, 200), intensity=0.5, light_type="point"):
        self.lights.append({
            "x": x, "y": y, "radius": radius,
            "color": color, "intensity": intensity, "type": light_type
        })

    def render_lights(self, target_surface, ambient_darkness=120):
        """Render 2D dynamic lighting with soft shadows."""
        if not PYGAME_AVAILABLE or not self.surface:
            return
        light_mask = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        light_mask.fill((ambient_darkness, ambient_darkness, ambient_darkness, 255))
        for light in self.lights:
            surf = pygame.Surface((light["radius"] * 2, light["radius"] * 2), pygame.SRCALPHA)
            for i in range(light["radius"], 0, -1):
                alpha = int(light["intensity"] * 255 * (1 - i / light["radius"]))
                c = light["color"]
                pygame.draw.circle(surf, (c[0], c[1], c[2], alpha),
                                  (light["radius"], light["radius"]), i)
            light_mask.blit(surf, (int(light["x"] - light["radius"]), int(light["y"] - light["radius"])),
                           special_flags=pygame.BLEND_RGBA_SUB)
        target_surface.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.lights.clear()


class ShadowCaster:
    def __init__(self, x, y, width, height, softness=4):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.softness = softness
        self.cast_shadows = True

    def render_shadow(self, surface, light_x, light_y, light_radius):
        """Render shadow cast by this object onto surface."""
        if not PYGAME_AVAILABLE or not self.cast_shadows:
            return
        shadow = pygame.Surface((self.width + self.softness * 2, self.height + self.softness * 2), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 120))
        shadow = gaussian_blur(shadow, self.softness)
        offset_x = self.x + (self.x - light_x) * 0.1
        offset_y = self.y + (self.y - light_y) * 0.1
        surface.blit(shadow, (int(offset_x - self.softness), int(offset_y - self.softness)),
                    special_flags=pygame.BLEND_RGBA_SUB)


class Material:
    def __init__(self, base_color=(255, 255, 255), texture_path="", normal_map_path="", specular=0.5, emission=(0, 0, 0), roughness=0.5, metallic=0.0, opacity=1.0):
        self.base_color = base_color
        self.texture_path = texture_path
        self.normal_map_path = normal_map_path
        self.specular = specular
        self.emission = emission
        self.roughness = roughness
        self.metallic = metallic
        self.opacity = opacity
        self._texture = None
        self._normal_map = None
        self._load_textures()

    def _load_textures(self):
        if not PYGAME_AVAILABLE:
            return
        if self.texture_path and pygame.image:
            try:
                self._texture = pygame.image.load(self.texture_path).convert_alpha()
            except Exception:
                self._texture = None
        if self.normal_map_path and pygame.image:
            try:
                self._normal_map = pygame.image.load(self.normal_map_path).convert_alpha()
            except Exception:
                self._normal_map = None

    def apply_to_surface(self, surface):
        """Apply material properties to a surface."""
        if not PYGAME_AVAILABLE:
            return
        surf = surface.copy()
        if self._texture:
            # Tile the texture
            tw, th = self._texture.get_size()
            sw, sh = surf.get_size()
            for x in range(0, sw, tw):
                for y in range(0, sh, th):
                    surf.blit(self._texture, (x, y))
        else:
            surf.fill(self.base_color)
        if self.emission != (0, 0, 0):
            emit_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            emit_surf.fill((*self.emission, int(self.opacity * 255)))
            surf.blit(emit_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        return surf


class PostProcessor:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.bloom_enabled = True
        self.bloom_threshold = 200
        self.bloom_intensity = 0.5
        self.bloom_radius = 8
        self.vignette_enabled = True
        self.vignette_strength = 0.3
        self.color_grade_enabled = True
        self.brightness = 1.0
        self.contrast = 1.0
        self.saturation = 1.0
        self.color_tint = (255, 255, 255)
        self.dof_enabled = False
        self.dof_focus_distance = 200
        self.dof_blur_amount = 4

    def apply_bloom(self, source, target):
        if not PYGAME_AVAILABLE or not self.bloom_enabled:
            return
        bloom_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pixels = pygame.PixelArray(source)
        for x in range(self.width):
            for y in range(self.height):
                r, g, b, _ = source.unmap_rgb(pixels[x][y])
                brightness = (r + g + b) / 3
                if brightness > self.bloom_threshold:
                    intensity = (brightness - self.bloom_threshold) / (255 - self.bloom_threshold)
                    alpha = int(intensity * self.bloom_intensity * 255)
                    bloom_surf.set_at((x, y), (r, g, b, alpha))
        del pixels
        bloom_surf = gaussian_blur(bloom_surf, self.bloom_radius)
        target.blit(bloom_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def apply_vignette(self, target):
        if not PYGAME_AVAILABLE or not self.vignette_enabled:
            return
        v = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width / 2, self.height / 2
        max_dist = math.sqrt(cx * cx + cy * cy)
        for x in range(0, self.width, 2):
            for y in range(0, self.height, 2):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                alpha = min(255, int((dist / max_dist) * self.vignette_strength * 255))
                v.set_at((x, y), (0, 0, 0, alpha))
                if x + 1 < self.width:
                    v.set_at((x + 1, y), (0, 0, 0, alpha))
                if y + 1 < self.height:
                    v.set_at((x, y + 1), (0, 0, 0, alpha))
        target.blit(v, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def apply_color_grading(self, target):
        if not PYGAME_AVAILABLE or not self.color_grade_enabled:
            return
        if self.brightness != 1.0 or self.contrast != 1.0 or self.saturation != 1.0 or self.color_tint != (255, 255, 255):
            pixels = pygame.PixelArray(target)
            for x in range(self.width):
                for y in range(self.height):
                    r, g, b, a = target.unmap_rgb(pixels[x][y])
                    r = int((r - 128) * self.contrast + 128 * self.brightness)
                    g = int((g - 128) * self.contrast + 128 * self.brightness)
                    b = int((b - 128) * self.contrast + 128 * self.brightness)
                    gray = (r + g + b) / 3
                    r = int(r * self.saturation + gray * (1 - self.saturation))
                    g = int(g * self.saturation + gray * (1 - self.saturation))
                    b = int(b * self.saturation + gray * (1 - self.saturation))
                    r = min(255, max(0, r * self.color_tint[0] // 255))
                    g = min(255, max(0, g * self.color_tint[1] // 255))
                    b = min(255, max(0, b * self.color_tint[2] // 255))
                    pixels[x][y] = (r, g, b, a)
            del pixels

    def process(self, source, target):
        if not PYGAME_AVAILABLE:
            return
        self.apply_bloom(source, target)
        self.apply_vignette(target)
        self.apply_color_grading(target)


class DecalRenderer:
    def __init__(self):
        self.decals = []

    def add_decal(self, surface, x, y, rotation=0, scale=1.0, alpha=255):
        self.decals.append({
            "surface": surface, "x": x, "y": y,
            "rotation": rotation, "scale": scale, "alpha": alpha
        })

    def render_all(self, target, camera=None):
        for d in self.decals:
            surf = d["surface"]
            if d["scale"] != 1.0:
                new_size = (int(surf.get_width() * d["scale"]), int(surf.get_height() * d["scale"]))
                surf = pygame.transform.scale(surf, new_size)
            if d["rotation"] != 0:
                surf = pygame.transform.rotate(surf, d["rotation"])
            if d["alpha"] < 255:
                surf.set_alpha(d["alpha"])
            sx, sy = d["x"], d["y"]
            if camera:
                sx, sy = camera.world_to_screen(sx, sy)
            target.blit(surf, (int(sx - surf.get_width() / 2), int(sy - surf.get_height() / 2)))
        self.decals.clear()


class SkyboxRenderer:
    def __init__(self, colors=None, stars=True, clouds=True):
        self.top_color = colors[0] if colors else (10, 10, 40)
        self.bottom_color = colors[1] if colors and len(colors) > 1 else (60, 40, 80)
        self.horizon_color = colors[2] if colors and len(colors) > 2 else (100, 80, 120)
        self.stars = stars
        self.clouds = clouds
        self._star_points = [(random.randint(0, 2000), random.randint(0, 1000), random.random()) for _ in range(200)]
        self._cloud_points = [(random.randint(0, 2000), random.randint(0, 600), random.randint(30, 80)) for _ in range(30)]
        self.time_of_day = 0.5

    def render(self, surface, width, height, camera_x=0, camera_y=0):
        if not PYGAME_AVAILABLE:
            return
        # Gradient sky
        for y in range(height):
            t = y / height
            if t < 0.5:
                c = tuple(int(a + (b - a) * t * 2) for a, b in zip(self.top_color, self.horizon_color))
            else:
                c = tuple(int(a + (b - a) * (t - 0.5) * 2) for a, b in zip(self.horizon_color, self.bottom_color))
            pygame.draw.line(surface, c, (0, y), (width, y))

        # Stars
        if self.stars:
            for sx, sy, sb in self._star_points:
                brightness = int(150 + sb * 105)
                visible_x = sx - camera_x * 0.1 % width
                visible_y = sy - camera_y * 0.1 % height
                if -5 < visible_x < width + 5 and -5 < visible_y < height + 5:
                    pygame.draw.circle(surface, (brightness, brightness, brightness, 200), 
                                      (int(visible_x), int(visible_y)), int(1 + sb))

        # Clouds
        if self.clouds:
            for cx, cy, cr in self._cloud_points:
                visible_x = ((cx - camera_x * 0.05) % (width + 200)) - 100
                if -100 < visible_x < width + 100:
                    cloud = pygame.Surface((cr * 3, cr), pygame.SRCALPHA)
                    for i in range(5):
                        ox = random.randint(0, cr * 3)
                        oy = random.randint(0, cr)
                        r = random.randint(cr // 3, cr // 2)
                        pygame.draw.circle(cloud, (200, 200, 220, 60), (ox, oy), r)
                    surface.blit(cloud, (int(visible_x), int(cy - camera_y * 0.1 % 600)))
