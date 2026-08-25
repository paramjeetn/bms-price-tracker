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
    """Build clean plain-text ntfy payload for an alert."""
    formatted_date = _format_date(slot.date)
    showtime_str = f"{formatted_date} {slot.showtime}".strip()
    
    body = (
        f"{slot.movie}\n"
        f"{slot.cinema}\n"
        f"{showtime_str}\n"
        f"₹{slot.price}"
    )

    return {
        "title": slot.movie,
        "body": body,
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
        headers = {
            "Title": payload["title"],
            "Priority": payload["priority"],
            "Tags": ",".join(payload["tags"]),
        }
        if payload.get("click"):
            headers["Click"] = payload["click"]

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                content=payload["body"],
                headers=headers,
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        print(f"[ntfy] Failed to send notification: {e}")
        return False
