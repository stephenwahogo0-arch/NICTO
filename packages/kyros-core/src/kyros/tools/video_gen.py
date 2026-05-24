from uuid import uuid4
from kyros.tools.base import Tool


class GifGenerateTool(Tool):
    name = "gif_generate"
    description = "Generate an animated GIF from frames or text"

    async def execute(self, text: str = "", frames: int = 10, **kwargs) -> dict:
        try:
            from PIL import Image
            images = []
            for i in range(frames):
                img = Image.new("RGB", (200, 200), color=(i * 25 % 255, 50, 100))
                images.append(img)
            path = f"/tmp/kyros_gif_{str(uuid4())[:8]}.gif"
            images[0].save(path, save_all=True, append_images=images[1:], duration=100, loop=0)
            return {"success": True, "path": path, "frames": frames, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}


class VideoGenerateTool(Tool):
    name = "video_generate"
    description = "Generate a video from frames"

    async def execute(self, text: str = "", duration_sec: int = 2, **kwargs) -> dict:
        try:
            import imageio
            import numpy as np
            fps = 10
            total_frames = duration_sec * fps
            frames = []
            for i in range(total_frames):
                frame = np.zeros((100, 100, 3), dtype=np.uint8)
                frame[:, :, 0] = i * 255 // total_frames
                frames.append(frame)
            path = f"/tmp/kyros_video_{str(uuid4())[:8]}.mp4"
            imageio.mimsave(path, frames, fps=fps)
            return {"success": True, "path": path, "duration_sec": duration_sec, "frames": total_frames}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def tool_generate_gif(text: str = "", frames: int = 10) -> dict:
    tool = GifGenerateTool()
    return await tool.execute(text=text, frames=frames)
