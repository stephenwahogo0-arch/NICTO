"""
NIKTO Avatar Personalization Engine — creates lively, accurate avatars from reference images.

Uses reference images (from Google Lens or other sources) to:
  1. Extract dominant color palettes
  2. Generate personalized avatar sprites
  3. Create natural animations: blinking, breathing, subtle movement
  4. Make the avatar feel alive and responsive
"""
import colorsys
import math
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


REF_DIR = os.path.expanduser("~/.nikto/avatar_refs")
PALETTE_PATH = os.path.expanduser("~/.nikto/avatar_palette.json")

AVATAR_SIZE = (200, 300)
RENDER_SCALE = 2


class ColorPalette:
    """Extract and manage color palettes from reference images."""

    @staticmethod
    def extract(image_path: str, num_colors: int = 8) -> list[tuple[int, int, int]]:
        """Extract dominant colors from an image using k-means-like quantization."""
        img = Image.open(image_path)
        img = img.resize((100, 100)).convert("RGB")
        pixels = list(img.getdata())

        # Simple color quantization: round colors and count frequencies
        buckets: dict[tuple[int, int, int], int] = {}
        for r, g, b in pixels:
            key = (r // 32 * 32, g // 32 * 32, b // 32 * 32)
            buckets[key] = buckets.get(key, 0) + 1

        sorted_colors = sorted(buckets.items(), key=lambda x: -x[1])
        return [color for color, _ in sorted_colors[:num_colors]]

    @staticmethod
    def dominant_color(image_path: str) -> tuple[int, int, int]:
        """Get the single dominant color."""
        colors = ColorPalette.extract(image_path, 1)
        return colors[0] if colors else (100, 100, 100)

    @staticmethod
    def skin_tone_detect(image_path: str) -> Optional[tuple[int, int, int]]:
        """Attempt to detect skin tone from reference image."""
        img = Image.open(image_path).resize((50, 50)).convert("RGB")
        pixels = list(img.getdata())
        skin_pixels = []
        for r, g, b in pixels:
            if r > 60 and g > 40 and b > 20 and r > g and r > b:
                if abs(r - g) > 10:
                    skin_pixels.append((r, g, b))
        if skin_pixels:
            avg_r = sum(p[0] for p in skin_pixels) // len(skin_pixels)
            avg_g = sum(p[1] for p in skin_pixels) // len(skin_pixels)
            avg_b = sum(p[2] for p in skin_pixels) // len(skin_pixels)
            return (avg_r, avg_g, avg_b)
        return None

    @staticmethod
    def complementary(color: tuple[int, int, int]) -> tuple[int, int, int]:
        """Get complementary color."""
        r, g, b = color
        return (255 - r, 255 - g, 255 - b)

    @staticmethod
    def analogous(color: tuple[int, int, int]) -> list[tuple[int, int, int]]:
        """Get analogous colors (30°, 60° offset on hue wheel)."""
        r, g, b = color
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        colors = []
        for offset in [-30, 30, 60]:
            nh = (h + offset / 360) % 1.0
            nr, ng, nb = colorsys.hsv_to_rgb(nh, s, v)
            colors.append((int(nr * 255), int(ng * 255), int(nb * 255)))
        return colors


class PersonalAvatarGenerator:
    """Generate personalized, lively avatar sprites from reference images."""

    def __init__(self, ref_dir: str = REF_DIR):
        self.ref_dir = Path(ref_dir)
        self.ref_dir.mkdir(parents=True, exist_ok=True)
        self.references = list(self.ref_dir.glob("*.jpg")) + list(self.ref_dir.glob("*.png"))
        self.palette: list[tuple[int, int, int]] = []
        self.skin_color: Optional[tuple[int, int, int]] = None
        self.hair_color: Optional[tuple[int, int, int]] = None
        self._extract_from_refs()

    def _extract_from_refs(self):
        """Extract palette and features from all reference images."""
        all_colors = []
        for ref in self.references:
            try:
                colors = ColorPalette.extract(str(ref), 4)
                all_colors.extend(colors)
                if not self.skin_color:
                    self.skin_color = ColorPalette.skin_tone_detect(str(ref))
            except Exception:
                pass

        # Average all extracted colors for final palette
        if all_colors:
            self.palette = all_colors[:8]

    def get_avatar_colors(self) -> dict:
        """Get personalized color scheme for avatar."""
        if self.skin_color:
            primary = self.skin_color
        elif self.palette:
            primary = self.palette[0]
        else:
            primary = (100, 160, 220)

        secondary = ColorPalette.complementary(primary)
        accent = ColorPalette.analogous(primary)[0] if self.palette else (0, 200, 255)

        return {
            "primary": primary,
            "secondary": secondary,
            "accent": accent,
            "skin": self.skin_color or (220, 180, 150),
            "palette": self.palette[:6],
        }

    def generate_lively_sprite(self, pose: str = "idle", expression: str = "neutral",
                                frame: int = 0) -> Image.Image:
        """Generate a personalized avatar sprite with natural liveliness."""
        colors = self.get_avatar_colors()
        skin = colors["skin"]
        primary = colors["primary"]
        accent = colors["accent"]

        w, h = AVATAR_SIZE[0] * RENDER_SCALE, AVATAR_SIZE[1] * RENDER_SCALE
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = w // 2, h // 2
        s = RENDER_SCALE

        # Breathing motion
        breath_offset = int(math.sin(frame * 0.15) * 3 * s)
        # Blink — every 120 frames (~2 seconds at 60fps)
        blinking = (frame % 120) < 4
        blink_amount = 1 if blinking else 0
        # Idle sway
        sway = int(math.sin(frame * 0.05) * 2 * s)

        # === Body ===
        body_top = int(130 * s) + breath_offset
        body_color = primary
        draw.ellipse([
            cx - int(40 * s) + sway, body_top,
            cx + int(40 * s) + sway, body_top + int(100 * s)
        ], fill=body_color, outline=(0, 0, 0, 60))

        # === Head ===
        head_cy = int(70 * s) + breath_offset
        head_r = int(50 * s)
        draw.ellipse([
            cx - head_r + sway, head_cy - head_r,
            cx + head_r + sway, head_cy + head_r
        ], fill=skin, outline=(0, 0, 0, 40))

        # === Hair (from palette) ===
        if self.palette and len(self.palette) > 1:
            hair_color = self.palette[1]
        else:
            hair_color = (60, 40, 30)
        draw.ellipse([
            cx - int(48 * s) + sway, head_cy - int(48 * s),
            cx + int(48 * s) + sway, head_cy - int(5 * s)
        ], fill=hair_color)

        # === Eyes ===
        eye_y = head_cy + int(5 * s)
        eye_spacing = int(20 * s)

        if blinking:
            # Closed eyes (line)
            draw.line([
                (cx - eye_spacing - int(10 * s) + sway, eye_y),
                (cx - eye_spacing + int(10 * s) + sway, eye_y)
            ], fill=(40, 30, 20), width=max(2, int(3 * s)))
            draw.line([
                (cx + eye_spacing - int(10 * s) + sway, eye_y),
                (cx + eye_spacing + int(10 * s) + sway, eye_y)
            ], fill=(40, 30, 20), width=max(2, int(3 * s)))
        else:
            # Open eyes
            for ex in [cx - eye_spacing + sway, cx + eye_spacing + sway]:
                # White
                draw.ellipse([ex - int(8 * s), eye_y - int(6 * s), ex + int(8 * s), eye_y + int(6 * s)], fill=(255, 255, 255))
                # Iris
                iris_offset_x = int(math.sin(frame * 0.1) * 2 * s)  # Micro-saccades
                draw.ellipse([ex - int(4 * s) + iris_offset_x, eye_y - int(4 * s), ex + int(4 * s) + iris_offset_x, eye_y + int(4 * s)], fill=(60, 40, 30))
                # Pupil
                draw.ellipse([ex - int(2 * s) + iris_offset_x, eye_y - int(2 * s), ex + int(2 * s) + iris_offset_x, eye_y + int(2 * s)], fill=(10, 10, 10))
                # Eye shine
                draw.ellipse([ex - int(3 * s) + iris_offset_x, eye_y - int(3 * s), ex - int(1 * s) + iris_offset_x, eye_y - int(1 * s)], fill=(255, 255, 255, 200))

        # === Eyebrows ===
        brow_y = eye_y - int(14 * s)
        brow_color = hair_color
        draw.line([
            (cx - eye_spacing - int(12 * s) + sway, brow_y),
            (cx - eye_spacing + int(10 * s) + sway, brow_y - int(2 * s))
        ], fill=brow_color, width=max(2, int(3 * s)))
        draw.line([
            (cx + eye_spacing - int(10 * s) + sway, brow_y - int(2 * s)),
            (cx + eye_spacing + int(12 * s) + sway, brow_y)
        ], fill=brow_color, width=max(2, int(3 * s)))

        # === Mouth (expression-based) ===
        mouth_y = head_cy + int(20 * s) + breath_offset
        expression_params = {
            "neutral": (0, 0, 0),
            "happy": (15, 5, 0),
            "sad": (-10, -5, 0),
            "surprised": (0, 0, 15),
            "focused": (0, -5, 0),
            "talking": (0, 0, 0),
        }
        params = expression_params.get(expression, (0, 0, 0))
        smile_offset, frown_offset, open_mouth = params

        mouth_w = int(20 * s)
        if open_mouth > 0:
            draw.ellipse([
                cx - mouth_w + sway, mouth_y,
                cx + mouth_w + sway, mouth_y + int(15 * s)
            ], fill=(80, 30, 30), outline=(40, 20, 20))
        else:
            # Smile curve
            draw.arc([
                cx - mouth_w + sway, mouth_y - int(3 * s) + smile_offset,
                cx + mouth_w + sway, mouth_y + int(8 * s) + frown_offset
            ], 0, 180, fill=(40, 30, 20), width=max(2, int(3 * s)))

        # === Cheek blush (subtle) ===
        blush_alpha = 30
        if expression in ("happy", "surprised"):
            blush_alpha = 60
        for ex in [cx - int(35 * s) + sway, cx + int(35 * s) + sway]:
            draw.ellipse([
                ex - int(8 * s), head_cy + int(10 * s),
                ex + int(8 * s), head_cy + int(18 * s)
            ], fill=(255, 150, 150, blush_alpha))

        # === Accent glow ring ===
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        glow_alpha = int(30 + math.sin(frame * 0.1) * 15)
        gdraw.ellipse([
            cx - int(55 * s) + sway, head_cy - int(55 * s),
            cx + int(55 * s) + sway, head_cy + int(55 * s)
        ], outline=(*accent, glow_alpha), width=max(2, int(2 * s)))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=int(4 * s)))
        img = Image.alpha_composite(img, glow)

        # Downscale for anti-aliasing
        if RENDER_SCALE > 1:
            img = img.resize(AVATAR_SIZE, Image.LANCZOS)

        return img

    def create_animation_frames(self, pose: str = "idle", expression: str = "neutral",
                                 num_frames: int = 60) -> list[Image.Image]:
        """Generate a sequence of frames for animation."""
        frames = []
        for f in range(num_frames):
            frame = self.generate_lively_sprite(pose, expression, f)
            frames.append(frame)
        return frames

    def has_references(self) -> bool:
        return len(self.references) > 0


def create_personalized_avatar(ref_dir: str = REF_DIR) -> PersonalAvatarGenerator:
    return PersonalAvatarGenerator(ref_dir)
