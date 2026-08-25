import json

with open("bms_initial_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

print("--- showtimesFunctionalApi queries ---")
st_api = state.get("showtimesFunctionalApi", {})
queries = st_api.get("queries", {})
for qk, qv in queries.items():
    print(f"\nQuery Key: {qk}")
    print(f"Status: {qv.get('status')}")
    data = qv.get("data")
    if data:
        print(f"Data type: {type(data)}")
        if isinstance(data, dict):
            print("Data keys:", list(data.keys()))
            for dk, dv in data.items():
                print(f"  {dk}: {type(dv)} (len={len(dv) if hasattr(dv, '__len__') else 'N/A'})")
        print("\nDATA PREVIEW:")
        print(json.dumps(data, indent=2)[:3000])

print("\n--- showtimesByEvent ---")
sbe = state.get("showtimesByEvent", {})
print(json.dumps(sbe, indent=2)[:2000])
