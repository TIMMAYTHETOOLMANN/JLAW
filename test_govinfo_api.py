"""
Direct GovInfo API Test
Tests actual API connectivity and diagnoses issues
"""

import requests
import os
from datetime import datetime

# Get API key
api_key = os.getenv("GOVINFO_API_KEY", "QLSbdMWeb3QadP66hRAhw3V027uRU9fSYWPistqD")

print("=" * 80)
print("GOVINFO API CONNECTIVITY TEST")
print("=" * 80)
print(f"Time: {datetime.now().isoformat()}")
print(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else f"API Key: {api_key}")
print()

# Test 1: Collections endpoint (simple test)
print("[TEST 1] Testing Collections Endpoint...")
try:
    url = f"https://api.govinfo.gov/collections?api_key={api_key}"
    response = requests.get(url, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("[SUCCESS] Collections endpoint working")
        data = response.json()
        print(f"Collections available: {len(data.get('collections', []))}")
    elif response.status_code == 403:
        print("[FAIL] 403 Forbidden - API key may be invalid or expired")
        print("Get new key: https://api.data.gov/signup/")
    elif response.status_code == 429:
        print("[FAIL] 429 Rate Limited - Too many requests")
        print("Limit: 1000 requests/hour per key")
    elif response.status_code == 500:
        print("[FAIL] 500 Server Error - GovInfo API having issues")
        print("This is a server-side problem, not your code")
    else:
        print(f"[FAIL] Unexpected status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except requests.exceptions.Timeout:
    print("[FAIL] Timeout - API not responding")
except requests.exceptions.ConnectionError:
    print("[FAIL] Connection Error - Cannot reach api.govinfo.gov")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")

print()

# Test 2: Specific USC statute
print("[TEST 2] Testing USC Statute Retrieval (15 USC 78j)...")
try:
    # Try 2024 (most recent complete year)
    year = 2024
    package_id = f"USCODE-{year}-title15"
    granule_id = f"USCODE-{year}-title15-section78j"
    
    url = f"https://api.govinfo.gov/packages/{package_id}/granules/{granule_id}?api_key={api_key}"
    print(f"URL: {url[:80]}...")
    
    response = requests.get(url, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("[SUCCESS] USC statute retrieval working")
        data = response.json()
        print(f"Title: {data.get('title', 'N/A')}")
        print(f"Download links available: {bool(data.get('download'))}")
    elif response.status_code == 404:
        print("[INFO] 404 Not Found - Granule may not exist")
        print(f"Tried: {package_id} / {granule_id}")
        print("Note: GovInfo granule IDs can be tricky - this is normal")
    elif response.status_code == 500:
        print("[FAIL] 500 Server Error - GovInfo API having issues")
    else:
        print(f"[FAIL] Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")

print()

# Test 3: CFR Link Service
print("[TEST 3] Testing CFR Link Service (17 CFR 240.10b-5)...")
try:
    url = "https://www.govinfo.gov/link/cfr/17/240.10b-5"
    response = requests.head(url, allow_redirects=True, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("[SUCCESS] CFR link service working")
        print(f"Final URL: {response.url[:80]}...")
    else:
        print(f"[INFO] Status: {response.status_code}")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")

print()
print("=" * 80)
print("DIAGNOSIS")
print("=" * 80)

# Provide diagnosis
print()
print("Common Issues:")
print("  1. 403 Forbidden = Invalid/expired API key")
print("     Solution: Get new key from https://api.data.gov/signup/")
print()
print("  2. 429 Rate Limited = Too many requests")
print("     Solution: Wait an hour or get additional keys")
print()
print("  3. 500 Server Error = GovInfo API down (TEMPORARY)")
print("     Solution: Wait and retry - this is on their end")
print()
print("  4. 404 Not Found = Granule ID incorrect (NORMAL for some statutes)")
print("     Solution: Use alternative endpoints or link service")
print()
print("  5. Timeout/Connection Error = Network issue")
print("     Solution: Check firewall, proxy, internet connection")
print()
print("=" * 80)

