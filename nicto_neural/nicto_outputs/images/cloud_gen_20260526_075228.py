#!/usr/bin/env python3
"""NICTO Image Generation - Cloud GPU Script (generated 20260526_075228)"""
import torch
from diffusers import StableDiffusionXLPipeline

pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16",
)
pipe.to("cuda")

prompt = """a cyberpunk city"""
negative_prompt = """"""
generator = None

image = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt or None,
    width=1024,
    height=1024,
    num_inference_steps=30,
    guidance_scale=7.5,
    generator=generator,
).images[0]

image.save("nicto_img_20260526_075228.png")
print(f"Image saved: nicto_img_20260526_075228.png")
