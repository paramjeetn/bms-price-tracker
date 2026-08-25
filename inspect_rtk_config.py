import json

with open("bms_initial_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

st_api = state.get("showtimesFunctionalApi", {})
print("showtimesFunctionalApi keys:", list(st_api.keys()))
print("Config:", json.dumps(st_api.get("config"), indent=2))
print("Mutations:", json.dumps(st_api.get("mutations"), indent=2))
print("Provided:", json.dumps(st_api.get("provided"), indent=2))
print("Subscriptions:", json.dumps(st_api.get("subscriptions"), indent=2))
