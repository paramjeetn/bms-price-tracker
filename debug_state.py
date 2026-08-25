"""Inspect the raw __INITIAL_STATE__ from BMS to find the correct key path."""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from curl_cffi import requests as cffi_requests

url = "https://in.bookmyshow.com/movies/bhubaneswar/awarapan-2/buytickets/ET00439318/20260825"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://in.bookmyshow.com/",
}

print("Fetching page...")
resp = cffi_requests.get(url, headers=headers, impersonate="chrome124", timeout=20)
print(f"Status: {resp.status_code}  |  Length: {len(resp.text)}")

html = resp.text

# Save full HTML for inspection
with open("debug_page.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved full HTML to debug_page.html")

# Look for __INITIAL_STATE__
pos = html.find("window.__INITIAL_STATE__")
print(f"\nwindow.__INITIAL_STATE__ found at pos: {pos}")

if pos != -1:
    # Show 200 chars around it
    print("Context:", html[pos:pos+200])
    sub = html[pos + len("window.__INITIAL_STATE__ ="):].strip()
    try:
        state, _ = json.JSONDecoder().raw_decode(sub)
        print("\nTop-level keys:", list(state.keys())[:20])
        # Save state
        with open("debug_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print("Saved state to debug_state.json")

        # Check showtimesFunctionalApi
        stf = state.get("showtimesFunctionalApi", {})
        print("\nshowtimesFunctionalApi keys:", list(stf.keys()))
        queries = stf.get("queries", {})
        print("Query keys:", list(queries.keys())[:10])
        for k in list(queries.keys())[:5]:
            print(f"  Key: {k}")
            v = queries[k]
            if isinstance(v, dict):
                print(f"    data keys: {list(v.get('data', {}).keys())[:10] if isinstance(v.get('data'), dict) else type(v.get('data'))}")
    except Exception as e:
        print(f"Parse error: {e}")
        print("Raw sub preview:", sub[:300])
else:
    print("NOT FOUND. Searching for alternatives...")
    for kw in ["__NEXT_DATA__", "INITIAL_STATE", "initialState", "reduxStore"]:
        idx = html.find(kw)
        print(f"  '{kw}' at: {idx}")
    print("\nHTML preview (first 1000 chars):")
    print(html[:1000])
