import torch
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
