import io
import os
import random
import struct
import tempfile
import zlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from nikto.tools.base import Tool


def _generate_png(width: int, height: int, pixels: bytes) -> bytes:
    """Generate a minimal PNG from raw RGBA pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw = b""
    for y in range(height):
        raw += b"\x00"
        for x in range(width):
            i = (y * width + x) * 4
            raw += pixels[i:i+4]

    return (
        b"\x89PNG\r\n\x1a\n" +
        chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
        chunk(b"IDAT", zlib.compress(raw)) +
        chunk(b"IEND", b"")
    )


async def tool_generate_image(prompt: str, width: int = 512, height: int = 512, output_format: str = "png") -> str:
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter

        img = Image.new("RGB", (width, height), (26, 26, 46))
        draw = ImageDraw.Draw(img)

        gradient = Image.new("RGB", (width, height))
        for y in range(height):
            r = int(26 + (y / height) * 40)
            g = int(26 + (y / height) * 60)
            b = int(46 + (y / height) * 80)
            for x in range(width):
                gradient.putpixel((x, y), (r, g, b))
        img = Image.blend(img, gradient, 0.5)

        draw = ImageDraw.Draw(img)
        try:
            font_large = ImageFont.truetype("arial.ttf", 28)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font_large = ImageFont.load_default()
            font_small = font_large

        lines = []
        words = prompt.split()
        current = ""
        for w in words:
            test = current + " " + w if current else w
            bbox = draw.textbbox((0, 0), test, font=font_large)
            if bbox[2] - bbox[0] > width - 40:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)

        line_height = 36
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font_large)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x + 1, start_y + i * line_height + 1), line, fill=(0, 0, 0), font=font_large)
            draw.text((x, start_y + i * line_height), line, fill=(0, 255, 255), font=font_large)

        decor_y = start_y - 10
        draw.rectangle([(width//2 - 200, decor_y), (width//2 + 200, decor_y + 2)], fill=(0, 200, 255))

        footer = "NIKTO GENERATIVE"
        bbox = draw.textbbox((0, 0), footer, font=font_small)
        fw = bbox[2] - bbox[0]
        draw.text(((width - fw) // 2, height - 30), footer, fill=(100, 100, 140), font=font_small)

        output_dir = Path(tempfile.gettempdir()) / "nikto_images"
        output_dir.mkdir(exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in prompt[:50])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_format == "png":
            output_path = output_dir / f"{safe_name}_{timestamp}.png"
            img.save(output_path, "PNG")
        elif output_format == "jpeg":
            output_path = output_dir / f"{safe_name}_{timestamp}.jpg"
            img.save(output_path, "JPEG", quality=85)
        else:
            output_path = output_dir / f"{safe_name}_{timestamp}.png"
            img.save(output_path, "PNG")

        return f"Image generated: {output_path} ({width}x{height}, {output_format})"

    except ImportError:
        return "Pillow not installed. Install with: uv pip install pillow"
    except Exception as e:
        return f"Error generating image: {str(e)}"


async def tool_generate_pattern(pattern_type: str = "checkerboard", width: int = 256, height: int = 256) -> str:
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        if pattern_type == "checkerboard":
            size = 32
            for y in range(0, height, size):
                for x in range(0, width, size):
                    if (x // size + y // size) % 2 == 0:
                        draw.rectangle([x, y, x + size - 1, y + size - 1], fill=(0, 0, 0))
        elif pattern_type == "gradient":
            for y in range(height):
                r = int((y / height) * 255)
                g = int((1 - y / height) * 255)
                b = 128
                for x in range(width):
                    draw.point((x, y), fill=(r, g, b))
        elif pattern_type == "noise":
            for x in range(width):
                for y in range(height):
                    r = random.randint(0, 255)
                    g = random.randint(0, 255)
                    b = random.randint(0, 255)
                    draw.point((x, y), fill=(r, g, b))
        elif pattern_type == "stripes":
            for y in range(height):
                if y % 20 < 10:
                    draw.line([(0, y), (width, y)], fill=(50, 50, 200), width=1)
        else:
            return f"Unknown pattern: {pattern_type}"

        output_dir = Path(tempfile.gettempdir()) / "nikto_images"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"pattern_{pattern_type}_{width}x{height}.png"
        img.save(output_path, "PNG")
        return f"Pattern generated: {output_path} ({width}x{height}, {pattern_type})"

    except ImportError:
        return "Pillow not installed."
    except Exception as e:
        return f"Error generating pattern: {str(e)}"


ImageGenerateTool = Tool(
    name="generate_image",
    description="Generate an image from a text prompt. Creates a visually styled PNG or JPEG with centered text on a gradient background.",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Text description of the image to generate"},
            "width": {"type": "integer", "description": "Image width in pixels (default 512)"},
            "height": {"type": "integer", "description": "Image height in pixels (default 512)"},
            "output_format": {"type": "string", "enum": ["png", "jpeg"], "description": "Output format"},
        },
        "required": ["prompt"],
    },
    async_function=tool_generate_image,
)

PatternGenerateTool = Tool(
    name="generate_pattern",
    description="Generate procedural patterns: checkerboard, gradient, noise, stripes. Saves as PNG.",
    parameters={
        "type": "object",
        "properties": {
            "pattern_type": {"type": "string", "enum": ["checkerboard", "gradient", "noise", "stripes"], "description": "Type of pattern"},
            "width": {"type": "integer", "description": "Image width"},
            "height": {"type": "integer", "description": "Image height"},
        },
        "required": ["pattern_type"],
    },
    async_function=tool_generate_pattern,
)
