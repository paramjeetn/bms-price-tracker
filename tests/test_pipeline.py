"""Test Turso connection and run a mini end-to-end pipeline test."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TURSO_URL   = "libsql://bookmyshow-paramjeetnpradhan.aws-ap-south-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODc2MzQxOTcsImlkIjoiMDFhMDM3NGMtMmYwMS03ZGU4LWFiNzctMTQ5ZGIxNjE0YzRlIiwia2lkIjoibXlHdmFSREZXUVlnTjgzejlLNVcxY21YVmlzOE5DRVprbjhwWTAwdnJrNCIsInJpZCI6IjY0ZTViMjk1LTAwODMtNDdjYS04MjU2LTQyM2E4MjRlZGVhOSJ9.hbl2jZDzCUZA2Jw8tWacsKN6V-Bw_QLJKTJjwfgg4Dykv7BWnY-FKfRYue8gPLsMLW2pGGvtLjFEBGLmK0UdBg"

os.environ["TURSO_URL"]   = TURSO_URL
os.environ["TURSO_TOKEN"] = TURSO_TOKEN
os.environ["NTFY_TOPIC"]  = "book_my_show_price_drop_alert_param"

async def test_turso():
    from app.storage.turso import get_turso_client
    print("Connecting to Turso...")
    async with get_turso_client() as db:
        print("  Connected! Schema created.")
        # Check tables exist
        rs = await db._client.execute("SELECT name FROM sqlite_master WHERE type='table'")
        print("  Tables:", [row[0] for row in rs.rows])

async def test_pipeline():
    from app.bms.client import BMSClient
    from app.storage.turso import get_turso_client, ALERT_NEW_CHEAP, ALERT_PRICE_DROP
    from app.monitoring.comparator import process_slot
    from app.monitoring.rules import qualifies_for_alert
    from datetime import datetime, timezone

    print("\nFetching slots for Awarapan 2...")
    client = BMSClient()
    slots = await client.get_slots(
        movie_id="ET00439318",
        movie_name="Awarapan 2",
        date="2026-08-25",
        booking_url="https://in.bookmyshow.com/movies/bhubaneswar/awarapan-2/buytickets/ET00439318/20260825"
    )
    print(f"  Got {len(slots)} slots")

    cheap = [s for s in slots if s.price <= 100 and s.available]
    print(f"  Cheap (<=100, available): {len(cheap)}")

    fetch_time = datetime.now(timezone.utc).isoformat()
    alerts_sent = []

    async def mock_notify(slot, alert_type, price_from):
        alerts_sent.append((alert_type, slot.cinema, slot.showtime, slot.category, slot.price))
        print(f"  [ALERT] {alert_type}: {slot.cinema} | {slot.showtime} | {slot.category} | Rs.{slot.price}")

    print("\nRunning pipeline against Turso (first 5 cheap slots)...")
    async with get_turso_client() as db:
        for slot in cheap[:5]:
            action = await process_slot(
                slot=slot,
                db=db,
                fetch_time=fetch_time,
                threshold=100,
                notify=mock_notify,
            )
            print(f"  action={action} | {slot.cinema} | {slot.category} | Rs.{slot.price}")

        # Check what's in DB
        rs = await db._client.execute("SELECT COUNT(*) FROM prices")
        print(f"\n  Rows in prices table: {rs.rows[0][0]}")
        rs2 = await db._client.execute("SELECT COUNT(*) FROM alerts")
        print(f"  Rows in alerts table: {rs2.rows[0][0]}")

        # Run cleanup
        deleted = await db.delete_stale_slots(fetch_time)
        print(f"  Stale rows cleaned up: {deleted}")

    print(f"\nTotal alerts triggered: {len(alerts_sent)}")

async def main():
    await test_turso()
    await test_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
