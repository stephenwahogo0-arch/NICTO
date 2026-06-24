#!/usr/bin/env python3
"""NICTO Video Generation - Cloud GPU Script (generated 20260526_074754)"""
import torch
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained(
    "damo-vilab/text-to-video-ms-1.7b",
    torch_dtype=torch.float16,
    variant="fp16",
)
pipe.to("cuda")

generator = None

prompt = """a drone flying"""
video_frames = pipe(
    prompt=prompt,
    num_frames=16,
    num_inference_steps=50,
    guidance_scale=7.5,
    generator=generator,
).frames[0]

# Save as GIF
gif_path = "nicto_vid_20260526_074754.gif"
video_frames[0].save(
    gif_path, save_all=True, append_images=video_frames[1:],
    duration=125, loop=0
)
print(f"Video saved: {gif_path}")
