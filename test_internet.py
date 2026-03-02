# test_internet.py
import requests
try:
    r = requests.get("https://www.google.com", timeout=5)
    print("google ->", r.status_code)
except Exception as e:
    print("google error:", repr(e))

try:
    r = requests.get("https://api.postalpincode.in/pincode/110001", timeout=5)
    print("pincode ->", r.status_code, r.text[:200])
except Exception as e:
    print("pincode error:", repr(e))
