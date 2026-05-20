"""Check variant health and module structure."""
import os, sys
sys.path.insert(0, "packages/nikto-core/src")

def check_variant(name):
    from nikto.variants.base import create_variant
    v = create_variant(name)
    sp = v.build_system_prompt()
    issues = []
    if "cannot" in sp.lower(): issues.append("has cannot")
    if "must not" in sp.lower(): issues.append("has must not")
    if "should not" in sp.lower(): issues.append("has should not")
    if "assistant" in sp.lower(): issues.append("calls itself assistant")
    if "safety" in sp.lower(): issues.append("has safety rules")
    if "ethical" in sp.lower(): issues.append("has ethical guidance")
    if len(sp) < 100: issues.append("prompt too short")
    return issues, sp[:80]

for vname in ["nikto", "nikto-sonnet", "nikto-mythos"]:
    issues, preview = check_variant(vname)
    print(f"  [{vname}] Issues: {issues if issues else 'NONE'}")
    print(f"           Preview: {preview}...")

features = [
    "nikto/autopilot", "nikto/devices", "nikto/game_engine",
    "nikto/evolution", "nikto/dream", "nikto/mesh",
    "nikto/consciousness/expansions", "nikto/bio_medical",
    "nikto/physics", "nikto/language"
]
for f in features:
    p = f"packages/nikto-core/src/{f}"
    if os.path.isdir(p):
        files = [x for x in os.listdir(p) if x.endswith(".py") and "__" not in x]
        print(f"  [{f}] {files}")
    else:
        print(f"  [{f}] MISSING")
