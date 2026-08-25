"""
ntfy notification sender.

Docs: https://docs.ntfy.sh/publish/
"""

import httpx
from app.bms.models import ShowSlot
from app.monitoring.rules import ntfy_priority
from app.storage.turso import ALERT_NEW_CHEAP, ALERT_PRICE_DROP, ALERT_PRICE_UP


def _format_date(date_str: str) -> str:
    """Format YYYY-MM-DD to dd-mm-yyyy."""
    try:
        parts = date_str.split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
    except Exception:
        pass
    return date_str


def _build_message(slot: ShowSlot, alert_type: str, price_from: int | None) -> dict:
    """Build minimal ntfy payload for an alert."""
    formatted_date = _format_date(slot.date)
    title = f"{slot.movie}"
    body = f"{slot.cinema}, {formatted_date}, ₹{slot.price}"

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
