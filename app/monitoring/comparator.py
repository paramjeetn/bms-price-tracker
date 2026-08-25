"""
Price comparator — orchestrates the upsert + alert decision for each ShowSlot.

For each slot fetched from BMS:
  - 'inserted' + qualifies → alert ALERT_NEW_CHEAP
  - 'price_drop' + qualifies → alert ALERT_PRICE_DROP
  - 'price_up' → log ALERT_PRICE_UP (no phone notification by default)
  - 'unchanged' → nothing
"""

from datetime import datetime, timezone
from typing import Callable, Awaitable

from app.bms.models import ShowSlot
from app.storage.turso import TursoClient, ALERT_NEW_CHEAP, ALERT_PRICE_DROP, ALERT_PRICE_UP
from app.monitoring.rules import qualifies_for_alert


# Type alias for the notification callback
NotifyFn = Callable[[ShowSlot, str, int | None], Awaitable[None]]


async def process_slot(
    slot: ShowSlot,
    db: TursoClient,
    fetch_time: str,
    threshold: int,
    notify: NotifyFn,
    notify_price_up: bool = False,
) -> str:
    """
    Process a single ShowSlot through the full compare-and-alert pipeline.
    Returns the action taken: 'inserted', 'price_drop', 'price_up', 'unchanged'.
    """
    result = await db.upsert_slot(slot, fetch_time)
    action = result["action"]
    prev_price = result["previous_price"]

    # Only alert if price is under threshold
    if qualifies_for_alert(slot, threshold):
        # Deduplicate: check if this hashed slot was already notified previously
        already_notified = await db.has_been_notified(slot.fingerprint)
        if not already_notified:
            await notify(slot, ALERT_NEW_CHEAP, prev_price)
            await db.log_alert(slot, ALERT_NEW_CHEAP, prev_price, fetch_time)

    return action
