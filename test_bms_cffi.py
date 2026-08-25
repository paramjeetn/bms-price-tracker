from curl_cffi import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://in.bookmyshow.com/",
    "x-bms-id": "IN-BMS",
    "x-region-code": "BHU",
    "x-region-slug": "bhubaneswar"
}

urls = [
    ("1. GETQUICKBOOK", "https://in.bookmyshow.com/serv/getData?cmd=GETQUICKBOOK&code=ET00439318&mtype=MT&qty=1&ibody=&type=MS&lang=en&prefLanguage=&output=json&city=BHU"),
    ("2. movies-by-city", "https://in.bookmyshow.com/api/movies-by-city/BHU"),
    ("3. GETDATEMARKS", "https://in.bookmyshow.com/serv/getData?cmd=GETDATEMARKS&code=ET00439318&type=MS&city=BHU&output=json"),
    ("4. v1/venue/shows", "https://in.bookmyshow.com/api/v1/venue/shows?eventCode=ET00439318&date=20260825&city=BHU"),
    ("5. Showtimes web HTML", "https://in.bookmyshow.com/movies/bhubaneswar/awarapan-2/buytickets/ET00439318/20260825"),
    ("6. GETSHOWTIMESBYEVENT", "https://in.bookmyshow.com/serv/getData?cmd=GETSHOWTIMESBYEVENT&f=json&dc=20260825&vc=BHU&ec=ET00439318"),
]

s = requests.Session(impersonate="chrome124")

for name, url in urls:
    print("=" * 60)
    print(f"TESTING WITH curl_cffi: {name}")
    print(f"URL: {url}")
    try:
        r = s.get(url, headers=headers, timeout=15)
        print(f"Status Code: {r.status_code}")
        print(f"Content-Type: {r.headers.get('content-type', 'N/A')}")
        print(f"Length: {len(r.text)}")
        print("First 2000 chars:")
        print(r.text[:2000])
        try:
            parsed = r.json()
            print("VALID JSON!")
            print(f"JSON Keys: {list(parsed.keys()) if isinstance(parsed, dict) else len(parsed)}")
            with open(f"response_{name.split('.')[0].strip()}.json", "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2)
        except Exception:
            print("NOT JSON")
    except Exception as e:
        print(f"Error: {e}")
    print("=" * 60 + "\n")
