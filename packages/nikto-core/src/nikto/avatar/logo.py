"""NIKTO Logo generator — professional AI system logo/profile picture."""
import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps


LOGO_SIZE = 512
COLOR_BG = (10, 15, 35)
COLOR_CYAN = (0, 195, 255)
COLOR_CYAN_DARK = (0, 100, 200)
COLOR_TEAL = (0, 255, 200)
COLOR_WHITE = (255, 255, 255)
COLOR_PURPLE = (100, 50, 180)
COLOR_GRADIENT_TOP = (0, 150, 255, 180)
COLOR_GRADIENT_BOT = (0, 50, 150, 60)


def _make_radial_glow(size, center, radius, color, alpha=100):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
                 fill=(color[0], color[1], color[2], alpha))
    return img.filter(ImageFilter.GaussianBlur(radius=radius * 0.4))


def generate_logo(size=LOGO_SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), COLOR_BG)
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    s = size / 512

    # === Background glow ===
    bg_glow = _make_radial_glow((size, size), (cx, cy), int(200 * s), COLOR_CYAN, 40)
    img = Image.alpha_composite(img, bg_glow)
    draw = ImageDraw.Draw(img)

    # === Outer hexagonal ring ===
    hex_radius = int(180 * s)
    hex_points = []
    for i in range(6):
        angle = math.radians(60 * i - 90)
        px = cx + hex_radius * math.cos(angle)
        py = cy + hex_radius * math.sin(angle)
        hex_points.append((px, py))
    draw.polygon(hex_points, outline=COLOR_CYAN, width=max(2, int(3 * s)))

    # === Inner hexagonal ring (glowing) ===
    hex_inner = int(155 * s)
    hex_points_inner = []
    for i in range(6):
        angle = math.radians(60 * i - 90)
        px = cx + hex_inner * math.cos(angle)
        py = cy + hex_inner * math.sin(angle)
        hex_points_inner.append((px, py))
    glow_inner = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_inner)
    gdraw.polygon(hex_points_inner, outline=(0, 200, 255, 120), width=max(3, int(4 * s)))
    glow_inner = glow_inner.filter(ImageFilter.GaussianBlur(radius=int(6 * s)))
    img = Image.alpha_composite(img, glow_inner)
    draw = ImageDraw.Draw(img)
    draw.polygon(hex_points_inner, outline=COLOR_TEAL, width=max(1, int(2 * s)))

    # === Brain/Circuit icon in center ===
    brain_r = int(60 * s)
    # Left hemisphere
    draw.ellipse([cx - brain_r, cy - brain_r // 2, cx, cy + brain_r // 2],
                 outline=COLOR_CYAN, width=max(2, int(3 * s)))
    # Right hemisphere
    draw.ellipse([cx, cy - brain_r // 2, cx + brain_r, cy + brain_r // 2],
                 outline=COLOR_CYAN, width=max(2, int(3 * s)))
    # Center bridge
    draw.rectangle([cx - int(8 * s), cy - int(25 * s), cx + int(8 * s), cy + int(25 * s)],
                   fill=COLOR_CYAN)
    # Brain glow
    brain_glow = _make_radial_glow((size, size), (cx, cy), int(70 * s), COLOR_CYAN, 60)
    img = Image.alpha_composite(img, brain_glow)
    draw = ImageDraw.Draw(img)

    # === Neural nodes ===
    node_positions = [
        (cx - int(40 * s), cy - int(20 * s)),
        (cx + int(40 * s), cy - int(20 * s)),
        (cx - int(35 * s), cy + int(15 * s)),
        (cx + int(35 * s), cy + int(15 * s)),
        (cx, cy - int(35 * s)),
        (cx, cy + int(30 * s)),
    ]
    for nx, ny in node_positions:
        draw.ellipse([nx - int(5 * s), ny - int(5 * s), nx + int(5 * s), ny + int(5 * s)], fill=COLOR_TEAL)
        ng = _make_radial_glow((size, size), (nx, ny), int(10 * s), COLOR_TEAL, 80)
        img = Image.alpha_composite(img, ng)
        draw = ImageDraw.Draw(img)

    # === Circuit lines ===
    circuit_paths = [
        (cx - int(80 * s), cy - int(50 * s), cx - int(50 * s), cy - int(50 * s)),
        (cx + int(50 * s), cy - int(50 * s), cx + int(80 * s), cy - int(50 * s)),
        (cx - int(80 * s), cy + int(50 * s), cx - int(50 * s), cy + int(50 * s)),
        (cx + int(50 * s), cy + int(50 * s), cx + int(80 * s), cy + int(50 * s)),
        (cx - int(90 * s), cy, cx - int(70 * s), cy),
        (cx + int(70 * s), cy, cx + int(90 * s), cy),
    ]
    for x1, y1, x2, y2 in circuit_paths:
        draw.line([(x1, y1), (x2, y2)], fill=COLOR_CYAN_DARK, width=max(1, int(2 * s)))

    # === NIKTO text ===
    text = "NIKTO"
    subtitle = "AI SYSTEM"
    try:
        font_size = int(72 * s)
        font = ImageFont.truetype("arialbd.ttf", font_size)
        sub_font = ImageFont.truetype("arial.ttf", int(28 * s))
    except (OSError, IOError):
        font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    # Text glow
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = cx - tw // 2
    ty = cy + int(100 * s)
    text_glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_glow)
    tdraw.text((tx, ty), text, fill=(0, 200, 255, 80), font=font)
    text_glow = text_glow.filter(ImageFilter.GaussianBlur(radius=int(8 * s)))
    img = Image.alpha_composite(img, text_glow)
    draw = ImageDraw.Draw(img)

    # Main text
    draw.text((tx, ty), text, fill=COLOR_CYAN, font=font)

    # Subtitle
    bbox2 = draw.textbbox((0, 0), subtitle, font=sub_font)
    sw = bbox2[2] - bbox2[0]
    draw.text((cx - sw // 2, ty + int(45 * s)), subtitle, fill=COLOR_TEAL, font=sub_font)

    # === Corner accents ===
    corner_len = int(30 * s)
    corners = [
        (int(20 * s), int(20 * s), int(20 * s) + corner_len, int(20 * s)),
        (int(20 * s), int(20 * s), int(20 * s), int(20 * s) + corner_len),
        (size - int(20 * s), int(20 * s), size - int(20 * s) - corner_len, int(20 * s)),
        (size - int(20 * s), int(20 * s), size - int(20 * s), int(20 * s) + corner_len),
        (int(20 * s), size - int(20 * s), int(20 * s) + corner_len, size - int(20 * s)),
        (int(20 * s), size - int(20 * s), int(20 * s), size - int(20 * s) - corner_len),
        (size - int(20 * s), size - int(20 * s), size - int(20 * s) - corner_len, size - int(20 * s)),
        (size - int(20 * s), size - int(20 * s), size - int(20 * s), size - int(20 * s) - corner_len),
    ]
    for x1, y1, x2, y2 in corners:
        draw.line([(x1, y1), (x2, y2)], fill=COLOR_CYAN_DARK, width=max(1, int(2 * s)))

    return img


def save_logo(path: str = None, size=LOGO_SIZE) -> str:
    if path is None:
        nikto_dir = os.path.expanduser("~/.nikto")
        os.makedirs(nikto_dir, exist_ok=True)
        path = os.path.join(nikto_dir, "nikto_logo.png")
    logo = generate_logo(size)
    logo.save(path, "PNG")
    return path


def get_logo(size=LOGO_SIZE) -> Image.Image:
    return generate_logo(size)


if __name__ == "__main__":
    path = save_logo()
    print(f"NIKTO logo saved to: {path}")
