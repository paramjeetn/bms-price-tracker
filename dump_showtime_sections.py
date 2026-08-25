import json

with open("bms_initial_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

queries = state.get("showtimesFunctionalApi", {}).get("queries", {})
primary = queries.get("fetchPrimaryDynamic-ET00439318---20260825-BHUB", {}).get("data", {}).get("data", {})

showtimeWidgets = primary.get("showtimeWidgets", [])

for w in showtimeWidgets:
    if w.get("type") == "groupList":
        groups = w.get("data", [])
        for g in groups:
            for venue in g.get("data", []):
                v_name = venue.get("additionalData", {}).get("venueName")
                v_code = venue.get("additionalData", {}).get("venueCode")
                sections = venue.get("showtimesSections", [])
                print("="*60)
                print(f"VENUE: {v_name} ({v_code})")
                print(f"Sections count: {len(sections)}")
                for s_idx, sec in enumerate(sections):
                    print(f"  Section {s_idx} keys:", list(sec.keys()))
                    # print details
                    print(json.dumps(sec, indent=4))
