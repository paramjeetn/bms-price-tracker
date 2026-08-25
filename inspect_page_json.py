from curl_cffi import requests
import json
import re
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://in.bookmyshow.com/",
    "x-bms-id": "IN-BMS",
    "x-region-code": "BHU",
    "x-region-slug": "bhubaneswar"
}

url = "https://in.bookmyshow.com/movies/bhubaneswar/awarapan-2/buytickets/ET00439318/20260825"
s = requests.Session(impersonate="chrome124")
r = s.get(url, headers=headers)

print(f"Page Status: {r.status_code}, Length: {len(r.text)}")

# Let's search for script tags or JSON data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
print(f"Found {len(scripts)} scripts")

# Check for JSON-LD, __NEXT_DATA__, window.__INITIAL_STATE__, etc.
for i, script in enumerate(scripts):
    if "__NEXT_DATA__" in script or "window.__INITIAL_STATE__" in script or "showtimes" in script.lower() or "cinemas" in script.lower() or "venue" in script.lower():
        print(f"Script {i} (Length {len(script)}):")
        print(script[:500])
        print("...")

# Check for JSON-LD
json_lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', r.text, re.DOTALL)
print(f"Found {len(json_lds)} JSON-LD blocks")
for j in json_lds:
    try:
        data = json.loads(j)
        print("JSON-LD:", json.dumps(data, indent=2)[:500])
    except Exception:
        pass

# Check if there are any data attributes or API endpoints referenced in scripts
api_matches = re.findall(r'https?://[^"\s\']+(?:api|serv|gateway|showtimes|venue)[^"\s\']+', r.text)
print("API endpoints found in HTML:")
for api in set(api_matches):
    print(" - ", api)
