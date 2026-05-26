"""Rename NIKTO to Kyros AI — comprehensive find-and-replace."""
import os
import re

ROOT = r"C:\Users\BYU\Desktop\NIKTO"
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".opencode"}
SKIP_FILES = {"smoke_test.py", "test_all_features.py", "rename_to_kyros.py", "AGENTS.md", "README.md"}

EXTENSIONS = {".py", ".toml", ".md", ".yml", ".yaml", ".cfg", ".ini", ".txt", ".json", ".html", ".css", ".js", ".ts", ".tsx", ".sh", "Dockerfile", "Dockerfile.*"}

REPLACEMENTS = [
    # Project name (case-sensitive exact matches)
    ("nikto-core", "kyros-core"),
    ("nikto-cli", "kyros-cli"),
    ("nikto_core", "kyros_core"),
    ("nikto_cli", "kyros_cli"),
    ("nikto/settings", "kyros/settings"),
    ("nikto/config", "kyros/config"),
    ("nikto/providers", "kyros/providers"),
    ("nikto/memory", "kyros/memory"),
    ("nikto/tools", "kyros/tools"),
    ("nikto/agent", "kyros/agent"),
    ("nikto/orchestrator", "kyros/orchestrator"),
    ("nikto/variants", "kyros/variants"),
    ("nikto/cua", "kyros/cua"),
    ("nikto/mcp", "kyros/mcp"),
    ("nikto/security", "kyros/security"),
    ("nikto/autopilot", "kyros/autopilot"),
    ("nikto/devices", "kyros/devices"),
    ("nikto/game_engine", "kyros/game_engine"),
    ("nikto/evolution", "kyros/evolution"),
    ("nikto/dream", "kyros/dream"),
    ("nikto/mesh", "kyros/mesh"),
    ("nikto/earn", "kyros/earn"),
    ("nikto/skills", "kyros/skills"),
    ("nikto/advanced_evolution", "kyros/advanced_evolution"),
    ("nikto/daemon", "kyros/daemon"),
    ("nikto/api", "kyros/api"),
    ("nikto/consciousness", "kyros/consciousness"),
    ("nikto/sensors", "kyros/sensors"),
    ("nikto/quantum", "kyros/quantum"),
    ("nikto/language", "kyros/language"),
    ("nikto/brain", "kyros/brain"),
    ("nikto/thinking", "kyros/thinking"),
    ("nikto/sandbox", "kyros/sandbox"),
    ("nikto/sourcing", "kyros/sourcing"),
    ("nikto/voice", "kyros/voice"),
    ("nikto/reasoning", "kyros/reasoning"),
    ("nikto/surpass", "kyros/surpass"),
    ("nikto/synthetic", "kyros/synthetic"),
    ("nikto/resilience", "kyros/resilience"),
    ("nikto/training", "kyros/training"),
    ("nikto/super", "kyros/super"),
    ("nikto/safety", "kyros/safety"),
    ("nikto/registration", "kyros/registration"),
    ("nikto/privacy", "kyros/privacy"),
    ("nikto/infinite_context", "kyros/infinite_context"),
    ("nikto/self_repair", "kyros/self_repair"),
    ("nikto/games", "kyros/games"),
    ("nikto/finance", "kyros/finance"),
    ("nikto/terminal", "kyros/terminal"),
    ("nikto/webui", "kyros/webui"),
    ("nikto/deploy", "kyros/deploy"),
    ("NIKTO", "KYROS"),
    ("Nikto API", "Kyros API"),
    ("NiktoConfig", "KyrosConfig"),
    ("NiktoDaemon", "KyrosDaemon"),
    ("NiktoHeavyweight", "KyrosHeavyweight"),
    ("NiktoSonnet", "KyrosSonnet"),
    ("NiktoMythos", "KyrosMythos"),
    ("NiktoReadOwnTool", "KyrosReadOwnTool"),
    ("NiktoWriteOwnTool", "KyrosWriteOwnTool"),
    ("NiktoSelfReviewTool", "KyrosSelfReviewTool"),
    ("NiktoWebScanTool", "KyrosWebScanTool"),
    ("nikto_scan", "kyros_scan"),
    ("nikto_read_own", "kyros_read_own"),
    ("nikto_write_own", "kyros_write_own"),
    ("nikto_self_review", "kyros_self_review"),
    ("nikto_nikto", "kyros_kyros"),
    ("nikto-denu", "kyros-denu"),
    ("nikto-plus", "kyros-plus"),
    ("nikto-heavyweight", "kyros-heavyweight"),
    ("nikto-sonnet", "kyros-sonnet"),
    ("nikto-mythos", "kyros-mythos"),
    ("nikto-block", "kyros-block"),
    ("nikto_image_", "kyros_image_"),
    ("nikto_pattern_", "kyros_pattern_"),
    ("nikto_gif_", "kyros_gif_"),
    ("nikto_video_", "kyros_video_"),
    ("nikto_web_scan", "kyros_web_scan"),
    ("'kyros'", "'kyros'"),
    ('"kyros"', '"kyros"'),
    # Package/module names in import strings
    (" from kyros.", " from kyros."),
    ("import kyros.", "import kyros."),
    ("import kyros\n", "import kyros\n"),
    ("import kyros;", "import kyros;"),
    ("`nikto`", "`kyros`"),
    # CLI entry point
    ("nikto = \"nikto_cli.main:cli\"", "kyros = \"kyros_cli.main:cli\""),
    # Docker
    ("nikto_data", "kyros_data"),
    # URLs (skip GitHub repo URLs - keep NICTO)
]

def should_process(filepath):
    name = os.path.basename(filepath)
    if name in SKIP_FILES:
        return False
    ext = os.path.splitext(name)[1].lower()
    if ext in EXTENSIONS or name.startswith("Dockerfile"):
        return True
    return False

total_files = 0
total_replacements = 0

for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for fname in files:
        fpath = os.path.join(root, fname)
        if not should_process(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            try:
                with open(fpath, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception:
                continue
        
        new_content = content
        count = 0
        for old, new in REPLACEMENTS:
            if old in new_content:
                new_content = new_content.replace(old, new)
                count += 1
        
        if count > 0:
            # Skip binary files
            if "\0" in new_content:
                continue
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)
            total_files += 1
            total_replacements += count
            print(f"  {fname}: {count} replacements")

print(f"\n=== Done: {total_files} files, {total_replacements} total replacements ===")
