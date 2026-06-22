#!/usr/bin/env python3
"""
NICTO Real AI — Video Generation Module
GPU mode: uses AnimateDiff / Modelscope Text-to-Video
CPU mode: generates prompts + Python code for cloud GPU execution.
"""
import json, os, sys, datetime
from pathlib import Path

HERE = Path(__file__).parent
OUTPUT_DIR = HERE / "nicto_outputs" / "videos"


def check_gpu():
    try:
        import torch
        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            return True, vram
        return False, 0
    except ImportError:
        return False, 0


class NICTOVideoGen:
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.pipe = None
        if mode == "auto":
            has_gpu, vram = check_gpu()
            self.mode = "gpu" if (has_gpu and vram >= 16) else "cpu"

    def _gpu_init(self):
        if self.pipe is not None:
            return
        print("Initializing Text-to-Video on GPU...")
        try:
            import torch
            from diffusers import DiffusionPipeline
            self.pipe = DiffusionPipeline.from_pretrained(
                "damo-vilab/text-to-video-ms-1.7b",
                torch_dtype=torch.float16,
                variant="fp16",
            )
            self.pipe.to("cuda")
            print("  Model loaded successfully.")
        except Exception as e:
            print(f"  GPU init failed: {e}")
            print("  Falling back to CPU mode.")
            self.mode = "cpu"

    def generate(self, prompt: str, num_frames: int = 16, fps: int = 8,
                 steps: int = 50, guidance: float = 7.5, seed: int = None) -> dict:
        if self.mode == "gpu":
            return self._gpu_generate(prompt, num_frames, fps, steps, guidance, seed)
        return self._cpu_generate(prompt, num_frames, fps, steps, seed)

    def _gpu_generate(self, prompt, num_frames, fps, steps, guidance, seed):
        self._gpu_init()
        import torch
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda").manual_seed(seed)

        video_frames = self.pipe(
            prompt=prompt,
            num_frames=num_frames,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=generator,
        ).frames[0]

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUTPUT_DIR / f"nicto_vid_{ts}"

        # Save as GIF
        gif_path = str(path) + ".gif"
        video_frames[0].save(
            gif_path, save_all=True, append_images=video_frames[1:],
            duration=1000 // fps, loop=0
        )

        # Save individual frames
        frames_dir = str(path) + "_frames"
        os.makedirs(frames_dir, exist_ok=True)
        for i, frame in enumerate(video_frames):
            frame.save(os.path.join(frames_dir, f"frame_{i:04d}.png"))

        return {
            "status": "completed",
            "gif_path": gif_path,
            "frames_dir": frames_dir,
            "num_frames": len(video_frames),
            "mode": "gpu",
            "prompt": prompt,
        }

    def _cpu_generate(self, prompt, num_frames, fps, steps, seed):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        script = f'''#!/usr/bin/env python3
"""NICTO Video Generation — Cloud GPU Script (generated {ts})"""
import torch
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained(
    "damo-vilab/text-to-video-ms-1.7b",
    torch_dtype=torch.float16,
    variant="fp16",
)
pipe.to("cuda")

{"generator = torch.Generator(device='cuda').manual_seed(" + str(seed) + ")" if seed is not None else "generator = None"}

prompt = \"\"\"{prompt}\"\"\"
video_frames = pipe(
    prompt=prompt,
    num_frames={num_frames},
    num_inference_steps={steps},
    guidance_scale=7.5,
    generator=generator,
).frames[0]

# Save as GIF
gif_path = "nicto_vid_{ts}.gif"
video_frames[0].save(
    gif_path, save_all=True, append_images=video_frames[1:],
    duration={1000 // fps}, loop=0
)
print(f"Video saved: {{gif_path}}")
'''
        script_path = OUTPUT_DIR / f"cloud_video_{ts}.py"
        with open(script_path, "w") as f:
            f.write(script)

        # Generate frame-by-frame description for manual creation
        frame_desc = []
        for i in range(num_frames):
            t = i / max(num_frames - 1, 1)
            frame_desc.append(f"Frame {i}: {prompt} — progress {t * 100:.0f}%")

        return {
            "status": "cpu_mode",
            "message": "No GPU with >=16GB VRAM detected. Generated cloud script.",
            "prompt": prompt,
            "num_frames": num_frames,
            "fps": fps,
            "cloud_script": str(script_path),
            "frame_descriptions": frame_desc,
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NICTO Video Generator")
    parser.add_argument("prompt", nargs="?", default=None, help="Video description")
    parser.add_argument("--mode", choices=["auto", "cpu", "gpu"], default="auto")
    parser.add_argument("--frames", type=int, default=16)
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    gen = NICTOVideoGen(mode=args.mode)

    if args.prompt:
        result = gen.generate(args.prompt, num_frames=args.frames, fps=args.fps, steps=args.steps, seed=args.seed)
        print(json.dumps(result, indent=2))
    else:
        print("NICTO Video Generator — Interactive Mode")
        while True:
            try:
                p = input("\nVideo description (or 'exit'): ").strip()
                if p.lower() in ("exit", "quit"):
                    break
                if p:
                    result = gen.generate(p)
                    print(json.dumps(result, indent=2))
            except (KeyboardInterrupt, EOFError):
                break


if __name__ == "__main__":
    main()
