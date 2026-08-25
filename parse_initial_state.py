from curl_cffi import requests
import json
import re

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

pos = r.text.find("window.__INITIAL_STATE__ =")
if pos != -1:
    sub = r.text[pos + len("window.__INITIAL_STATE__ ="):].strip()
    decoder = json.JSONDecoder()
    state, end_idx = decoder.raw_decode(sub)
    print("Successfully parsed window.__INITIAL_STATE__!")
    print("Keys in state:", list(state.keys()))
    with open("bms_initial_state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print("Saved JSON to bms_initial_state.json")
    
    # Analyze keys
    for k in state:
        val = state[k]
        if isinstance(val, dict):
            print(f"Key '{k}' (dict, {len(val)} subkeys): {list(val.keys())[:10]}")
        elif isinstance(val, list):
            print(f"Key '{k}' (list, {len(val)} items)")
        else:
            print(f"Key '{k}': {val}")
