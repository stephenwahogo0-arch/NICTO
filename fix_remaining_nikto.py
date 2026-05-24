"""Fix remaining nikto references in all .py files."""
import os, re

ROOT = r"C:\Users\BYU\Desktop\NIKTO"
SKIP_DIRS = {"__pycache__", ".git", ".opencode", "node_modules"}

for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if not f.endswith(".py"):
            continue
        fp = os.path.join(root, f)
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception:
            continue
        
        new = content
        new = re.sub(r"\bfrom nikto\.", "from kyros.", new)
        new = re.sub(r"\bimport nikto\.", "import kyros.", new)
        new = re.sub(r"\bimport nikto\b(?![-_])", "import kyros", new)
        new = re.sub(r"\'nikto\'", "'kyros'", new)
        new = re.sub(r"\"nikto\"", '"kyros"', new)
        
        if new != content:
            with open(fp, "w", encoding="utf-8") as fh:
                fh.write(new)
            print(f"  Fixed: {os.path.relpath(fp, ROOT)}")

print("Done")
