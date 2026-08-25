import json

with open("bms_initial_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

queries = state.get("showtimesFunctionalApi", {}).get("queries", {})
primary = queries.get("fetchPrimaryDynamic-ET00439318---20260825-BHUB", {}).get("data", {}).get("data", {})

showtimeWidgets = primary.get("showtimeWidgets", [])
print(f"showtimeWidgets count: {len(showtimeWidgets)}")

for idx, w in enumerate(showtimeWidgets):
    print(f"\n--- Widget {idx} Type: {w.get('type')} ---")
    data = w.get("data", [])
    print(f"Data count: {len(data) if isinstance(data, list) else type(data)}")
    print(json.dumps(w, indent=2)[:2500])
