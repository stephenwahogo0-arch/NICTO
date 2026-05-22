"""Test all server endpoints."""
import json
import urllib.request
import sys

BASE = "http://127.0.0.1:8767"

def test(path, method="GET", data=None):
    try:
        if method == "POST":
            req = urllib.request.Request(
                BASE + path,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        else:
            req = urllib.request.Request(BASE + path)
        r = urllib.request.urlopen(req, timeout=10)
        if r.status == 200:
            body = r.read().decode()
            # Try JSON
            try:
                parsed = json.loads(body)
                print(f"OK {method} {path}: {list(parsed.keys())[:3]}")
            except json.JSONDecodeError:
                print(f"OK {method} {path}: {len(body)} chars (not JSON)")
            return True
        else:
            print(f"FAIL {method} {path}: HTTP {r.status}")
            return False
    except Exception as e:
        print(f"FAIL {method} {path}: {e}")
        return False

passed = 0
failed = 0

# Test GET endpoints
for path in ["/health", "/", "/system/info", "/model/status", 
             "/engine/info", "/finance/accounts", "/training/stats"]:
    if test(path):
        passed += 1
    else:
        failed += 1

# Test POST /chat
if test("/chat", "POST", {"message": "hello", "mode": "build"}):
    passed += 1
else:
    failed += 1

# Test POST /finance/account
if test("/finance/account", "POST", {"name": "test", "initial_deposit": 100}):
    passed += 1
else:
    failed += 1

print(f"\n{passed}/{passed+failed} endpoints OK")
sys.exit(0 if failed == 0 else 1)
