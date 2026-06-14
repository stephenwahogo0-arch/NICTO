"""AI Asset Factory — procedural texture, material, and model generation."""

from __future__ import annotations
import math
import random
import struct
from typing import Optional
from pathlib import Path


def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


class TextureGenerator:
    """Generates procedural textures using Pillow + numpy."""

    def generate_brick(self, w: int, h: int, output_path: str):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (w, h), (180, 80, 60))
        draw = ImageDraw.Draw(img)
        brick_h = h // 8
        for row in range(8):
            y0 = row * brick_h
            offset = (w // 2) if row % 2 else 0
            for col in range(-1, w // (w // 4) + 2):
                x0 = col * (w // 4) + offset
                shade = random.randint(140, 200)
                draw.rectangle([x0, y0, x0 + w // 4 - 2, y0 + brick_h - 2],
                               fill=(shade, shade // 2, shade // 3))
        img.save(output_path)

    def generate_metal(self, w: int, h: int, output_path: str):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (w, h), (120, 120, 130))
        draw = ImageDraw.Draw(img)
        for _ in range(30):
            x = random.randint(0, w)
            y = random.randint(0, h)
            shade = random.randint(100, 180)
            draw.ellipse([x, y, x + random.randint(5, 20), y + random.randint(5, 20)],
                         fill=(shade, shade, shade + 10))
        img.save(output_path)

    def generate_grass(self, w: int, h: int, output_path: str):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (w, h), (40, 100, 30))
        draw = ImageDraw.Draw(img)
        for _ in range(200):
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            shade = random.randint(30, 80)
            draw.point((x, y), fill=(shade, shade + 60, shade))
        img.save(output_path)

    def generate_wood(self, w: int, h: int, output_path: str):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (w, h), (140, 100, 60))
        draw = ImageDraw.Draw(img)
        for y in range(0, h, 8):
            shade = random.randint(100, 160)
            draw.line([(0, y), (w, y)], fill=(shade, shade - 20, shade - 40), width=2)
        img.save(output_path)

    def generate_stone(self, w: int, h: int, output_path: str):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (w, h), (100, 100, 100))
        draw = ImageDraw.Draw(img)
        for _ in range(50):
            x = random.randint(0, w - 16)
            y = random.randint(0, h - 12)
            shade = random.randint(80, 130)
            draw.rectangle([x, y, x + 15, y + 11], fill=(shade, shade, shade))
            draw.rectangle([x + 1, y + 1, x + 14, y + 10], fill=(shade + 10, shade + 10, shade + 10))
        img.save(output_path)


class AssetFactory:
    """Manages all asset generation pipelines."""

    def __init__(self):
        self.textures = TextureGenerator()

    async def generate_all(self, output_dir: str, texture_size: int = 256) -> dict[str, list[str]]:
        from nicto_game.assets.textures import ensure_dir
        assets: dict[str, list[str]] = {"textures": [], "audio": []}

        tex_dir = Path(output_dir) / "assets" / "textures"
        tex_dir.mkdir(parents=True, exist_ok=True)

        tex_map = {
            "brick.png": lambda: self.textures.generate_brick(texture_size, texture_size, str(tex_dir / "brick.png")),
            "metal.png": lambda: self.textures.generate_metal(texture_size, texture_size, str(tex_dir / "metal.png")),
            "grass.png": lambda: self.textures.generate_grass(texture_size, texture_size, str(tex_dir / "grass.png")),
            "wood.png": lambda: self.textures.generate_wood(texture_size, texture_size, str(tex_dir / "wood.png")),
            "stone.png": lambda: self.textures.generate_stone(texture_size, texture_size, str(tex_dir / "stone.png")),
        }

        for name, gen in tex_map.items():
            try:
                gen()
                assets["textures"].append(str(tex_dir / name))
            except Exception as e:
                print(f"Warning: texture {name} failed: {e}")

        return assets
