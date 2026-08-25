"""
ntfy notification sender.

Docs: https://docs.ntfy.sh/publish/
"""

import httpx
from app.bms.models import ShowSlot
from app.monitoring.rules import ntfy_priority
from app.storage.turso import ALERT_NEW_CHEAP, ALERT_PRICE_DROP, ALERT_PRICE_UP


def _build_message(slot: ShowSlot, alert_type: str, price_from: int | None) -> dict:
    """Build the ntfy payload for a given alert."""

    if alert_type == ALERT_NEW_CHEAP:
        title = f"🎬 New Cheap Show — {slot.movie}"
        body  = (
            f"📍 {slot.cinema}\n"
            f"📅 {slot.date}  🕐 {slot.showtime}"
            + (f" [{slot.format}]" if slot.format else "")
            + f"\n🎟  {slot.category}\n"
            f"💰 ₹{slot.price}"
        )

    elif alert_type == ALERT_PRICE_DROP:
        title = f"📉 Price Drop — {slot.movie}"
        body  = (
            f"📍 {slot.cinema}\n"
            f"📅 {slot.date}  🕐 {slot.showtime}"
            + (f" [{slot.format}]" if slot.format else "")
            + f"\n🎟  {slot.category}\n"
            f"💰 ₹{slot.price}  (was ₹{price_from})"
        )

    else:  # ALERT_PRICE_UP — shouldn't reach here normally
        title = f"📈 Price Up — {slot.movie}"
        body  = f"{slot.cinema} {slot.date} {slot.showtime} — ₹{slot.price} (was ₹{price_from})"

    return {
        "title": title,
        "body":  body,
        "priority": ntfy_priority(slot.price),
        "click": slot.booking_url,
        "tags": ["movie_ticket", "bookmyshow"],
    }


async def send_notification(
    slot: ShowSlot,
    alert_type: str,
    price_from: int | None,
    ntfy_server: str,
    ntfy_topic: str,
) -> bool:
    """
    POST a notification to ntfy. Returns True on success.
    """
    payload = _build_message(slot, alert_type, price_from)
    url = f"{ntfy_server.rstrip('/')}/{ntfy_topic}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                json={
                    "topic":    ntfy_topic,
                    "title":    payload["title"],
                    "message":  payload["body"],
                    "priority": payload["priority"],
                    "click":    payload["click"],
                    "tags":     payload["tags"],
                },
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        print(f"[ntfy] Failed to send notification: {e}")
        return False
