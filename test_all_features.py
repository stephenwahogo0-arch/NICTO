"""NIKTO Complete Feature Test Suite"""
import sys, os, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'nikto-core', 'src'))

os.environ['NIKTO_TEST'] = '1'

# Import everything first (outside try/except so variables are accessible)
print("Importing NIKTO modules...")
from nikto.api.routes import app
print("  [OK] FastAPI app")
from nikto.sensors.gesture import WiFiGestureMonitor, SignalProcessor, WiFiCapture
sp = SignalProcessor()
print("  [OK] Gesture module")
from nikto.quantum.engine import IBMQuantumEngine
qe = IBMQuantumEngine()
print(f"  [OK] Quantum engine (connected={qe.connected})")
from nikto.language.detector import LanguageDetector, LANGUAGES
ld = LanguageDetector()
print(f"  [OK] LanguageDetector ({len(LANGUAGES)} langs)")
from nikto.finance import BankManager
bm = BankManager()
print("  [OK] BankManager")
from nikto.model_manager import ModelManager
mm = ModelManager()
hw = mm.detect_hardware_tier()
print(f"  [OK] ModelManager (hw_tier={hw})")

passed = 0
failed = 0
errors = []

def test(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}" + (f" — {detail}" if detail else ""))
    else:
        failed += 1
        errors.append(f"{name}: {detail}")
        print(f"  [FAIL] {name} — {detail}")

print("\n" + "=" * 60)
print("  NIKTO COMPLETE FEATURE TEST")
print("=" * 60)

# ── Module Checks ───────────────────────────────────────
print("\n1. Module Validation")
test("FastAPI app import", True)
test("SignalProcessor scipy", sp.scipy_available)
test("C++ binary available", WiFiCapture.cpp_available())
r = ld.detect("Hello world")
test("LanguageDetector detect", r is not None, f"detected={r.lang if r else 'none'}")
test("ModelManager hw_tier", hw in ("tier1","tier2","tier3"), f"tier={hw}")

# ── Go CLI executables ──────────────────────────────────
print("\n2. Go CLI Executables")
root = os.path.dirname(__file__)
go_tools = [
    ("scanner", "packages/nikto-super-kernel/go/scanner/scanner.exe"),
    ("odds", "packages/nikto-super-kernel/go/odds/odds.exe"),
    ("monitor", "packages/nikto-super-kernel/go/background_monitor/monitor.exe"),
    ("hsync", "packages/nikto-super-kernel/go/hsync_engine/hsync.exe"),
    ("graph", "packages/nikto-super-kernel/go/graph_core/graph.exe"),
]
for name, path in go_tools:
    test(f"Go {name}.exe", os.path.exists(os.path.join(root, path)))

# ── C++ Binary ──────────────────────────────────────────
print("\n3. C++ Wi-Fi Capture")
cpp_path = os.path.join(root, "packages/nikto-core/src/nikto/sensors/cpp/wifi_capture.exe")
test("C++ wifi_capture.exe", os.path.exists(cpp_path))

# ── Start API Server ────────────────────────────────────
print("\n4. Starting API Server...")
import uvicorn
server_thread = threading.Thread(
    target=lambda: uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error"),
    daemon=True
)
server_thread.start()
time.sleep(4)

# ── API Endpoint Tests ──────────────────────────────────
print("5. API Endpoint Tests\n")
import httpx
try:
    c = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15)

    # Root
    r = c.get("/")
    test("GET /", r.status_code == 200 and "NIKTO" in r.text)

    # Health
    r = c.get("/health")
    test("GET /health", r.status_code == 200 and r.json().get("status") == "ok")

    # System info
    r = c.get("/system/info")
    test("GET /system/info", r.status_code == 200 and "cpu_percent" in r.json())

    # Chat English
    r = c.post("/chat", json={"message": "Hello, what can you do?", "language": "auto"}, timeout=30)
    resp = r.json().get("response", "")
    lang = r.json().get("language", "")
    test("POST /chat (EN)", r.status_code == 200 and len(resp) > 20, f"lang={lang}")

    # Chat French (language detection)
    r = c.post("/chat", json={"message": "Bonjour, comment allez-vous?", "language": "auto"}, timeout=30)
    detected = r.json().get("language", "")
    test("POST /chat (FR detect)", "fr" in detected.lower(), f"detected={detected}")

    # Chat Spanish
    r = c.post("/chat", json={"message": "Hola, como estas?", "language": "auto"}, timeout=30)
    detected = r.json().get("language", "")
    test("POST /chat (ES detect)", "es" in detected.lower(), f"detected={detected}")

    # Memory
    r = c.get("/memory/search?q=nikto")
    test("GET /memory/search", r.status_code == 200)

    # Model status
    r = c.get("/model/status")
    test("GET /model/status", r.status_code == 200, f"tier={r.json().get('hw_tier')}")

    # Finance accounts
    r = c.get("/finance/accounts")
    test("GET /finance/accounts", r.status_code == 200)

    # Finance create
    r = c.post("/finance/account", json={"name": "TestAcct", "initial_deposit": 1000})
    test("POST /finance/account", r.status_code == 200 and r.json().get("success"))

    # Finance transfer
    accts = c.get("/finance/accounts").json().get("accounts", [])
    if len(accts) >= 2:
        r = c.post("/finance/transfer", json={"from_id": accts[0]["id"], "to_id": accts[1]["id"], "amount": 50})
        test("POST /finance/transfer", r.status_code == 200)
    else:
        # Create second account
        c.post("/finance/account", json={"name": "Spending", "initial_deposit": 500})
        accts = c.get("/finance/accounts").json().get("accounts", [])
        if len(accts) >= 2:
            r = c.post("/finance/transfer", json={"from_id": accts[0]["id"], "to_id": accts[1]["id"], "amount": 50})
            test("POST /finance/transfer", r.status_code == 200)
        else:
            test("POST /finance/transfer", False, "need 2 accounts")

    # Risk check
    r = c.get("/finance/risk")
    test("GET /finance/risk", r.status_code == 200)

    # Game status
    r = c.get("/game/status")
    test("GET /game/status", r.status_code == 200)

    # Game physics
    r = c.get("/game/physics")
    test("GET /game/physics", r.status_code == 200)

    # Game audio
    r = c.get("/game/audio")
    test("GET /game/audio", r.status_code == 200)

    # Game VFX
    r = c.get("/game/vfx")
    test("GET /game/vfx", r.status_code == 200)

    # Game animation
    r = c.get("/game/animation")
    test("GET /game/animation", r.status_code == 200)

    # Game AI
    r = c.get("/game/ai")
    test("GET /game/ai", r.status_code == 200)

    # Game templates
    r = c.get("/game/templates")
    test("GET /game/templates", r.status_code == 200)

    # Training stats
    r = c.get("/training/stats")
    test("GET /training/stats", r.status_code == 200)

    # Evolution status
    r = c.get("/evolution/status")
    test("GET /evolution/status", r.status_code == 200)

    # Voice profiles
    r = c.get("/voice/profiles")
    test("GET /voice/profiles", r.status_code == 200)

    # Sources summary
    r = c.get("/sources/summary")
    test("GET /sources/summary", r.status_code == 200)

    # Engine info
    r = c.get("/engine/info")
    test("GET /engine/info", r.status_code == 200)

    # Quantum status
    r = c.get("/quantum/status")
    test("GET /quantum/status", r.status_code == 200)

    # Quantum backends
    r = c.get("/quantum/backends")
    test("GET /quantum/backends", r.status_code == 200)

    # Quantum run bell
    r = c.post("/quantum/run", json={"circuit_type": "bell", "num_qubits": 2, "shots": 1024}, timeout=30)
    test("POST /quantum/run bell", r.status_code == 200)

    # Quantum run ghz
    r = c.post("/quantum/run", json={"circuit_type": "ghz", "num_qubits": 4, "shots": 2048}, timeout=30)
    test("POST /quantum/run ghz", r.status_code == 200)

    # Quantum run qft
    r = c.post("/quantum/run", json={"circuit_type": "qft", "num_qubits": 3, "shots": 4096}, timeout=30)
    test("POST /quantum/run qft", r.status_code == 200)

    # Quantum run random
    r = c.post("/quantum/run", json={"circuit_type": "random", "num_qubits": 5, "depth": 10, "shots": 5000}, timeout=30)
    test("POST /quantum/run random", r.status_code == 200)

    # Gesture status
    r = c.get("/gesture/status")
    test("GET /gesture/status", r.status_code == 200)

    # Gesture sample
    r = c.get("/gesture/sample")
    test("GET /gesture/sample", r.status_code == 200)

    # Gesture simulate walking
    r = c.post("/gesture/simulate", json={"activity": "walking", "duration": 3}, timeout=30)
    test("POST /gesture/simulate walking", r.status_code == 200 and r.json().get("samples", 0) > 0, f"samples={r.json().get('samples')}")

    # Gesture simulate running
    r = c.post("/gesture/simulate", json={"activity": "running", "duration": 3}, timeout=30)
    test("POST /gesture/simulate running", r.status_code == 200 and r.json().get("samples", 0) > 0)

    # Gesture simulate sleeping
    r = c.post("/gesture/simulate", json={"activity": "sleeping", "duration": 5}, timeout=30)
    test("POST /gesture/simulate sleeping", r.status_code == 200 and r.json().get("samples", 0) > 0)

    # Gesture simulate fall
    r = c.post("/gesture/simulate/fall", timeout=15)
    test("POST /gesture/simulate fall", r.status_code == 200)

    # Web UI HTML page
    r = c.get("/chat-ui")
    test("GET /chat-ui (HTML)", r.status_code == 200)

except Exception as e:
    import traceback
    traceback.print_exc()
    test("API test suite", False, str(e))

# ── Summary ─────────────────────────────────────────────
print()
print("=" * 60)
total = passed + failed
print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
if errors:
    print("  Failures:")
    for e in errors:
        print(f"    - {e}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
