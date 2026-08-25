import httpx

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://in.bookmyshow.com/",
    "x-bms-id": "IN-BMS",
    "x-region-code": "BHU",
    "x-region-slug": "bhubaneswar"
}

targets = [
    ("1. GETQUICKBOOK", "https://in.bookmyshow.com/serv/getData?cmd=GETQUICKBOOK&code=ET00439318&mtype=MT&qty=1&ibody=&type=MS&lang=en&prefLanguage=&output=json&city=BHU"),
    ("2. movies-by-city", "https://in.bookmyshow.com/api/movies-by-city/BHU"),
    ("3. GETDATEMARKS", "https://in.bookmyshow.com/serv/getData?cmd=GETDATEMARKS&code=ET00439318&type=MS&city=BHU&output=json"),
    ("4. v1/venue/shows", "https://in.bookmyshow.com/api/v1/venue/shows?eventCode=ET00439318&date=20260825&city=BHU"),
]

client = httpx.Client(headers=headers, follow_redirects=True, timeout=15.0)

for name, url in targets:
    print("=" * 60)
    print(f"Testing URL: {name}")
    print(f"Target: {url}")
    try:
        r = client.get(url)
        print(f"Status Code: {r.status_code}")
        print(f"Content-Type: {r.headers.get('content-type', 'N/A')}")
        print(f"Response Body (first 2000 chars):\n{r.text[:2000]}")
        print("=" * 60)
    except Exception as e:
        print(f"Exception: {e}")
