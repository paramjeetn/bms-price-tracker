"""Get the full show[0] additionalData and customGestureCTA."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("debug_state.json", encoding="utf-8") as f:
    state = json.load(f)

q = state["showtimesFunctionalApi"]["queries"]["fetchPrimaryDynamic-ET00439318---20260825-BHUB"]
data = q["data"]["data"]
widget1 = data["showtimeWidgets"][1]
group0 = widget1["data"][0]

# INOX Symphony - last venue which had 5 shows
vc = group0["data"][-1]
print("Venue:", vc["additionalData"].get("venueName"))
sections = vc.get("showtimesSections", [])
sec = sections[0]
shows = sec.get("showtimes", [])
s0 = shows[0]

print("\nFull show[0]:")
print(json.dumps(s0, indent=2)[:3000])
