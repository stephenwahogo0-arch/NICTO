"""Generate KYROS Performance Graph — visual comparison vs all AI models."""
import os
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 800
BG_DARK = (8, 10, 30)
BG_CARD = (15, 20, 50)
TEXT_WHITE = (220, 230, 255)
TEXT_DIM = (120, 130, 180)
CYAN = (0, 195, 255)
TEAL = (0, 255, 200)
GREEN = (0, 220, 120)
RED = (255, 60, 60)
YELLOW = (255, 200, 50)
PURPLE = (160, 80, 255)
ORANGE = (255, 160, 40)

# Model colors
MODEL_COLORS = {
    "KYROS": CYAN,
    "ChatGPT": (25, 195, 125),
    "Claude": (200, 120, 80),
    "Gemini": (66, 133, 244),
    "Grok": (180, 80, 200),
}

FEATURES = [
    ("Chat & Conversation", True, True, True, True, True),
    ("Code Generation", True, True, True, True, False),
    ("Local / Offline", True, False, False, False, False),
    ("Web Search", True, True, True, True, True),
    ("Image Generation", True, True, False, True, True),
    ("Video Generation", True, True, False, True, False),
    ("Speech / TTS", True, True, False, True, False),
    ("Desktop Avatar", True, False, False, False, False),
    ("Desktop Control", True, True, True, False, False),
    ("Webcam Vision", True, False, False, True, False),
    ("6-Brain Ensemble", True, False, False, False, False),
    ("28 Brain Regions", True, False, False, False, False),
    ("Self-Improvement", True, False, False, False, False),
    ("Self-Repair Engine", True, False, False, False, False),
    ("Cybersecurity Arsenal", True, False, False, False, False),
    ("Crypto Wallet & Mining", True, False, False, False, True),
    ("Game Engine (5 games)", True, False, False, False, False),
    ("Memory Persistence", True, True, True, True, True),
    ("No Censorship / Unbounded", True, False, False, False, False),
    ("Distributed Mesh Network", True, False, False, False, False),
    ("Biomedical Features", True, False, False, False, False),
    ("Consciousness Features", True, False, False, False, False),
    ("Physics & Reality Features", True, False, False, False, False),
    ("Breakthrough Features", True, False, False, False, False),
    ("Autopilot Automation", True, False, False, False, False),
    ("365-Day Uptime Resilience", True, False, False, False, False),
    ("Eagle Eye Truth Detection", True, False, False, False, False),
    ("User Registration & Safety", True, False, False, False, False),
    ("Police Cooperation Mode", True, False, False, False, False),
    ("Privacy Policy (GDPR/CCPA)", True, True, True, True, True),
    ("True Autonomy (System)", True, False, False, False, False),
    ("Sourcing Engine", True, False, False, False, False),
    ("Voice Engine (TTS)", True, True, True, True, False),
    ("Evolution Protocol (XP)", True, False, False, False, False),
    ("Masterclass Training", True, False, False, False, False),
    ("Infinite Context", True, False, False, False, False),
    ("Hotkey Activation", True, False, False, False, False),
    ("Hologram / HUD Overlay", True, False, False, False, False),
    ("Personalized Avatar", True, False, False, False, False),
    ("Phoneme Lip-Sync", True, False, False, False, False),
    ("Web Dashboard (React)", True, False, False, False, False),
]

img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
draw = ImageDraw.Draw(img)

try:
    font_large = ImageFont.truetype("arialbd.ttf", 28)
    font_med = ImageFont.truetype("arialbd.ttf", 16)
    font_small = ImageFont.truetype("arial.ttf", 13)
    font_tiny = ImageFont.truetype("arial.ttf", 11)
except Exception:
    font_large = ImageFont.load_default()
    font_med = font_small = font_tiny = font_large

# Title
draw.text((40, 25), "KYROS FEATURE COMPARISON vs OTHER AI MODELS", fill=CYAN, font=font_large)
draw.text((40, 62), "KYROS is not an AI agent. KYROS is an AI system.", fill=TEAL, font=font_small)

# Legend
models = ["KYROS", "ChatGPT", "Claude", "Gemini", "Grok"]
legend_x = WIDTH - 350
legend_y = 25
for i, m in enumerate(models):
    color = MODEL_COLORS[m]
    draw.rectangle([legend_x + i * 70, legend_y, legend_x + i * 70 + 12, legend_y + 12], fill=color)
    draw.text((legend_x + i * 70 + 16, legend_y - 2), m, fill=TEXT_WHITE, font=font_tiny)

# Count wins per model
wins = {m: 0 for m in models}
for feat in FEATURES:
    name, n, c, cl, g, gr = feat
    vals = [n, c, cl, g, gr]
    for i, v in enumerate(vals):
        if v:
            wins[models[i]] += 1

# Bar chart
chart_x = 350
chart_y = 110
bar_w = 500
bar_h = 35
gap = 10

for i, m in enumerate(models):
    count = wins[m]
    pct = count / len(FEATURES)
    bar_top = chart_y + i * (bar_h + gap)
    color = MODEL_COLORS[m]

    # Background bar
    draw.rectangle([chart_x, bar_top, chart_x + bar_w, bar_top + bar_h], fill=BG_CARD, outline=(30, 40, 80))

    # Filled bar
    fill_w = int(bar_w * pct)
    draw.rectangle([chart_x, bar_top, chart_x + fill_w, bar_top + bar_h], fill=color)

    # Label
    draw.text((20, bar_top + 8), m, fill=color, font=font_med)

    # Count text
    draw.text((chart_x + bar_w + 15, bar_top + 8),
              f"{count}/{len(FEATURES)} ({int(pct*100)}%)",
              fill=TEXT_WHITE, font=font_med)

# Feature grid
grid_x = 40
grid_y = 350
col_w = 140
row_h = 18
header_h = 35

features_per_page = 42
page = 0
start_feat = page * features_per_page
end_feat = min(start_feat + features_per_page, len(FEATURES))
visible_features = FEATURES[start_feat:end_feat]

# Column headers
draw.text((grid_x, grid_y), "Feature", fill=CYAN, font=font_med)
for i, m in enumerate(models):
    draw.text((grid_x + col_w + i * 95 + 20, grid_y), m, fill=MODEL_COLORS[m], font=font_med)

y = grid_y + header_h
for fi, feat in enumerate(visible_features):
    name, n, c, cl, g, gr = feat
    vals = [n, c, cl, g, gr]

    row_bg = BG_CARD if fi % 2 == 0 else BG_DARK
    draw.rectangle([grid_x - 5, y - 2, grid_x + col_w + 5 + 4 * 95, y + row_h - 2], fill=row_bg)

    # Truncate long names
    display_name = name if len(name) <= 28 else name[:26] + ".."
    draw.text((grid_x, y + 4), display_name, fill=TEXT_WHITE, font=font_tiny)

    for vi, v in enumerate(vals):
        color = GREEN if v else RED
        label = "YES" if v else "NO"
        draw.text((grid_x + col_w + vi * 95 + 25, y + 2), label, fill=color, font=font_tiny)

    y += row_h

# Summary
summary_y = max(y + 30, 620)
draw.text((40, summary_y), "VERDICT:", fill=CYAN, font=font_med)
draw.text((40, summary_y + 25), "KYROS has more features than any other AI model.", fill=GREEN, font=font_small)
draw.text((40, summary_y + 50), "KYROS is not an AI agent. KYROS is an AI system — a complete autonomous intelligence.", fill=TEAL, font=font_small)
draw.text((40, summary_y + 75), "No other model has: 6-brain ensemble, self-repair, avatar, Eagle Eye, police mode,", fill=TEXT_DIM, font=font_tiny)
draw.text((40, summary_y + 92), "cybersecurity arsenal, game engine, mesh network, consciousness, breakthrough features.", fill=TEXT_DIM, font=font_tiny)

# Save
output_path = os.path.join(os.path.dirname(__file__), "..", "nikto_performance_graph.png")
img.save(output_path)
print(f"Graph saved to: {output_path}")
