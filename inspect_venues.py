import json

with open("bms_initial_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

queries = state.get("showtimesFunctionalApi", {}).get("queries", {})
primary = queries.get("fetchPrimaryDynamic-ET00439318---20260825-BHUB", {}).get("data", {})

print("Primary keys:", list(primary.keys()))

# Check __showtimesComputed
print("\n--- __showtimesComputed ---")
st_comp = queries.get("fetchPrimaryDynamic-ET00439318---20260825-BHUB", {}).get("__showtimesComputed", {})
print("Computed keys:", list(st_comp.keys()))

# Let's inspect widgets / sections in primary['data']
pdata = primary.get("data", {})
print("pdata keys:", list(pdata.keys()))

# Look for venue / showtime widgets
for k, v in pdata.items():
    if isinstance(v, list):
        print(f"List '{k}' with {len(v)} items")
        if v:
            print("  First item type:", type(v[0]))
            if isinstance(v[0], dict):
                print("  First item keys:", list(v[0].keys()))
                print("  First item sample:", json.dumps(v[0], indent=2)[:1000])
    elif isinstance(v, dict):
        print(f"Dict '{k}' with {len(v)} keys: {list(v.keys())}")
