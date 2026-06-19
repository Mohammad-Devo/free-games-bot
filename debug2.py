import requests, re

# صفحه open giveaway رو بگیر و لینک نهایی رو پیدا کن
url = 'https://www.gamerpower.com/open/construction-simulator-3-mobile-giveaway'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# اول بدون redirect
r = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
print(f"Status (no redirect): {r.status_code}")
print(f"Location header: {r.headers.get('location', 'NONE')}")

# بعد با redirect
r2 = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
print(f"\nStatus (with redirect): {r2.status_code}")
print(f"Final URL: {r2.url}")

# HTML رو بررسی کن
html = r2.text[:5000]
print(f"\n--- HTML snippet ---")
print(html[:2000])

# دنبال لینک بگرد
patterns = [
    r'window\.location\s*=\s*["\']([^"\']+)["\']',
    r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
    r'meta[^>]+http-equiv=["\']refresh["\'][^>]+url=([^\s"\']+)',
    r'href=["\']https?://(?!www\.gamerpower)[^"\']+["\']',
]
for p in patterns:
    found = re.findall(p, html, re.IGNORECASE)
    if found:
        print(f"\nPattern '{p[:40]}...' found: {found[:3]}")
