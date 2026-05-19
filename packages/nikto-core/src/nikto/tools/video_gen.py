import os
import random
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from nikto.tools.base import Tool


async def tool_generate_gif(prompt: str, width: int = 320, height: int = 240, frames: int = 12) -> str:
    try:
        from PIL import Image, ImageDraw, ImageFont

        images = []
        phrases = prompt.split(".")[0].split() if "." in prompt else prompt.split()
        phrase_parts = phrases if len(phrases) <= 3 else [phrases[i] for i in range(0, len(phrases), max(1, len(phrases)//3))]

        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()

        for step in range(frames):
            img = Image.new("RGB", (width, height), (10, 10, 30))
            draw = ImageDraw.Draw(img)

            phase = step / frames
            r = int(20 + phase * 60)
            g = int(20 + (1 - phase) * 60)
            b = int(50 + phase * 100)
            draw.rectangle([0, 0, width, height], fill=(r, g, b))

            dot_x = int(width * 0.5 + (width * 0.3) * (step / frames) * 2 - width * 0.3)
            dot_y = height // 2
            dot_r = 15 + int(5 * abs((step / frames) * 2 - 1))
            draw.ellipse([dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r], fill=(0, 255, 255))

            text_y = 30
            for pi, part in enumerate(phrase_parts):
                draw.text((20, text_y + pi * 28), part, fill=(200, 200, 255), font=font)
            draw.text((width - 150, height - 25), f"NIKTO GIF", fill=(100, 100, 150), font=font)

            images.append(img)

        output_dir = Path(tempfile.gettempdir()) / "nikto_videos"
        output_dir.mkdir(exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in prompt[:40])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{safe_name}_{timestamp}.gif"

        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=150,
            loop=0,
            optimize=True,
        )

        size_kb = os.path.getsize(output_path) / 1024
        return f"GIF generated: {output_path} ({width}x{height}, {frames} frames, {size_kb:.1f}KB)"

    except ImportError:
        return "Pillow not installed."
    except Exception as e:
        return f"Error generating GIF: {str(e)}"


async def tool_generate_video(prompt: str, width: int = 640, height: int = 480, duration_sec: int = 3) -> str:
    output_dir = Path(tempfile.gettempdir()) / "nikto_videos"
    output_dir.mkdir(exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in prompt[:40])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    frames_dir = output_dir / f"frames_{timestamp}"
    frames_dir.mkdir(exist_ok=True)

    try:
        from PIL import Image, ImageDraw, ImageFont

        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except Exception:
            font = ImageFont.load_default()

        fps = 10
        total_frames = duration_sec * fps
        frame_paths = []

        for step in range(total_frames):
            img = Image.new("RGB", (width, height), (10, 10, 30))
            draw = ImageDraw.Draw(img)

            phase = step / total_frames
            r = int(30 + phase * 100)
            g = int(30 + (1 - phase) * 60)
            b = int(80 + phase * 120)
            draw.rectangle([0, 0, width, height], fill=(r, g, b))

            cx, cy = width // 2, height // 2
            radius = 40 + int(30 * abs((phase * 4) % 2 - 1))
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(0, 255, 255), width=3)
            draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(0, 255, 255))

            draw.text((20, 20), f"NIKTO VIDEO", fill=(100, 100, 150), font=font)
            words = prompt.split()[:5]
            draw.text((20, 50), " ".join(words), fill=(200, 200, 255), font=font)
            draw.text((width - 120, height - 30), f"frame {step+1}/{total_frames}", fill=(80, 80, 100), font=font)

            fp = frames_dir / f"frame_{step:04d}.png"
            img.save(fp, "PNG")
            frame_paths.append(str(fp))

        output_path = output_dir / f"{safe_name}_{timestamp}.mp4"
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-framerate", str(fps), "-i",
                 str(frames_dir / "frame_%04d.png"),
                 "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 str(output_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                gif_path = output_dir / f"{safe_name}_{timestamp}.gif"
                from PIL import Image as PILImage
                pil_images = [PILImage.open(fp) for fp in frame_paths]
                pil_images[0].save(
                    gif_path, save_all=True, append_images=pil_images[1:],
                    duration=100, loop=0, optimize=True
                )
                output_path = gif_path
        except FileNotFoundError:
            gif_path = output_dir / f"{safe_name}_{timestamp}.gif"
            from PIL import Image as PILImage
            pil_images = [PILImage.open(fp) for fp in frame_paths]
            pil_images[0].save(
                gif_path, save_all=True, append_images=pil_images[1:],
                duration=100, loop=0, optimize=True
            )
            output_path = gif_path

        import shutil
        shutil.rmtree(str(frames_dir), ignore_errors=True)

        size_kb = os.path.getsize(output_path) / 1024
        fmt = output_path.suffix
        return f"Video generated: {output_path} ({width}x{height}, {duration_sec}s, {size_kb:.1f}KB, {fmt})"

    except ImportError:
        return "Pillow not installed."
    except Exception as e:
        return f"Error generating video: {str(e)}"


GifGenerateTool = Tool(
    name="generate_gif",
    description="Generate an animated GIF from a text prompt. Creates looping animation with moving elements across frames.",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Text description of the animation"},
            "width": {"type": "integer", "description": "Frame width"},
            "height": {"type": "integer", "description": "Frame height"},
            "frames": {"type": "integer", "description": "Number of animation frames (8-30)"},
        },
        "required": ["prompt"],
    },
    async_function=tool_generate_gif,
)

VideoGenerateTool = Tool(
    name="generate_video",
    description="Generate an MP4 video from a text prompt. Uses ffmpeg if available, falls back to animated GIF. Creates frame-by-frame animation with motion effects.",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Text description of the video content"},
            "width": {"type": "integer", "description": "Video width"},
            "height": {"type": "integer", "description": "Video height"},
            "duration_sec": {"type": "integer", "description": "Duration in seconds"},
        },
        "required": ["prompt"],
    },
    async_function=tool_generate_video,
)
