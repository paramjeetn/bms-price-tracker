"""
Main orchestrator — runs one full fetch-compare-notify-cleanup cycle.

Flow:
  1. Load config
  2. Connect to Turso
  3. For each movie × date: fetch ShowSlots from BMS
  4. Upsert each slot → detect price changes → send ntfy alerts
  5. Delete stale slots (not seen in this fetch)
  6. Print summary
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path

import yaml

from app.bms.client import BMSClient
from app.bms.models import ShowSlot
from app.monitoring.comparator import process_slot
from app.notifications.ntfy import send_notification
from app.storage.turso import get_turso_client

# ── Config ────────────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    # Environment overrides
    cfg["ntfy"]["topic"]   = os.environ.get("NTFY_TOPIC",        cfg["ntfy"]["topic"])
    cfg["ntfy"]["server"]  = os.environ.get("NTFY_SERVER",       cfg["ntfy"]["server"])
    cfg["price_threshold"] = int(os.environ.get("PRICE_THRESHOLD", cfg["price_threshold"]))
    return cfg


def date_range(days_ahead: int) -> list[str]:
    """Return ISO date strings from today through today+days_ahead."""
    today = datetime.now(timezone.utc).date()
    return [(today + timedelta(days=i)).isoformat() for i in range(days_ahead + 1)]


# ── Main ──────────────────────────────────────────────────────────────────────

async def run():
    cfg = load_config()

    threshold        = cfg["price_threshold"]
    days_ahead       = cfg["days_ahead"]
    city_code        = cfg["city_code"]
    ntfy_server      = cfg["ntfy"]["server"]
    ntfy_topic       = cfg["ntfy"]["topic"]
    notify_price_up  = cfg["alerts"].get("notify_price_increase", False)

    fetch_time = datetime.now(timezone.utc).isoformat()

    print(f"\n{'='*60}")
    print(f"  BMS Price Monitor — {fetch_time}")
    print(f"  Threshold: ₹{threshold}  |  Days ahead: {days_ahead}")
    print(f"  ntfy topic: {ntfy_topic}")
    print(f"{'='*60}\n")

    bms = BMSClient(city_code=city_code)

    # Build notify callback
    async def notify(slot: ShowSlot, alert_type: str, price_from: int | None):
        print(f"  🔔 ALERT [{alert_type}] {slot.movie} @ {slot.cinema} "
              f"{slot.showtime} {slot.category} ₹{slot.price}")
        await send_notification(slot, alert_type, price_from, ntfy_server, ntfy_topic)

    # Counters
    total_slots = 0
    counts = {"inserted": 0, "price_drop": 0, "price_up": 0, "unchanged": 0}

    async with get_turso_client() as db:

        # ── Step 1: Discover all movies ───────────────────────────────────
        try:
            movies = await bms.get_all_movies()
        except NotImplementedError:
            print("⚠️  BMS client not implemented yet.")
            print("   Run discover_bms.py first (Milestone 1) to identify the API,")
            print("   then implement app/bms/client.py and app/bms/parser.py.\n")
            return

        print(f"Found {len(movies)} movies.\n")

        # ── Step 2: For each movie × date, fetch and process slots ────────
        for movie in movies:
            for date in date_range(days_ahead):
                print(f"  Scanning: {movie['title']} — {date}")
                try:
                    slots = await bms.get_slots(
                        movie_id=movie["movie_id"],
                        movie_name=movie["title"],
                        date=date,
                        booking_url=movie["booking_url"],
                    )
                except NotImplementedError:
                    print("   ⚠️  Skipping — client not implemented.")
                    break
                except Exception as e:
                    print(f"   ⚠️  Error fetching slots: {e}")
                    continue

                for slot in slots:
                    action = await process_slot(
                        slot=slot,
                        db=db,
                        fetch_time=fetch_time,
                        threshold=threshold,
                        notify=notify,
                        notify_price_up=notify_price_up,
                    )
                    counts[action] += 1
                    total_slots += 1

        # ── Step 3: Cleanup stale slots ────────────────────────────────────
        deleted = await db.delete_stale_slots(fetch_time)

    finally:
        bms.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Cycle complete.")
    print(f"  Total slots processed : {total_slots}")
    print(f"  New slots             : {counts['inserted']}")
    print(f"  Price drops           : {counts['price_drop']}")
    print(f"  Price increases       : {counts['price_up']}")
    print(f"  Unchanged             : {counts['unchanged']}")
    print(f"  Stale slots deleted   : {deleted}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(run())
