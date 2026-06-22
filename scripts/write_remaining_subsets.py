"""Write remaining x and universal Kaggle subsets."""
import json, random
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "kaggle_data"
SRC = Path(__file__).parent.parent / "nicto_neural" / "training_data" / "super_v3_chatml.jsonl"

entries = []
with open(SRC, encoding="utf-8") as f:
    for line in f:
        if line.strip():
            entries.append(json.loads(line))
print(f"Loaded {len(entries)} entries")

# Classify
rd, sc, cd, ag, gn = [], [], [], [], []
rd_kw = {"mathematics", "logic", "physics", "philosophy"}
sc_kw = {"security", "vulnerability", "attack", "threat", "encrypt", "malware", "cyber"}
cd_kw = {"programming", "code", "function", "algorithm", "software", "python", "rust", "javascript"}
ag_kw = {"plan", "research", "coordinate", "orchestrat", "distribut", "multi-agent", "workflow"}

for e in entries:
    c = e["messages"][0]["content"].lower() + " " + e["messages"][1]["content"].lower()
    if any(k in c for k in ag_kw):
        ag.append(e)
    elif any(k in c for k in cd_kw):
        cd.append(e)
    elif any(k in c for k in sc_kw):
        sc.append(e)
    elif any(k in c for k in rd_kw) or "?" in e["messages"][1]["content"]:
        rd.append(e)
    else:
        gn.append(e)
print(f"Classified: rd={len(rd)} sc={len(sc)} cd={len(cd)} ag={len(ag)} gn={len(gn)}")

# Write x
aid = set(id(x) for x in ag + cd)
x_data = ag[:30000] + cd[:30000] + rd[:40000] + [e for e in entries[:50000] if id(e) not in aid]
print(f"x: {len(x_data)} entries", end=" writing... ")
with open(OUT_DIR / "x_chatml.jsonl", "w", encoding="utf-8", buffering=4*1024*1024) as f:
    for e in x_data:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
print(f"{(OUT_DIR / 'x_chatml.jsonl').stat().st_size / 1024 / 1024:.0f}MB")

# Write universal
print(f"universal: {len(entries)} entries", end=" writing... ")
with open(OUT_DIR / "universal_chatml.jsonl", "w", encoding="utf-8", buffering=4*1024*1024) as f:
    for i, e in enumerate(entries):
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
        if (i + 1) % 50000 == 0:
            f.flush()
print(f"{(OUT_DIR / 'universal_chatml.jsonl').stat().st_size / 1024 / 1024:.0f}MB")

print("ALL DONE")
