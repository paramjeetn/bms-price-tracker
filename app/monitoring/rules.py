"""
Price rules — decides whether a ShowSlot qualifies for an alert
and what priority level to assign to the ntfy notification.
"""

from app.bms.models import ShowSlot


def qualifies_for_alert(slot: ShowSlot, threshold: int) -> bool:
    """Return True if this slot's price is at or below the threshold."""
    return slot.price <= threshold and slot.available


def ntfy_priority(price: int) -> str:
    """
    Map price to ntfy notification priority.
    https://docs.ntfy.sh/publish/#message-priority
    """
    if price <= 50:
        return "max"      # urgent — vibrates repeatedly
    elif price <= 75:
        return "high"
    elif price <= 100:
        return "default"
    else:
        return "low"
