"""Start NIKTO web server and test endpoints."""
import sys, subprocess, time, urllib.request, json

sys.path.insert(0, "packages/nikto-core/src")

# Start server
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "nikto.api.routes:app",
     "--host", "127.0.0.1", "--port", "8765", "--log-level", "warning"],
    cwd="packages/nikto-core/src"
)

time.sleep(4)

try:
    # Test root
    resp = urllib.request.urlopen("http://127.0.0.1:8765/")
    data = json.loads(resp.read())
    print(f"  [OK] Root: {data['status']}")

    # Test health
    resp = urllib.request.urlopen("http://127.0.0.1:8765/health")
    data = json.loads(resp.read())
    print(f"  [OK] Health: agent_ready={data['agent_ready']}")

    # Test chat UI
    resp = urllib.request.urlopen("http://127.0.0.1:8765/chat-ui")
    html = resp.read().decode()
    print(f"  [OK] Chat UI: {len(html)} bytes loaded")

    # Test chat endpoint
    req = urllib.request.Request(
        "http://127.0.0.1:8765/chat",
        data=json.dumps({"message": "hello", "mode": "build"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    print(f"  [OK] Chat response: {len(data['response'])} chars")

    # Test finance endpoints
    resp = urllib.request.urlopen("http://127.0.0.1:8765/finance/accounts")
    data = json.loads(resp.read())
    print(f"  [OK] Finance: {len(data['accounts'])} accounts")

    # Test training stats
    resp = urllib.request.urlopen("http://127.0.0.1:8765/training/stats")
    data = json.loads(resp.read())
    print(f"  [OK] Training: {data.get('total_patterns', 0)} patterns")

    print("\n  ALL ENDPOINTS WORKING")
except Exception as e:
    print(f"\n  ERROR: {e}")
finally:
    proc.terminate()
    proc.wait()
