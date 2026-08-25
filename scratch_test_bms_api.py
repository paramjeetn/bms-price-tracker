import httpx
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
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

with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
    for name, url, params in urls:
        print(f"\n=== {name} ===")
        try:
            r = client.get(url, params=params)
            print(f"Status: {r.status_code}")
            print(f"Content-Type: {r.headers.get('content-type', 'unknown')}")
            try:
                data = r.json()
                print("Valid JSON: True")
            except Exception as e:
                print(f"Valid JSON: False ({e})")
            body = r.text[:3000]
            print(f"Body preview: {body[:500]}")
            # Save to file
            with open(f'discovery_{name}.json', 'w', encoding='utf-8') as f:
                f.write(r.text[:50000])
        except Exception as e:
            print(f"Error: {e}")
