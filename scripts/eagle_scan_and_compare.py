"""Eagle Eye scan and feature comparison, then push to GitHub."""
import json, os, sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "kyros-core", "src"))

from kyros.eagle_eye import EagleEye

# 1. Eagle Eye preemptive scan
print("=" * 60)
print("EAGLE EYE PREEMPTIVE SCAN OF KYROS CODEBASE")
print("=" * 60)

ee = EagleEye()
result = ee.preemptive_scan()
print(f"Files scanned: {result['files_scanned']}")
print(f"Total issues: {result['total_issues']}")
print(f"Critical: {result['critical']}")
print(f"Warnings: {result['warnings']}")
for r in result.get("errors", []):
    print(f"  ERROR: {r.get('filename')}: {r.get('error')}")

# 2. Generate feature comparison
print("\n" + "=" * 60)
print("KYROS FEATURE COMPARISON VS OTHER AI MODELS")
print("=" * 60)

features = {
    "Chat & Conversation": {
        "KYROS": True, "ChatGPT": True, "Claude": True, "Gemini": True, "Grok": True
    },
    "Code Generation": {
        "KYROS": True, "ChatGPT": True, "Claude": True, "Gemini": True, "Copilot": True
    },
    "Local/Offline Operation": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Web Search": {
        "KYROS": True, "ChatGPT": True, "Claude": True, "Gemini": True, "Grok": True
    },
    "Image Generation": {
        "KYROS": True, "ChatGPT": True, "Claude": False, "Gemini": True, "Grok": True
    },
    "Video Generation": {
        "KYROS": True, "ChatGPT": True, "Claude": False, "Gemini": True, "Grok": False
    },
    "Speech/TTS": {
        "KYROS": True, "ChatGPT": True, "Claude": False, "Gemini": True, "Grok": False
    },
    "Desktop Avatar": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Desktop Control (CUA)": {
        "KYROS": True, "ChatGPT": True, "Claude": True, "Gemini": False, "Grok": False
    },
    "Webcam Vision": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": True, "Grok": False
    },
    "6-Brain Ensemble": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "28 Brain Regions": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Self-Improvement": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Self-Repair Engine": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Cybersecurity Arsenal": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Crypto Wallet & Mining": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": True
    },
    "Game Engine (5 games)": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Memory Persistence": {
        "KYROS": True, "ChatGPT": True, "Claude": True, "Gemini": True, "Grok": True
    },
    "No Censorship/Unbounded": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Distributed Mesh Network": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Biomedical Features": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Consciousness Features": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Physics & Reality Features": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Breakthrough Features": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Autopilot Automation": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "365-Day Uptime Resilience": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "True Autonomy (Agent -> System)": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Eagle Eye Truth Detection": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "User Registration & Safety": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Police Cooperation Mode": {
        "KYROS": True, "ChatGPT": False, "Claude": False, "Gemini": False, "Grok": False
    },
    "Privacy Policy (GDPR/CCPA)": {
        "KYROS": True, "ChatGPT": True, "Claude": True, "Gemini": True, "Grok": True
    },
}

print(f"\n{'Feature':<40} {'KYROS':<10} {'ChatGPT':<10} {'Claude':<10} {'Gemini':<10} {'Grok':<10}")
print("-" * 90)
nikto_count = 0
for feature, models in features.items():
    nikto_has = "YES" if models.get("KYROS") else "no"
    chatgpt = "YES" if models.get("ChatGPT") else "no"
    claude = "YES" if models.get("Claude") else "no"
    gemini = "YES" if models.get("Gemini") else "no"
    grok = "YES" if models.get("Grok") else "no"
    if models.get("KYROS"):
        nikto_count += 1
    print(f"{feature:<40} {nikto_has:<10} {chatgpt:<10} {claude:<10} {gemini:<10} {grok:<10}")

print("-" * 90)
print(f"\nTotal Features: {len(features)}")
print(f"KYROS: {nikto_count}/{len(features)} ({100*nikto_count//len(features)}%)")
for model in ["ChatGPT", "Claude", "Gemini", "Grok"]:
    count = sum(1 for f in features.values() if f.get(model))
    print(f"{model}: {count}/{len(features)} ({100*count//len(features)}%)")

# Save as JSON
output = {
    "nikto_features": {
        "total_features": len(features),
        "nikto_wins": nikto_count,
        "nikto_percentage": f"{100*nikto_count//len(features)}%",
    },
    "comparison": {
        model: {
            "features": sum(1 for f in features.values() if f.get(model)),
            "percentage": f"{100*sum(1 for f in features.values() if f.get(model))//len(features)}%"
        }
        for model in ["KYROS", "ChatGPT", "Claude", "Gemini", "Grok"]
    },
    "features": features,
}

Path("feature_comparison.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
print(f"\nComparison saved to feature_comparison.json")
