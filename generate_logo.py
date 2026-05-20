"""NIKTO logo — clean, professional design."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 800, 800
CX, CY = W // 2, H // 2

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Dark gradient background
bg = Image.new("RGBA", (W, H), (8, 8, 12))
for y in range(H):
    alpha = int(20 + 10 * (y / H))
    ImageDraw.Draw(bg).rectangle([0, y, W, y], fill=(10, 10, 18, alpha))

# Outer ring
for r in range(240, 200, -8):
    a = max(20, 100 - (240 - r))
    draw.ellipse([CX - r, CY - r, CX + r, CY + r], outline=(0, 100, 200, a), width=1)

# Inner ring
for r in range(180, 150, -6):
    a = max(30, 120 - (180 - r))
    draw.ellipse([CX - r, CY - r, CX + r, CY + r], outline=(0, 150, 255, a), width=1)

# Central hexagon (representing 6 brains)
hex_points = []
for i in range(6):
    angle = 3.14159 / 3 * i - 3.14159 / 2
    px = CX + 90 * 0.6 * (1.2 if i % 2 == 0 else 1.0) * (1 if i == 0 else (0.85 if i % 2 == 0 else 0.9))
    py = CY + 90 * 0.6 * (1.2 if i % 2 == 0 else 1.0) * (1 if i == 0 else (0.85 if i % 2 == 0 else 0.9))
    hex_points.append((CX + 80 * (1 if i % 2 == 0 else 0.87) * (1 if i in [0, 3] else 0.9),
                        CY + 80 * (1 if i % 2 == 0 else 0.87) * (1 if i in [0, 3] else 0.9)))
# Simpler hexagon
hex_pts = []
for i in range(6):
    angle = 3.14159 / 3 * i - 3.14159 / 6
    hex_pts.append((CX + 80 * (1 if i % 2 == 0 else 0.87),
                     CY + 80 * (1 if i % 2 == 0 else 0.87)))
# Better hexagon with math
hex_pts = []
for i in range(6):
    angle = 3.14159 / 3 * i - 3.14159 / 6
    r = 85
    hex_pts.append((CX + r * 0.866 * (1 if i % 2 == 0 else 0.866),
                    CY + r * 0.866 * (1 if i % 2 == 0 else 0.866)))
# Correct hexagon
hex_pts = []
for i in range(6):
    angle = 3.14159 / 3 * i - 3.14159 / 6
    hex_pts.append((CX + 80 * (1 if i % 2 == 0 else 0.866),
                    CY + 80 * (0.866 if i % 2 == 0 else 1.0)))
# Just use an octagon approximation
hex_pts = [(CX + 80, CY), (CX + 40, CY - 69), (CX - 40, CY - 69),
           (CX - 80, CY), (CX - 40, CY + 69), (CX + 40, CY + 69)]
draw.polygon(hex_pts, outline=(0, 180, 255, 200), width=2)

# Inner hexagon
inner_pts = [(CX + 50, CY), (CX + 25, CY - 43), (CX - 25, CY - 43),
             (CX - 50, CY), (CX - 25, CY + 43), (CX + 25, CY + 43)]
draw.polygon(inner_pts, outline=(100, 200, 255, 150), width=1)

# NIKTO text
try:
    font_big = ImageFont.truetype("arialbd.ttf", 56)
    font_small = ImageFont.truetype("arial.ttf", 18)
except:
    font_big = ImageFont.load_default()
    font_small = font_big

draw.text((CX, CY + 130), "NIKTO", fill=(0, 180, 255, 255), font=font_big, anchor="mm")
draw.text((CX, CY + 170), "AI SYSTEM", fill=(100, 150, 200, 180), font=font_small, anchor="mm")

# Subtle glow effect
glow = img.filter(ImageFilter.GaussianBlur(radius=6))

# Small decorative dots at corners of hex
dots = [(CX + 80, CY), (CX - 80, CY), (CX, CY - 69), (CX, CY + 69)]
for dx, dy in dots:
    draw.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=(0, 200, 255, 220))

final = Image.alpha_composite(bg, img)
final = Image.alpha_composite(final, glow.filter(ImageFilter.GaussianBlur(radius=2)))

output = os.path.join(os.path.dirname(__file__), "nikto_logo.png")
final.save(output)
print(f"Logo saved: {output}")
