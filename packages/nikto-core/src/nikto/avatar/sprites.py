"""Avatar sprite system — programmatic character drawing with poses, expressions, and glow effects."""
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops


AVATAR_WIDTH = 200
AVATAR_HEIGHT = 300

COLORS = {
    "body": (0, 180, 255),
    "body_dark": (0, 120, 200),
    "glow": (0, 220, 255),
    "eye": (255, 255, 255),
    "eye_pupil": (0, 200, 255),
    "mouth": (0, 200, 255),
    "accent": (0, 255, 200),
    "panel": (20, 30, 50),
    "panel_light": (40, 60, 90),
    "visor": (0, 200, 255),
    "shadow": (10, 15, 25),
}


def _rounded_rect(draw, xy, radius, fill, outline=None):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


class AvatarSprite:
    def __init__(self, width=AVATAR_WIDTH, height=AVATAR_HEIGHT):
        self.width = width
        self.height = height
        self.image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

    def clear(self):
        self.image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

    def draw_robot_body(self, pose="idle"):
        cx, cy = self.width // 2, self.height // 2

        # Shadow
        self.draw.ellipse([cx - 50, self.height - 30, cx + 50, self.height - 10], fill=(0, 0, 0, 60))

        if pose == "walking":
            body_offsets = [0, -3, 0, 3, 0]
        else:
            body_offsets = [0, 0, 0, 0, 0]

        # Legs
        leg_color = COLORS["body_dark"]
        self.draw.rounded_rectangle([cx - 30, cy + 50, cx - 15, cy + 90], radius=6, fill=leg_color)
        self.draw.rounded_rectangle([cx + 15, cy + 50, cx + 30, cy + 90], radius=6, fill=leg_color)

        # Feet
        self.draw.rounded_rectangle([cx - 35, cy + 85, cx - 10, cy + 100], radius=4, fill=COLORS["accent"])
        self.draw.rounded_rectangle([cx + 10, cy + 85, cx + 35, cy + 100], radius=4, fill=COLORS["accent"])

        # Body / Torso
        torso_color = COLORS["body"]
        self.draw.rounded_rectangle([cx - 40, cy - 20, cx + 40, cy + 55], radius=15, fill=torso_color)

        # Chest panel
        panel_y = cy + 5
        self.draw.rounded_rectangle([cx - 25, panel_y, cx + 25, panel_y + 30], radius=6, fill=COLORS["panel"])
        for i, label in enumerate(["|", "|", "|"]):
            lx = cx - 15 + i * 15
            self.draw.text((lx - 2, panel_y + 8), label, fill=COLORS["accent"])

        # Arms
        arm_color = COLORS["body_dark"]
        if pose == "working":
            self.draw.rounded_rectangle([cx - 55, cy - 10, cx - 40, cy + 35], radius=8, fill=arm_color)
            self.draw.rounded_rectangle([cx + 40, cy - 10, cx + 55, cy + 35], radius=8, fill=arm_color)
            # Hands typing
            for hx in [cx - 50, cx - 45, cx - 40, cx + 40, cx + 45, cx + 50]:
                self.draw.ellipse([hx - 4, cy + 32, hx + 4, cy + 40], fill=COLORS["accent"])
        elif pose == "pointing":
            self.draw.rounded_rectangle([cx - 55, cy - 10, cx - 40, cy + 20], radius=8, fill=arm_color)
            self.draw.rounded_rectangle([cx + 40, cy - 10, cx + 70, cy + 10], radius=8, fill=arm_color)
            self.draw.ellipse([cx + 66, cy + 6, cx + 74, cy + 14], fill=COLORS["accent"])
        else:
            self.draw.rounded_rectangle([cx - 55, cy - 10, cx - 40, cy + 25], radius=8, fill=arm_color)
            self.draw.rounded_rectangle([cx + 40, cy - 10, cx + 55, cy + 25], radius=8, fill=arm_color)

        # Neck
        self.draw.rounded_rectangle([cx - 8, cy - 28, cx + 8, cy - 18], radius=3, fill=COLORS["body_dark"])

        # Head
        head_cy = cy - 50
        self.draw.rounded_rectangle([cx - 35, head_cy - 25, cx + 35, head_cy + 15], radius=18, fill=COLORS["body"])

        # Antenna
        self.draw.line([cx, head_cy - 25, cx, head_cy - 38], fill=COLORS["body_dark"], width=3)
        self.draw.ellipse([cx - 5, head_cy - 44, cx + 5, head_cy - 34], fill=COLORS["glow"])

        return self.image

    def draw_eyes(self, expression="neutral", pupil_offset=0):
        cx = self.width // 2
        cy = self.height // 2 - 50
        eye_spacing = 20

        if expression == "happy":
            for ex in [cx - eye_spacing, cx + eye_spacing]:
                self.draw.arc([ex - 8, cy - 5, ex + 8, cy + 5], 0, 180, fill=COLORS["eye"], width=3)
            self.draw.arc([cx - 10, cy + 8, cx + 10, cy + 18], 0, 180, fill=COLORS["mouth"], width=3)
        elif expression == "surprised":
            for ex in [cx - eye_spacing, cx + eye_spacing]:
                self.draw.ellipse([ex - 8, cy - 8, ex + 8, cy + 8], fill=COLORS["eye"])
                self.draw.ellipse([ex - 4 + pupil_offset, cy - 4, ex + 4 + pupil_offset, cy + 4], fill=COLORS["eye_pupil"])
            self.draw.ellipse([cx - 6, cy + 8, cx + 6, cy + 18], fill=COLORS["mouth"])
        elif expression == "focused":
            for ex in [cx - eye_spacing, cx + eye_spacing]:
                self.draw.ellipse([ex - 6, cy - 6, ex + 6, cy + 6], fill=COLORS["eye"])
                self.draw.ellipse([ex - 2, cy - 2, ex + 2, cy + 2], fill=COLORS["eye_pupil"])
            self.draw.line([cx - 5, cy + 15, cx + 5, cy + 15], fill=COLORS["mouth"], width=3)
        else:
            for ex in [cx - eye_spacing, cx + eye_spacing]:
                self.draw.ellipse([ex - 7, cy - 7, ex + 7, cy + 7], fill=COLORS["eye"])
                self.draw.ellipse([ex - 3 + pupil_offset, cy - 3, ex + 3 + pupil_offset, cy + 3], fill=COLORS["eye_pupil"])
            self.draw.line([cx - 6, cy + 13, cx + 6, cy + 13], fill=COLORS["mouth"], width=2)

        return self.image

    def add_glow_effect(self):
        blurred = self.image.filter(ImageFilter.GaussianBlur(radius=8))
        glow = Image.new("RGBA", blurred.size, (0, 0, 0, 0))
        for x in range(blurred.width):
            for y in range(blurred.height):
                r, g, b, a = blurred.getpixel((x, y))
                if a > 0:
                    glow.putpixel((x, y), (r, g, b, max(30, a // 2)))
        self.image = Image.alpha_composite(glow, self.image)
        return self.image

    def render(self, pose="idle", expression="neutral", with_glow=True):
        self.clear()
        self.draw_robot_body(pose)
        self.draw_eyes(expression)
        if with_glow:
            self.add_glow_effect()
        return self.image


def create_avatar_frame(pose="idle", expression="neutral", width=AVATAR_WIDTH, height=AVATAR_HEIGHT):
    sprite = AvatarSprite(width, height)
    return sprite.render(pose, expression)


SPRITE_CACHE = {}

def get_sprite(pose="idle", expression="neutral"):
    key = f"{pose}_{expression}"
    if key not in SPRITE_CACHE:
        SPRITE_CACHE[key] = create_avatar_frame(pose, expression)
    return SPRITE_CACHE[key]


AVAILABLE_POSES = ["idle", "walking", "working", "pointing"]
AVAILABLE_EXPRESSIONS = ["neutral", "happy", "surprised", "focused"]