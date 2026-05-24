"""Check variant health and module structure."""
import os, sys
sys.path.insert(0, "packages/kyros-core/src")

def check_variant(name):
    from kyros.variants.base import create_variant
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

for vname in ["kyros", "kyros-sonnet", "kyros-mythos"]:
    issues, preview = check_variant(vname)
    print(f"  [{vname}] Issues: {issues if issues else 'NONE'}")
    print(f"           Preview: {preview}...")

features = [
    "kyros/autopilot", "kyros/devices", "kyros/game_engine",
    "kyros/evolution", "kyros/dream", "kyros/mesh",
    "kyros/consciousness/expansions", "nikto/bio_medical",
    "nikto/physics", "kyros/language"
]
for f in features:
    p = f"packages/kyros-core/src/{f}"
    if os.path.isdir(p):
        files = [x for x in os.listdir(p) if x.endswith(".py") and "__" not in x]
        print(f"  [{f}] {files}")
    else:
        print(f"  [{f}] MISSING")
