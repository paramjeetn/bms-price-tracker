import httpx
import json
import traceback

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
    ("7. quickbook (no city)", "https://in.bookmyshow.com/serv/getData?cmd=GETQUICKBOOK&code=ET00439318&type=MS&output=json"),
    ("8. quickbook alt", "https://in.bookmyshow.com/serv/getData?cmd=QUICKBOOK&f=json&rc=BHU&dc=20260825&ec=ET00439318")
]

client = httpx.Client(headers=headers, follow_redirects=True, timeout=15.0)

for name, url in urls:
    print(f"==================================================")
    print(f"TEST: {name}")
    print(f"URL: {url}")
    try:
        resp = client.get(url)
        print(f"Status Code: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type', '')}")
        text = resp.text
        print(f"Body length: {len(text)}")
        print("First 2000 chars of body:")
        print(text[:2000])
        try:
            data = resp.json()
            print("Successfully parsed as JSON!")
            print(f"Top-level keys / type: {type(data)} -> {list(data.keys()) if isinstance(data, dict) else len(data)}")
        except Exception:
            print("Response is NOT valid JSON.")
    except Exception as e:
        print(f"Request failed: {e}")
    print(f"==================================================\n")
