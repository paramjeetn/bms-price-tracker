"""Send a live test notification to ntfy."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.bms.models import ShowSlot
from app.notifications.ntfy import send_notification
from app.storage.turso import ALERT_NEW_CHEAP

async def main():
    topic = os.environ.get("NTFY_TOPIC", "book_my_show_price_drop_alert_param")
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
    
    sample_slot = ShowSlot(
        movie="Awarapan 2",
        movie_id="ET00439318",
        date="2026-08-25",
        cinema="Maharaja (Christie 4K, DOLBY ATMOS 64 CHANNEL)",
        cinema_id="MPDB",
        showtime="07:25 PM",
        format="2D",
        category="SUPER DELUXE",
        price=99,
        available=True,
        booking_url="https://in.bookmyshow.com/movies/bhubaneswar/awarapan-2/buytickets/ET00439318/20260825",
        language="Hindi"
    )
    
    print(f"Sending test notification to {server}/{topic}...")
    success = await send_notification(
        slot=sample_slot,
        alert_type=ALERT_NEW_CHEAP,
        price_from=None,
        ntfy_server=server,
        ntfy_topic=topic
    )
    if success:
        print("[SUCCESS] Test notification sent to ntfy! Check your phone/browser on topic:", topic)
    else:
        print("[FAILED] Could not send test notification.")

if __name__ == "__main__":
    asyncio.run(main())
