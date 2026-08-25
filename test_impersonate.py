from curl_cffi import requests
import json

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "x-region-code": "BHU",
    "x-region-slug": "bhubaneswar",
    "x-platform": "web",
    "x-app-code": "WEB",
    "Referer": "https://in.bookmyshow.com/",
    "Cookie": "RRC=BHU; regionCode=BHU; regionSlug=bhubaneswar;"
}

urls = [
    ("movies_list", "https://in.bookmyshow.com/api/explore/v1/discover/movies", {"regionCode": "BHU"}),
    ("showtimes_api", "https://in.bookmyshow.com/api/v2/events/ET00439318/showtimes", {"regionCode": "BHU", "date": "20260825"}),
    ("quickbook", "https://in.bookmyshow.com/serv/getData", {"cmd": "GETQUICKBOOK", "code": "ET00439318", "mtype": "MT", "qty": "1", "city": "BHU", "output": "json"}),
]

for name, url, params in urls:
    print(f"\n=== {name} (curl_cffi chrome124) ===")
    try:
        r = requests.get(url, params=params, headers=headers, impersonate="chrome124", timeout=15)
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('content-type', 'unknown')}")
        try:
            data = r.json()
            print("Valid JSON: True")
        except Exception as e:
            print(f"Valid JSON: False ({e})")
        print(f"Body preview: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
