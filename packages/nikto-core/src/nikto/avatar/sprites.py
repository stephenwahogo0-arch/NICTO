"""Avatar sprite system — premium rendering with anti-aliasing, gradients, 3D depth, and fine textures."""
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps


AVATAR_WIDTH = 200
AVATAR_HEIGHT = 300
RENDER_SCALE = 2  # Render at 2x for anti-aliasing, then downscale

# Extended color palette with gradients
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CYAN_PRIMARY = (0, 180, 255)
CYAN_LIGHT = (100, 220, 255)
CYAN_DARK = (0, 80, 160)
CYAN_GLOW = (0, 230, 255)
TEAL_ACCENT = (0, 255, 200)
TEAL_DARK = (0, 180, 140)
PURPLE_DEEP = (40, 20, 80)
NAVY_DARK = (10, 15, 40)
PANEL_BG = (15, 25, 50)
PANEL_HIGHLIGHT = (30, 50, 90)
CHROME_MID = (180, 200, 220)
CHROME_LIGHT = (220, 235, 255)
CHROME_DARK = (80, 100, 130)


def _make_linear_gradient(size, color_stops, horizontal=False):
    """Create a linear gradient image."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size
    if horizontal:
        for x in range(w):
            ratio = x / max(w - 1, 1)
            c = _gradient_at(ratio, color_stops)
            draw.line([(x, 0), (x, h)], fill=c)
    else:
        for y in range(h):
            ratio = y / max(h - 1, 1)
            c = _gradient_at(ratio, color_stops)
            draw.line([(0, y), (w, y)], fill=c)
    return img


def _make_radial_gradient(size, center, radius, color_stops):
    """Create a radial gradient image using box blur for speed."""
    from PIL import ImageDraw as _ImageDraw
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = _ImageDraw.Draw(img)
    inner_color = color_stops[0][1]
    outer_color = color_stops[-1][1]
    draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], fill=inner_color)
    img = img.filter(ImageFilter.GaussianBlur(radius=radius * 0.3))
    return img


def _gradient_at(ratio, color_stops):
    stops = sorted(color_stops, key=lambda s: s[0])
    if ratio <= stops[0][0]:
        return stops[0][1]
    if ratio >= stops[-1][0]:
        return stops[-1][1]
    for i in range(len(stops) - 1):
        if stops[i][0] <= ratio <= stops[i + 1][0]:
            t = (ratio - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
            c1 = stops[i][1]
            c2 = stops[i + 1][1]
            return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
    return stops[-1][1]


def _rounded_polygon(draw, points, radius, fill, outline=None):
    if not points:
        return
    draw.polygon(points, fill=fill, outline=outline)


def _soft_glow(img, radius=10, intensity=0.4):
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
    overlay = blurred.copy()
    alpha = overlay.split()[3]
    overlay.putalpha(alpha.point(lambda v: min(int(v * intensity), 255)))
    return Image.alpha_composite(overlay, img)


def _chrome_gradient(w, h, base_color, highlight_color):
    metallic = [(0.0, base_color), (0.3, highlight_color), (0.5, base_color), (0.7, highlight_color), (1.0, base_color)]
    return _make_linear_gradient((w, h), metallic)


class AvatarSprite:
    def __init__(self, width=AVATAR_WIDTH, height=AVATAR_HEIGHT):
        self.output_w = width
        self.output_h = height
        self.scale = RENDER_SCALE
        self.w = width * self.scale
        self.h = height * self.scale
        self.image = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

    def _scale(self, *values):
        return tuple(v * self.scale for v in values)

    def clear(self):
        self.image = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

    def _finalize(self):
        return self.image.resize((self.output_w, self.output_h), Image.Resampling.LANCZOS)

    def draw_gradient_rect(self, bbox, color_stops, radius=0, horizontal=False):
        x1, y1, x2, y2 = bbox
        w, h = x2 - x1, y2 - y1
        gradient = _make_linear_gradient((w, h), color_stops, horizontal)
        if radius > 0:
            mask = Image.new("L", (w, h), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
            gradient.putalpha(mask)
        self.image.paste(gradient, (x1, y1), gradient)

    def draw_body(self, pose="idle"):
        cx, cy = self.w // 2, self.h // 2
        s = self.scale

        # Shadow
        shadow_y = self.h - int(15 * s)
        self.draw.ellipse([cx - int(50 * s), shadow_y - int(5 * s), cx + int(50 * s), shadow_y + int(5 * s)],
                          fill=(0, 0, 0, 80))

        # === LEGS ===
        leg_grad = [(0.0, CYAN_DARK), (0.5, CYAN_PRIMARY), (1.0, CYAN_DARK)]
        leg_w, leg_h = int(14 * s), int(38 * s)
        for lx in [cx - int(26 * s), cx + int(12 * s)]:
            self.draw_gradient_rect((lx, cy + int(50 * s), lx + leg_w, cy + int(50 * s) + leg_h), leg_grad, radius=int(5 * s))

        # Feet
        foot_color = TEAL_ACCENT
        for fx in [cx - int(32 * s), cx + int(8 * s)]:
            self.draw.rounded_rectangle([fx, cy + int(84 * s), fx + int(24 * s), cy + int(96 * s)],
                                        radius=int(4 * s), fill=foot_color)

        # === TORSO ===
        body_grad = [(0.0, CYAN_LIGHT), (0.2, CYAN_PRIMARY), (0.6, CYAN_PRIMARY), (1.0, CYAN_DARK)]
        self.draw_gradient_rect((cx - int(38 * s), cy - int(18 * s), cx + int(38 * s), cy + int(52 * s)),
                                body_grad, radius=int(14 * s))

        # Shoulder pads
        shoulder_grad = [(0.0, CYAN_DARK), (1.0, CYAN_PRIMARY)]
        self.draw_gradient_rect((cx - int(50 * s), cy - int(22 * s), cx - int(36 * s), cy - int(6 * s)),
                                shoulder_grad, radius=int(6 * s))
        self.draw_gradient_rect((cx + int(36 * s), cy - int(22 * s), cx + int(50 * s), cy - int(6 * s)),
                                shoulder_grad, radius=int(6 * s))

        # Chest core glow
        core_center = (cx, cy + int(18 * s))
        core_radius = int(20 * s)
        glow = _make_radial_gradient((self.w, self.h), core_center, core_radius,
                                     [(0.0, (100, 255, 255, 80)), (0.5, (0, 180, 255, 40)), (1.0, (0, 0, 0, 0))])
        self.image = Image.alpha_composite(self.image, glow)
        self.draw = ImageDraw.Draw(self.image)

        # Chest panel
        panel_grad = [(0.0, PANEL_BG), (0.5, PANEL_HIGHLIGHT), (1.0, PANEL_BG)]
        self.draw_gradient_rect((cx - int(22 * s), cy + int(5 * s), cx + int(22 * s), cy + int(30 * s)),
                                panel_grad, radius=int(5 * s))

        # Panel LEDs
        led_colors = [TEAL_ACCENT, CYAN_PRIMARY, (255, 200, 0)]
        for i, lc in enumerate(led_colors):
            lx = cx - int(14 * s) + i * int(14 * s)
            # Glow
            self.draw.ellipse([lx - int(5 * s), cy + int(11 * s), lx + int(5 * s), cy + int(21 * s)],
                              fill=(lc[0], lc[1], lc[2], 60))
            # LED
            self.draw.ellipse([lx - int(3 * s), cy + int(13 * s), lx + int(3 * s), cy + int(19 * s)],
                              fill=lc)

        # === ARMS ===
        arm_grad = [(0.0, CYAN_DARK), (0.3, CYAN_PRIMARY), (1.0, CYAN_DARK)]
        if pose == "working":
            self.draw_gradient_rect((cx - int(52 * s), cy - int(8 * s), cx - int(40 * s), cy + int(32 * s)),
                                    arm_grad, radius=int(6 * s))
            self.draw_gradient_rect((cx + int(40 * s), cy - int(8 * s), cx + int(52 * s), cy + int(32 * s)),
                                    arm_grad, radius=int(6 * s))
            for hx in [cx - int(48 * s), cx - int(44 * s), cx - int(40 * s),
                       cx + int(40 * s), cx + int(44 * s), cx + int(48 * s)]:
                self.draw.ellipse([hx - int(3 * s), cy + int(30 * s), hx + int(3 * s), cy + int(36 * s)], fill=TEAL_ACCENT)
        elif pose == "pointing":
            self.draw_gradient_rect((cx - int(52 * s), cy - int(8 * s), cx - int(40 * s), cy + int(18 * s)),
                                    arm_grad, radius=int(6 * s))
            self.draw_gradient_rect((cx + int(38 * s), cy - int(8 * s), cx + int(66 * s), cy + int(8 * s)),
                                    arm_grad, radius=int(6 * s))
            self.draw.ellipse([cx + int(62 * s), cy + int(4 * s), cx + int(70 * s), cy + int(12 * s)], fill=TEAL_ACCENT)
        elif pose == "walking":
            self.draw_gradient_rect((cx - int(52 * s), cy - int(6 * s), cx - int(40 * s), cy + int(28 * s)),
                                    arm_grad, radius=int(6 * s))
            self.draw_gradient_rect((cx + int(40 * s), cy - int(6 * s), cx + int(52 * s), cy + int(22 * s)),
                                    arm_grad, radius=int(6 * s))
        else:
            self.draw_gradient_rect((cx - int(52 * s), cy - int(8 * s), cx - int(40 * s), cy + int(24 * s)),
                                    arm_grad, radius=int(6 * s))
            self.draw_gradient_rect((cx + int(40 * s), cy - int(8 * s), cx + int(52 * s), cy + int(24 * s)),
                                    arm_grad, radius=int(6 * s))

        # === NECK ===
        neck_grad = [(0.0, CHROME_LIGHT), (0.5, CHROME_MID), (1.0, CHROME_DARK)]
        self.draw_gradient_rect((cx - int(7 * s), cy - int(26 * s), cx + int(7 * s), cy - int(18 * s)),
                                neck_grad, radius=int(3 * s))

        # === HEAD ===
        head_grad = [(0.0, CYAN_LIGHT), (0.3, CYAN_PRIMARY), (0.7, CYAN_PRIMARY), (1.0, CYAN_DARK)]
        head_top = cy - int(48 * s)
        head_bot = cy - int(12 * s)
        self.draw_gradient_rect((cx - int(34 * s), head_top, cx + int(34 * s), head_bot),
                                head_grad, radius=int(16 * s))

        # Head chrome trim
        trim_color = CHROME_LIGHT
        self.draw.rounded_rectangle([cx - int(34 * s), head_top + int(2 * s), cx + int(34 * s), head_top + int(6 * s)],
                                    radius=int(3 * s), fill=trim_color)

        # === ANTENNA ===
        ant_x = cx
        ant_top = head_top - int(14 * s)
        self.draw.line([ant_x, head_top, ant_x, ant_top], fill=CHROME_MID, width=max(1, int(2 * s)))
        ant_glow = _make_radial_gradient((self.w, self.h), (ant_x, ant_top), int(6 * s),
                                         [(0.0, (0, 255, 255, 200)), (0.5, (0, 200, 255, 80)), (1.0, (0, 0, 0, 0))])
        self.image = Image.alpha_composite(self.image, ant_glow)
        self.draw = ImageDraw.Draw(self.image)
        self.draw.ellipse([ant_x - int(4 * s), ant_top - int(4 * s), ant_x + int(4 * s), ant_top + int(4 * s)],
                          fill=CYAN_GLOW)

    def draw_face(self, expression="neutral", pupil_offset=0):
        cx = self.w // 2
        cy = self.h // 2 - int(50 * self.scale)
        s = self.scale
        es = int(20 * s)  # eye spacing

        # === EYES ===
        eye_y = cy - int(2 * s)

        if expression == "happy":
            # Happy eyes - arcs (smiling)
            for ex in [cx - es, cx + es]:
                self.draw.arc([ex - int(7 * s), eye_y - int(4 * s), ex + int(7 * s), eye_y + int(4 * s)],
                              0, 180, fill=WHITE, width=max(1, int(3 * s)))
                # Eye glow
                self.draw.ellipse([ex - int(10 * s), eye_y - int(7 * s), ex + int(10 * s), eye_y + int(7 * s)],
                                  fill=(255, 255, 255, 30))
            # Smiling mouth
            self.draw.arc([cx - int(10 * s), cy + int(8 * s), cx + int(10 * s), cy + int(18 * s)],
                          0, 180, fill=CYAN_PRIMARY, width=max(1, int(3 * s)))

        elif expression == "surprised":
            for ex in [cx - es, cx + es]:
                # Large circular eyes
                self.draw.ellipse([ex - int(8 * s), eye_y - int(8 * s), ex + int(8 * s), eye_y + int(8 * s)],
                                  fill=WHITE)
                self.draw.ellipse([ex - int(4 * s) + pupil_offset, eye_y - int(4 * s),
                                   ex + int(4 * s) + pupil_offset, eye_y + int(4 * s)],
                                  fill=CYAN_PRIMARY)
                self.draw.ellipse([ex - int(11 * s), eye_y - int(11 * s), ex + int(11 * s), eye_y + int(11 * s)],
                                  fill=(255, 255, 255, 20))
            # Open mouth
            self.draw.ellipse([cx - int(6 * s), cy + int(8 * s), cx + int(6 * s), cy + int(18 * s)], fill=CYAN_PRIMARY)

        elif expression == "focused":
            for ex in [cx - es, cx + es]:
                self.draw.ellipse([ex - int(6 * s), eye_y - int(6 * s), ex + int(6 * s), eye_y + int(6 * s)],
                                  fill=WHITE)
                self.draw.ellipse([ex - int(2 * s), eye_y - int(2 * s), ex + int(2 * s), eye_y + int(2 * s)],
                                  fill=CYAN_PRIMARY)
            # Straight line mouth
            self.draw.line([cx - int(6 * s), cy + int(14 * s), cx + int(6 * s), cy + int(14 * s)],
                           fill=CYAN_PRIMARY, width=max(1, int(2 * s)))

        elif expression == "listening":
            for ex in [cx - es, cx + es]:
                self.draw.ellipse([ex - int(6 * s), eye_y - int(6 * s), ex + int(6 * s), eye_y + int(6 * s)],
                                  fill=WHITE)
                self.draw.ellipse([ex - int(2 * s) + int(1 * s), eye_y - int(2 * s),
                                   ex + int(2 * s) + int(1 * s), eye_y + int(2 * s)],
                                  fill=CYAN_PRIMARY)
            # Small o mouth
            self.draw.ellipse([cx - int(3 * s), cy + int(12 * s), cx + int(3 * s), cy + int(16 * s)], fill=CYAN_PRIMARY)

        elif expression == "thinking":
            for ex in [cx - es, cx + es]:
                self.draw.ellipse([ex - int(6 * s), eye_y - int(6 * s), ex + int(6 * s), eye_y + int(6 * s)],
                                  fill=WHITE)
                # Looking up (pupils shifted up)
                self.draw.ellipse([ex - int(2 * s), eye_y - int(4 * s), ex + int(2 * s), eye_y],
                                  fill=CYAN_PRIMARY)
            self.draw.line([cx - int(4 * s), cy + int(14 * s), cx + int(4 * s), cy + int(14 * s)],
                           fill=CYAN_PRIMARY, width=max(1, int(2 * s)))

        else:  # neutral
            for ex in [cx - es, cx + es]:
                self.draw.ellipse([ex - int(7 * s), eye_y - int(7 * s), ex + int(7 * s), eye_y + int(7 * s)],
                                  fill=WHITE)
                self.draw.ellipse([ex - int(3 * s) + pupil_offset, eye_y - int(3 * s),
                                   ex + int(3 * s) + pupil_offset, eye_y + int(3 * s)],
                                  fill=CYAN_PRIMARY)
            # Neutral mouth
            self.draw.line([cx - int(5 * s), cy + int(14 * s), cx + int(5 * s), cy + int(14 * s)],
                           fill=CYAN_PRIMARY, width=max(1, int(2 * s)))

    def add_final_effects(self):
        """Add glow, ambient light, and final polish using PIL filters."""
        alpha = self.image.split()[3]
        glow_mask = alpha.filter(ImageFilter.GaussianBlur(radius=int(4 * self.scale)))
        glow = Image.new("RGBA", self.image.size, (0, 200, 255, 0))
        glow.putalpha(glow_mask.point(lambda v: min(v, 60)))
        self.image = Image.alpha_composite(glow, self.image)

        light_overlay = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
        light_draw = ImageDraw.Draw(light_overlay)
        for y in range(self.image.height):
            ratio = y / self.image.height
            a = int(30 * (1 - ratio))
            light_draw.line([(0, y), (self.image.width, y)], fill=(255, 255, 255, a))

    def render(self, pose="idle", expression="neutral"):
        self.clear()
        self.draw_body(pose)
        self.draw_face(expression)
        self.add_final_effects()
        return self._finalize()


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
AVAILABLE_EXPRESSIONS = ["neutral", "happy", "surprised", "focused", "listening", "thinking"]