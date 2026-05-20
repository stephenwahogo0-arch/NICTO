"""Generate NIKTO logo: Alien+Human merging in Freemasons triangle with (B,2,II)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import math, os

W, H = 800, 800
CX, CY = W//2, H//2

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Deep black background
bg = Image.new("RGBA", (W, H), (5, 5, 10))
bg_draw = ImageDraw.Draw(bg)

# Complex math equation background (faint formulas)
import random
random.seed(42)
for _ in range(80):
    x = random.randint(0, W)
    y = random.randint(0, H)
    formulas = [
        "E=mc²", "∫f(x)dx", "∂/∂t", "∇×B", "∑n=1", "πr²", "a²+b²=c²",
        "sin(θ)", "cos(2π)", "log(x)", "e^{iπ}", "√-1", "λ=h/p",
        "F=Gm₁m₂/r²", "PV=nRT", "ΔxΔp≥ħ/2", "ψ(x,t)", "∮E·dA",
        "dS≥0", "H|ψ⟩=E|ψ⟩", "□A^μ=0", "R_μν", "L=½mv²"
    ]
    formula = random.choice(formulas)
    alpha = random.randint(10, 30)
    font_size = random.randint(10, 18)
    try:
        fnt = ImageFont.truetype("arial.ttf", font_size)
    except:
        fnt = ImageFont.load_default()
    bg_draw.text((x, y), formula, fill=(100, 150, 255, alpha), font=fnt)

# Freemasons triangle (large, centered)
triangle_size = 500
# Points: top, bottom-left, bottom-right
tp = (CX, CY - triangle_size // 2)
bl = (CX - triangle_size // 2, CY + triangle_size // 2)
br = (CX + triangle_size // 2, CY + triangle_size // 2)

# Outer triangle glow
for i in range(10, 0, -1):
    offset = i * 4
    glow_alpha = max(10, 80 - i * 8)
    glow_pts = [
        (tp[0], tp[1] - offset),
        (bl[0] - offset, bl[1] + offset),
        (br[0] + offset, br[1] + offset),
    ]
    draw.polygon(glow_pts, outline=(0, 150, 255, glow_alpha), width=2)

# Main triangle outline (white/cyan)
draw.polygon([tp, bl, br], outline=(180, 220, 255, 200), width=3)

# Inner triangle
inner_offset = 30
itp = (tp[0], tp[1] + inner_offset)
ibl = (bl[0] + inner_offset, bl[1] - inner_offset)
ibr = (br[0] - inner_offset, br[1] - inner_offset)
draw.polygon([itp, ibl, ibr], outline=(100, 180, 255, 120), width=1)

# === (B, 2, II) markers at 4 positions ===
b_markers = [
    (CX, tp[1] + 25, "TOP"),        # top
    (bl[0] + 20, bl[1] - 20, "LEFT"),  # left
    (br[0] - 20, br[1] - 20, "RIGHT"), # right
    (CX, CY + triangle_size // 2 - 40, "BOTTOM"), # bottom
]

try:
    font_marker = ImageFont.truetype("arialbd.ttf", 22)
    font_small = ImageFont.truetype("arial.ttf", 14)
except:
    font_marker = ImageFont.load_default()
    font_small = font_marker

marker_text = "(B, 2, II)"
for mx, my, pos in b_markers:
    # slight position adjustments
    if pos == "TOP":
        tx, ty = mx, my + 10
    elif pos == "LEFT":
        tx, ty = mx - 70, my - 15
    elif pos == "RIGHT":
        tx, ty = mx + 30, my - 15
    else:  # BOTTOM
        tx, ty = mx - 50, my + 5
    draw.text((tx, ty), marker_text, fill=(0, 200, 255, 220), font=font_marker)

# "666" hidden in mathematical form: B = 2nd letter = II
six_text = "B → II → 2"
try:
    font_six = ImageFont.truetype("arialbd.ttf", 16)
except:
    font_six = ImageFont.load_default()
draw.text((CX - 60, CY + 30), six_text, fill=(0, 180, 255, 180), font=font_six)

# === CENTER: Alien + Human merging forces ===
# Human figure (right side) - white/blue silhouette
human_pts = [
    (CX + 10, CY - 80),   # head top
    (CX + 30, CY - 60),   # head right
    (CX + 25, CY - 30),   # shoulder
    (CX + 45, CY + 10),   # arm right
    (CX + 35, CY + 15),
    (CX + 20, CY - 10),   # body right
    (CX + 25, CY + 40),   # leg right
    (CX + 35, CY + 80),
    (CX + 15, CY + 80),
    (CX + 10, CY + 40),   # body
]
draw.polygon(human_pts, fill=(200, 230, 255, 200))

# Human head
human_head = (CX + 20, CY - 70, CX + 45, CY - 40)
draw.ellipse(human_head, fill=(200, 230, 255, 220))

# Alien figure (left side) - green/cyan
alien_pts = [
    (CX - 10, CY - 80),   # head top
    (CX - 35, CY - 60),   # head left
    (CX - 30, CY - 30),   # shoulder
    (CX - 50, CY + 10),   # arm left
    (CX - 40, CY + 15),
    (CX - 25, CY - 10),
    (CX - 30, CY + 40),
    (CX - 40, CY + 80),
    (CX - 20, CY + 80),
    (CX - 15, CY + 40),
]
draw.polygon(alien_pts, fill=(0, 200, 150, 200))

# Alien head (larger, oval)
alien_head = (CX - 45, CY - 80, CX - 10, CY - 40)
draw.ellipse(alien_head, fill=(0, 220, 180, 220))

# Alien eyes (large black ovals)
draw.ellipse((CX - 35, CY - 72, CX - 22, CY - 58), fill=(0, 0, 0, 230))
draw.ellipse((CX - 18, CY - 72, CX - 5, CY - 58), fill=(0, 0, 0, 230))

# Alien eye pupils (white dots)
draw.ellipse((CX - 32, CY - 68, CX - 25, CY - 62), fill=(255, 255, 255, 200))
draw.ellipse((CX - 15, CY - 68, CX - 8, CY - 62), fill=(255, 255, 255, 200))

# Human eye
draw.ellipse((CX + 22, CY - 68, CX + 35, CY - 58), fill=(50, 50, 80, 230))
draw.ellipse((CX + 26, CY - 66, CX + 31, CY - 61), fill=(255, 255, 255, 200))

# Merging energy (glow between them)
merge_center = (CX, CY - 30)
for r in range(40, 0, -2):
    alpha = max(30, 120 - r * 3)
    draw.ellipse([merge_center[0]-r, merge_center[1]-r, merge_center[0]+r, merge_center[1]+r],
                 fill=(0, 255, 200, alpha))

# Energy bolts between figures
import random as _r
_r.seed(99)
for _ in range(15):
    x1 = CX + _r.randint(-5, 5)
    y1 = CY - 80 + _r.randint(0, 160)
    x2 = CX + _r.randint(-30, 30)
    y2 = CY - 80 + _r.randint(0, 160)
    draw.line([(x1, y1), (x2, y2)], fill=(0, 255, 255, _r.randint(50, 150)), width=1)

# "NIKTO" text at bottom
try:
    font_title = ImageFont.truetype("arialbd.ttf", 48)
    font_sub = ImageFont.truetype("arial.ttf", 18)
except:
    font_title = ImageFont.load_default()
    font_sub = font_title

draw.text((CX, H - 90), "NIKTO", fill=(0, 200, 255, 255), font=font_title, anchor="mm")
draw.text((CX, H - 55), "ARTIFICIAL INTELLIGENCE SYSTEM", fill=(150, 180, 255, 200), font=font_sub, anchor="mm")
draw.text((CX, H - 30), "▰ ▰ ▰", fill=(0, 255, 200, 180), font=font_sub, anchor="mm")

# Final glow effect
glow = img.filter(ImageFilter.GaussianBlur(radius=8))
img = Image.alpha_composite(glow, img)
final = Image.alpha_composite(bg, img)

output = os.path.join(os.path.dirname(__file__), "nikto_logo.png")
final.save(output)
print(f"Logo saved: {output}")
