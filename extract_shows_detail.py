import json

with open("bms_initial_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

queries = state.get("showtimesFunctionalApi", {}).get("queries", {})
primary = queries.get("fetchPrimaryDynamic-ET00439318---20260825-BHUB", {}).get("data", {}).get("data", {})

showtimeWidgets = primary.get("showtimeWidgets", [])

for w in showtimeWidgets:
    if w.get("type") == "groupList":
        groups = w.get("data", [])
        print(f"Number of groups: {len(groups)}")
        for g_idx, group in enumerate(groups):
            venues = group.get("data", [])
            print(f"Group {g_idx} has {len(venues)} venues:")
            for v_idx, v in enumerate(venues):
                venue_data = v.get("additionalData", {})
                venue_name = venue_data.get("venueName")
                venue_code = venue_data.get("venueCode")
                print(f"\n--- Venue #{v_idx+1}: {venue_name} (Code: {venue_code}) ---")
                
                # Check venue children/sections/showtimes
                show_groups = v.get("showGroup", [])
                print(f"Show groups count: {len(show_groups)}")
                for sg in show_groups:
                    print(f"  Format/Category: {sg.get('eventSessionCode')} / {sg.get('eventSessionDescription')} / {sg.get('format')}")
                    shows = sg.get("shows", [])
                    print(f"  Shows count: {len(shows)}")
                    for s in shows:
                        print("   Show:", json.dumps(s, indent=4))
                        
                # Also dump other keys of v
                print("Venue card keys:", [k for k in v.keys() if k != "showGroup"])
