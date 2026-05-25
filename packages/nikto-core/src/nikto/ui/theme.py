NICTO_THEME = {
    "name": "NICTO Cyber Green",
    "version": "2.0",

    "colors": {
        "bg_primary":      "#000000",
        "bg_secondary":    "#000D02",
        "bg_panel":        "#001505",
        "bg_card":         "#001A06",
        "border_dim":      "#003C14",
        "border_mid":      "#00B43C",
        "border_bright":   "#00FF64",
        "accent_primary":  "#00FF64",
        "accent_electric": "#00FFAA",
        "accent_neon":     "#39FF14",
        "accent_glow":     "#64FF8C",
        "text_primary":    "#DCFCE7",
        "text_secondary":  "#86EFAC",
        "text_muted":      "#3D6B50",
        "text_code":       "#00FF64",
        "danger":          "#FF4444",
        "warning":         "#FFB800",
        "success":         "#00FF64",
        "info":            "#00FFAA",
    },

    "fonts": {
        "heading":    "Poppins Bold",
        "body":       "Poppins Regular",
        "mono":       "DejaVu Sans Mono",
        "ui":         "Poppins Medium",
    },

    "textual": {
        "background":        "#000000",
        "surface":           "#001505",
        "primary":           "#00FF64",
        "secondary":         "#00FFAA",
        "accent":            "#39FF14",
        "foreground":        "#DCFCE7",
        "success":           "#00FF64",
        "error":             "#FF4444",
        "warning":           "#FFB800",
        "border":            "#00B43C",
    },

    "rich": {
        "prompt":     "bold bright_green",
        "response":   "green",
        "code":       "bright_green on grey3",
        "tool_call":  "bold cyan",
        "system":     "dim green",
        "error":      "bold red",
        "success":    "bold bright_green",
        "heading":    "bold underline bright_green",
        "dim":        "dim green",
    },

    "logo_ascii": '''
 \u2588\u2588\u2588\u2557   \u2588\u2588\u2588\u2557\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557
 \u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2591\u2588\u2588\u2591\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595\u2570\u2570\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595
 \u2588\u2588\u2594\u2588\u2588\u2557\u2588\u2588\u2591\u2588\u2588\u2591\u2588\u2588\u2595       \u2588\u2588\u2595   \u2588\u2588\u2595   \u2588\u2588\u2595   \u2588\u2588\u2595
 \u2588\u2588\u2595\u255a\u2588\u2588\u2557\u2588\u2588\u2591\u2588\u2588\u2591\u2588\u2588\u2595       \u2588\u2588\u2595   \u2588\u2588\u2595   \u2588\u2588\u2595   \u2588\u2588\u2595
 \u2588\u2588\u2595 \u255a\u2588\u2588\u2588\u2588\u2591\u2588\u2588\u2591\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595   \u2588\u2588\u2595   \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595
 \u255a\u2588\u2588\u2595  \u255a\u2588\u2588\u2588\u2588\u2595\u255a\u2588\u2588\u2595 \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595   \u255a\u2588\u2588\u2595    \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595\u2570\u2570\u2570\u2588\u2588\u2595
  \u255a\u2588\u2588\u2595  \u255a\u2588\u2588\u2588\u2588\u2595\u255a\u2588\u2588\u2595 \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595   \u255a\u2588\u2588\u2595    \u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2595
    AUTONOMOUS INTELLIGENCE v2.0
    Built by Stephen Wahogo \u00b7 Nairobi, Kenya
    ''',

    "logo_short": "[ NICTO v2.0 ]",
}

def apply_theme_to_rich():
    from rich.theme import Theme
    from rich.console import Console
    theme = Theme({
        "prompt": "bold bright_green",
        "response": "green",
        "code": "bright_green on grey3",
        "tool_call": "bold cyan",
        "system": "dim green",
        "error": "bold red",
        "success": "bold bright_green",
        "heading": "bold underline bright_green",
        "dim": "dim green",
    })
    return Console(theme=theme)

def make_style(name):
    from rich.style import Style
    c = NICTO_THEME["colors"]
    mapping = {
        "bg_primary": Style(bgcolor=c["bg_primary"]),
        "panel": Style(bgcolor=c["bg_panel"], color=c["text_primary"]),
        "card": Style(bgcolor=c["bg_card"], color=c["text_primary"], border_style=c["border_mid"]),
        "accent": Style(color=c["accent_primary"], bold=True),
        "electric": Style(color=c["accent_electric"]),
        "neon": Style(color=c["accent_neon"]),
        "danger": Style(color=c["danger"], bold=True),
        "warning": Style(color=c["warning"]),
        "success": Style(color=c["success"], bold=True),
    }
    return mapping.get(name, Style())
