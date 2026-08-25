import httpx

# Test various endpoints, mobile app endpoints, gateway endpoints, etc.
endpoints = [
    # Mobile app endpoints / API endpoints
    ("BMS Gateway Showtimes", "https://in.bookmyshow.com/api/explore/v1/discover/regions/BHU/movies/ET00439318"),
    ("BMS Mobile API", "https://in.bookmyshow.com/mobile/synopsis?cmd=GETEVENTSYNOPSIS&eventcode=ET00439318&f=json"),
    ("BMS API Gateway Showtimes V1", "https://in.bookmyshow.com/api/v1/movies/bhubaneswar/ET00439318"),
    ("BMS Quickbook GET", "https://in.bookmyshow.com/serv/getData?cmd=GETQUICKBOOK&code=ET00439318&city=BHU&type=MS&output=json"),
]

# Let's test with mobile app user agent
mobile_headers = {
    "User-Agent": "BookMyShow/14.0.0 (Android 14; Pixel 7)",
    "Accept": "application/json",
    "x-bms-id": "IN-BMS",
    "x-region-code": "BHU"
}

with httpx.Client(headers=mobile_headers, follow_redirects=True, timeout=10.0) as client:
    for name, url in endpoints:
        try:
            r = client.get(url)
            print(f"[Mobile UA] {name} -> Status: {r.status_code}, Length: {len(r.text)}")
            if r.status_code == 200:
                print(r.text[:500])
        except Exception as e:
            print(f"[Mobile UA] {name} -> Error: {e}")
