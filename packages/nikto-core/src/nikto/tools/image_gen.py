from uuid import uuid4
import numpy as np
from nikto.tools.base import Tool


class ImageGenerateTool(Tool):
    name = "image_generate"
    description = "Generate an image from a text prompt"

    async def execute(self, prompt: str, width: int = 512, height: int = 512, **kwargs) -> dict:
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (width, height), color=(20, 20, 40))
            draw = ImageDraw.Draw(img)
            draw.text((20, height // 2), prompt[:50], fill=(200, 200, 255))
            path = f"/tmp/nikto_image_{str(uuid4())[:8]}.png"
            img.save(path)
            return {"success": True, "path": path, "width": width, "height": height, "prompt": prompt}
        except Exception as e:
            return {"success": False, "error": str(e)}


class PatternGenerateTool(Tool):
    name = "pattern_generate"
    description = "Generate a checkerboard or geometric pattern"

    async def execute(self, pattern_type: str = "checkerboard", width: int = 256, height: int = 256, **kwargs) -> dict:
        try:
            from PIL import Image
            arr = np.zeros((height, width, 3), dtype=np.uint8)
            if pattern_type == "checkerboard":
                for y in range(height):
                    for x in range(width):
                        if (x // 32 + y // 32) % 2 == 0:
                            arr[y, x] = [255, 255, 255]
                        else:
                            arr[y, x] = [0, 0, 0]
            elif pattern_type == "gradient":
                for y in range(height):
                    for x in range(width):
                        arr[y, x] = [x * 255 // width, y * 255 // height, 128]
            img = Image.fromarray(arr)
            path = f"/tmp/nikto_pattern_{str(uuid4())[:8]}.png"
            img.save(path)
            return {"success": True, "path": path, "pattern_type": pattern_type}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def tool_generate_image(prompt: str, width: int = 512, height: int = 512) -> dict:
    tool = ImageGenerateTool()
    return await tool.execute(prompt=prompt, width=width, height=height)


async def tool_generate_pattern(pattern_type: str = "checkerboard", width: int = 256, height: int = 256) -> dict:
    tool = PatternGenerateTool()
    return await tool.execute(pattern_type=pattern_type, width=width, height=height)
