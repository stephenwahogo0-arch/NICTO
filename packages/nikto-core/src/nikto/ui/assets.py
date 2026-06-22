import os
from nikto.ui.theme import NICTO_THEME

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

C = NICTO_THEME["colors"]

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "generated")

def _ensure_dir():
    os.makedirs(ASSETS_DIR, exist_ok=True)

def generate_banner(output_path=None):
    if not PILLOW_AVAILABLE:
        return None
    _ensure_dir()
    path = output_path or os.path.join(ASSETS_DIR, "nicto_banner.png")
    img = Image.new("RGB", (1200, 400), C["bg_primary"])
    draw = ImageDraw.Draw(img)
    # Matrix-style grid lines
    for x in range(0, 1200, 40):
        draw.line([(x, 0), (x, 400)], fill=C["bg_secondary"], width=1)
    for y in range(0, 400, 40):
        draw.line([(0, y), (1200, y)], fill=C["bg_secondary"], width=1)
    # Corner brackets
    bracket_color = C["border_mid"]
    draw.line([(20, 20), (80, 20)], fill=bracket_color, width=3)
    draw.line([(20, 20), (20, 80)], fill=bracket_color, width=3)
    draw.line([(1120, 20), (1180, 20)], fill=bracket_color, width=3)
    draw.line([(1180, 20), (1180, 80)], fill=bracket_color, width=3)
    draw.line([(20, 320), (80, 320)], fill=bracket_color, width=3)
    draw.line([(20, 320), (20, 380)], fill=bracket_color, width=3)
    draw.line([(1120, 320), (1180, 320)], fill=bracket_color, width=3)
    draw.line([(1180, 320), (1180, 380)], fill=bracket_color, width=3)
    # Status bar
    draw.rectangle([(0, 0), (1200, 28)], fill=C["bg_secondary"])
    draw.text((10, 4), "SYSTEM: ONLINE  |  NICTO v2.0  |  Autonomous Intelligence", fill=C["text_muted"])
    dot_color = C["accent_primary"]
    draw.ellipse([(1170, 8), (1185, 23)], fill=dot_color)
    # Neural network icon (hexagon with nodes)
    cx, cy = 150, 180
    hexagon = []
    for i in range(6):
        angle = 3.14159 * 2 * i / 6 - 3.14159 / 2
        hexagon.append((cx + 70 * __import__('math').cos(angle), cy + 70 * __import__('math').sin(angle)))
    draw.polygon(hexagon, outline=C["accent_primary"], width=2)
    # Inner hexagon
    inner_hex = []
    for i in range(6):
        angle = 3.14159 * 2 * i / 6 - 3.14159 / 2
        inner_hex.append((cx + 35 * __import__('math').cos(angle), cy + 35 * __import__('math').sin(angle)))
    draw.polygon(inner_hex, outline=C["accent_electric"], width=1)
    # Neural nodes
    import random
    random.seed(42)
    for _ in range(20):
        nx, ny = cx + random.randint(-65, 65), cy + random.randint(-65, 65)
        draw.ellipse([(nx - 3, ny - 3), (nx + 3, ny + 3)], fill=C["accent_neon"])
    connections = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]
    for s, e in connections:
        draw.line([hexagon[s], hexagon[e]], fill=C["accent_primary"], width=1)
    # Center hexagon connections to outer
    for i in range(6):
        draw.line([hexagon[i], inner_hex[i]], fill=C["accent_electric"], width=1)
    # NICTO text
    draw.text((320, 140), "NICTO", fill=C["accent_primary"])
    draw.text((320, 210), "AUTONOMOUS INTELLIGENCE", fill=C["accent_electric"])
    draw.text((320, 250), "v2.0  |  Neural Independent Cognitive Thought Operator", fill=C["text_muted"])
    # Binary string at bottom
    binary = "01001110 01001001 01000011 01010100 01001111"
    draw.text((320, 370), binary, fill=C["border_dim"])
    img.save(path)
    return path

def generate_icon(output_path=None):
    if not PILLOW_AVAILABLE:
        return None
    _ensure_dir()
    path = output_path or os.path.join(ASSETS_DIR, "nicto_icon.png")
    img = Image.new("RGB", (800, 800), C["bg_primary"])
    draw = ImageDraw.Draw(img)
    # Radial green glow
    for r in range(400, 0, -4):
        intensity = int(255 * (r / 400))
        color = (0, int(100 * (r / 400)), 0)
        draw.ellipse([(400 - r, 400 - r), (400 + r, 400 + r)], outline=color)
    # Concentric hexagon rings
    for radius in [200, 150, 100, 50]:
        hexagon = []
        for i in range(6):
            angle = 3.14159 * 2 * i / 6 - 3.14159 / 2
            hexagon.append((400 + radius * __import__('math').cos(angle), 400 + radius * __import__('math').sin(angle)))
        draw.polygon(hexagon, outline=C["border_mid" if radius > 100 else C["accent_primary"]], width=2)
    # N letter
    draw.text((320, 280), "N", fill=C["accent_primary"])
    # Neural nodes
    import random
    random.seed(42)
    for _ in range(30):
        nx, ny = 400 + random.randint(-180, 180), 400 + random.randint(-180, 180)
        draw.ellipse([(nx - 4, ny - 4), (nx + 4, ny + 4)], fill=C["accent_neon"])
    draw.text((300, 510), "NICTO", fill=C["accent_electric"])
    draw.text((260, 550), "AUTONOMOUS AI", fill=C["text_muted"])
    img.save(path)
    return path

def generate_favicon(output_path=None):
    if not PILLOW_AVAILABLE:
        return None
    _ensure_dir()
    path = output_path or os.path.join(ASSETS_DIR, "favicon.png")
    img = Image.new("RGB", (64, 64), C["bg_primary"])
    draw = ImageDraw.Draw(img)
    # Hexagon
    hexagon = []
    for i in range(6):
        angle = 3.14159 * 2 * i / 6 - 3.14159 / 2
        hexagon.append((32 + 20 * __import__('math').cos(angle), 32 + 20 * __import__('math').sin(angle)))
    draw.polygon(hexagon, outline=C["accent_neon"], width=2)
    # N
    draw.text((22, 18), "N", fill=C["accent_primary"])
    img.save(path)
    return path

def generate_terminal_banner():
    return '''
 \u2588\u2588\u2588\u2557   \u2588\u2588\u2588\u2557\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557
 \u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2591\u2588\u2588\u2591\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595\u2570\u2570\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595
 \u2588\u2588\u2594\u2588\u2588\u2557\u2588\u2588\u2591\u2588\u2588\u2591\u2588\u2588\u2595       \u2588\u2588\u2595   \u2588\u2588\u2595   \u2588\u2588\u2595   \u2588\u2588\u2595
 \u2588\u2588\u2595\u255a\u2588\u2588\u2557\u2588\u2588\u2591\u2588\u2588\u2591\u2588\u2588\u2595       \u2588\u2588\u2595   \u2588\u2588\u2595   \u2588\u2588\u2595   \u2588\u2588\u2595
 \u2588\u2588\u2595 \u255a\u2588\u2588\u2588\u2588\u2591\u2588\u2588\u2591\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595   \u2588\u2588\u2595   \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595
 \u255a\u2588\u2588\u2595  \u255a\u2588\u2588\u2588\u2588\u2595\u255a\u2588\u2588\u2595 \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595   \u255a\u2588\u2588\u2595    \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595
  \u255a\u2588\u2588\u2595  \u255a\u2588\u2588\u2588\u2588\u2595\u255a\u2588\u2588\u2595 \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595   \u255a\u2588\u2588\u2595    \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595
    AUTONOMOUS INTELLIGENCE v2.0
    Built by Stephen Wahogo \u00b7 Nairobi, Kenya
    '''
