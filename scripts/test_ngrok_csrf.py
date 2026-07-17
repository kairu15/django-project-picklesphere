"""
PickleSphere - Ngrok CSRF Fix Verification Script
Starts Django + ngrok, then tests the tunnel for CSRF errors.
"""
import subprocess
import time
import urllib.request
import json
import os
import sys
import signal

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_DIR)

print("=" * 60)
print("PickleSphere - Ngrok CSRF Fix Verification")
print("=" * 60)

# Kill any lingering ngrok
subprocess.run("taskkill /f /im ngrok.exe 2>nul", shell=True, capture_output=True)
time.sleep(1)

# 1) Start Django
print("\n[1/4] Starting Django dev server...")
django_proc = subprocess.Popen(
    [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
print(f"  PID: {django_proc.pid}")
time.sleep(5)

# Verify Django
try:
    resp = urllib.request.urlopen("http://127.0.0.1:8000/", timeout=5)
    print(f"  Django: OK (status {resp.status})")
    resp.close()
except Exception as e:
    print(f"  FAILED: {e}")
    django_proc.terminate()
    sys.exit(1)

# 2) Start ngrok
print("\n[2/4] Starting ngrok tunnel...")
ngrok_proc = subprocess.Popen(
    ["ngrok", "http", "8000", "--log=stdout"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
print(f"  PID: {ngrok_proc.pid}")
time.sleep(6)

# Get tunnel URL
try:
    resp = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=5)
    data = json.loads(resp.read())
    resp.close()
    tunnels = data.get("tunnels", [])
    if not tunnels:
        print("  FAILED: No tunnels found")
        ngrok_proc.terminate()
        django_proc.terminate()
        sys.exit(1)
    url = tunnels[0]["public_url"]
    print(f"  Ngrok URL: {url}")
except Exception as e:
    print(f"  FAILED: {e}")
    ngrok_proc.terminate()
    django_proc.terminate()
    sys.exit(1)

# 3) TEST GET through ngrok
print("\n[3/4] Testing GET through ngrok tunnel...")

# Test homepage
try:
    req = urllib.request.Request(url + "/")
    resp = urllib.request.urlopen(req, timeout=15)
    print(f"  GET {url}/ -> {resp.status}")
    assert resp.status == 200, f"Expected 200, got {resp.status}"
    print(f"  ✅ Homepage serves correctly (no CSRF error)")
    resp.close()
except Exception as e:
    print(f"  ❌ Homepage failed: {e}")
    ngrok_proc.terminate()
    django_proc.terminate()
    sys.exit(1)

# Test login page (check CSRF token is present)
try:
    req = urllib.request.Request(url + "/accounts/login/")
    resp = urllib.request.urlopen(req, timeout=15)
    body = resp.read().decode("utf-8", errors="replace")
    has_csrf = "csrf" in body.lower()
    print(f"  GET {url}/accounts/login/ -> {resp.status}")
    print(f"  {'✅ CSRF token found' if has_csrf else '⚠️ No CSRF token found'} in login page")
    resp.close()
except Exception as e:
    print(f"  ⚠️ Login page test: {e}")

# Test POST without CSRF token (should get 403)
print("\n[4/4] Testing POST CSRF protection through ngrok...")
try:
    post_data = b"username=test&password=test&csrfmiddlewaretoken=fake"
    req = urllib.request.Request(
        url + "/accounts/login/",
        data=post_data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Origin", url)
    req.add_header("Referer", url + "/accounts/login/")
    resp = urllib.request.urlopen(req, timeout=15)
    print(f"  POST -> {resp.status} (unexpected - CSRF might not be enforced)")
    resp.close()
except urllib.request.HTTPError as e:
    status = e.code
    body = e.read().decode("utf-8", errors="replace")
    if status == 403:
        print(f"  POST -> 403 (expected for missing/incorrect CSRF token)")
        if "origin checking failed" in body.lower() and "ngrok" in body.lower():
            print(f"  ❌ FAIL: CSRF origin checking still failing for ngrok!")
        else:
            print(f"  ✅ CSRF protection is working correctly")
    else:
        print(f"  POST -> {status}")
except Exception as e:
    print(f"  ⚠️ POST test: {e}")

# Summary
print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)

# Cleanup hint
print(f"\nServers are still running:")
print(f"  Django: http://127.0.0.1:8000")
print(f"  Ngrok:  {url}")
print(f"  Dashboard: http://127.0.0.1:4040")
print(f"\nTo stop them, run: taskkill /f /im python.exe & taskkill /f /im ngrok.exe")
