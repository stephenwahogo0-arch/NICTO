#!/usr/bin/env python3
"""
NICTO Real AI — Image Generation Module
GPU mode: uses Stable Diffusion XL / FLUX.1
CPU mode: generates prompts + Python code for cloud GPU execution.
"""
import json, os, sys, datetime, tempfile, subprocess
from pathlib import Path

HERE = Path(__file__).parent
OUTPUT_DIR = HERE / "nicto_outputs" / "images"


def check_gpu():
    try:
        import torch
        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            return True, torch.cuda.get_device_name(0), vram
        return False, None, 0
    except ImportError:
        return False, None, 0


def check_diffusers():
    try:
        import diffusers
        return True
    except ImportError:
        return False


class NICTOImageGen:
    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.pipe = None
        if mode == "auto":
            has_gpu, _, vram = check_gpu()
            self.mode = "gpu" if (has_gpu and vram >= 8) else "cpu"

    def _get_model(self):
        return "stabilityai/stable-diffusion-xl-base-1.0"

    def _gpu_init(self):
        if self.pipe is not None:
            return
        print("Initializing SDXL on GPU...")
        try:
            import torch
            from diffusers import StableDiffusionXLPipeline
            model = self._get_model()
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                model, torch_dtype=torch.float16, variant="fp16"
            )
            self.pipe.to("cuda")
            print("  SDXL loaded successfully.")
        except Exception as e:
            print(f"  GPU init failed: {e}")
            print("  Falling back to CPU mode.")
            self.mode = "cpu"

    def generate(self, prompt: str, negative_prompt: str = "", width: int = 1024, height: int = 1024,
                 steps: int = 30, guidance: float = 7.5, seed: int = None) -> dict:
        if self.mode == "gpu":
            return self._gpu_generate(prompt, negative_prompt, width, height, steps, guidance, seed)
        return self._cpu_generate(prompt, negative_prompt, width, height, steps, guidance, seed)

    def _gpu_generate(self, prompt, negative_prompt, width, height, steps, guidance, seed):
        self._gpu_init()
        import torch
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cuda").manual_seed(seed)

        image = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt or None,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=generator,
        ).images[0]

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUTPUT_DIR / f"nicto_img_{ts}.png"
        image.save(path)
        return {"status": "completed", "path": str(path), "mode": "gpu", "prompt": prompt}

    def _cpu_generate(self, prompt, negative_prompt, width, height, steps, guidance, seed):
        """CPU mode: generate Python script for cloud GPU execution."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        script = f'''#!/usr/bin/env python3
"""NICTO Image Generation — Cloud GPU Script (generated {ts})"""
import torch
from diffusers import StableDiffusionXLPipeline

pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16",
)
pipe.to("cuda")

prompt = """{prompt}"""
negative_prompt = """{negative_prompt or ""}"""
{"generator = torch.Generator(device='cuda').manual_seed(" + str(seed) + ")" if seed is not None else "generator = None"}

image = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt or None,
    width={width},
    height={height},
    num_inference_steps={steps},
    guidance_scale={guidance},
    generator=generator,
).images[0]

image.save("nicto_img_{ts}.png")
print(f"Image saved: nicto_img_{ts}.png")
'''
        script_path = OUTPUT_DIR / f"cloud_gen_{ts}.py"
        with open(script_path, "w") as f:
            f.write(script)

        torch_code = '''import torch
import torch.nn as nn

class NICTO_CPU_ImageGen:
    """
    CPU Fallback: Image generation prompt + code generator.
    Use this output as input to any image generation model.
    """

    @staticmethod
    def enhance_prompt(prompt: str) -> dict:
        prompt_map = {
            "cyber": "cyberpunk cityscape with neon lights, digital rain, high contrast, dark atmosphere, holographic displays, cinematic lighting, 8K",
            "nature": "photorealistic landscape, golden hour lighting, detailed foliage, natural colors, depth of field, professional photography",
            "code": "abstract digital art representing computer code, green matrix style, glowing syntax on dark background, data streams, technology concept",
            "portrait": "professional portrait photography, soft lighting, shallow depth of field, natural skin tones, high detail, editorial style",
            "game": "fantasy video game concept art, vibrant colors, epic composition, detailed environment, unreal engine 5 style, trending on ArtStation",
        }
        for key, enhanced in prompt_map.items():
            if key in prompt.lower():
                return {"original": prompt, "enhanced": enhanced}
        return {"original": prompt, "enhanced": f"{prompt}, high quality, detailed, professional"}

    @staticmethod
    def generate_prompt(description: str) -> str:
        enhancer = NICTO_CPU_ImageGen.enhance_prompt(description)
        return enhancer["enhanced"]
'''
        code_path = OUTPUT_DIR / f"cpu_fallback_gen_{ts}.py"
        with open(code_path, "w") as f:
            f.write(torch_code)

        return {
            "status": "cpu_mode",
            "message": "No GPU detected. Generated cloud script and CPU fallback code.",
            "prompt": prompt,
            "enhanced_prompt": self._enhance_prompt(prompt).get("enhanced", prompt),
            "cloud_script": str(script_path),
            "cpu_code": str(code_path),
        }

    def _enhance_prompt(self, prompt: str) -> dict:
        prompt_map = {
            "cyber": "cyberpunk cityscape with neon lights, digital rain, high contrast, dark atmosphere, holographic displays, cinematic lighting",
            "nature": "photorealistic landscape, golden hour lighting, detailed foliage, natural colors, depth of field, professional photography",
            "code": "abstract digital art representing computer code, green matrix style, glowing syntax on dark background, data streams, technology concept",
            "portrait": "professional portrait photography, soft lighting, shallow depth of field, natural skin tones, high detail, editorial style",
            "game": "fantasy video game concept art, vibrant colors, epic composition, detailed environment, unreal engine 5 style, trending on ArtStation",
        }
        for key, enhanced in prompt_map.items():
            if key in prompt.lower():
                return {"original": prompt, "enhanced": enhanced}
        return {"original": prompt, "enhanced": f"{prompt}, high quality, detailed, professional"}

    def batch_generate(self, prompts: list, **kwargs) -> list:
        return [self.generate(p, **kwargs) for p in prompts]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NICTO Image Generator")
    parser.add_argument("prompt", nargs="?", default=None, help="Image description")
    parser.add_argument("--mode", choices=["auto", "cpu", "gpu"], default="auto")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    gen = NICTOImageGen(mode=args.mode)

    if args.prompt:
        result = gen.generate(args.prompt, width=args.width, height=args.height, steps=args.steps, seed=args.seed)
        print(json.dumps(result, indent=2))
    else:
        print("NICTO Image Generator — Interactive Mode")
        print("Enter an image description (or 'exit'):")
        while True:
            try:
                p = input("\nPrompt: ").strip()
                if p.lower() in ("exit", "quit"):
                    break
                if p:
                    result = gen.generate(p)
                    print(json.dumps(result, indent=2))
            except (KeyboardInterrupt, EOFError):
                break


if __name__ == "__main__":
    main()
