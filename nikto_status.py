"""NICTO — Quick status check for running servers."""
import urllib.request, json, sys

def check(name, url, timeout=5):
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        status = r.status
        body = r.read().decode()
        if name == "API":
            data = json.loads(body)
            return f"OK (brain={data['brain_active']}, models={len(data['available_models'])})"
        return f"HTTP {status}"
    except Exception as e:
        return f"OFFLINE ({e})"

print("=== NICTO Status Check ===")
print(f"  API:      {check('API', 'http://127.0.0.1:5000/health')}")
print(f"  Desktop:  {check('Desktop', 'http://127.0.0.1:5173')}")
print()

api_ok = "OK" in check("API", "http://127.0.0.1:5000/health", 2)
desktop_ok = "HTTP 200" in check("Desktop", "http://127.0.0.1:5173", 2)

if api_ok and desktop_ok:
    print("STATUS: RUNNING")
    print("  API:      http://127.0.0.1:5000")
    print("  Desktop:  http://127.0.0.1:5173")
    print("  Start:    double-click start_nikto.bat")
elif api_ok:
    print("STATUS: API running, Desktop offline")
    print("  Run: start_nikto.bat to launch desktop")
else:
    print("STATUS: OFFLINE")
    print("  Run: start_nikto.bat to launch both servers")
