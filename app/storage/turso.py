"""
Turso (libSQL) storage layer.

Handles:
  - Schema creation (idempotent)
  - Upsert of ShowSlots (insert or update last_seen + price)
  - Price comparison (detect drops, increases, new slots)
  - Cleanup of stale slots (not seen in current fetch cycle)
  - Appending to the alerts audit log
"""

import os
from datetime import datetime, timezone
from typing import Optional
import libsql_client

from app.bms.models import ShowSlot

# ── DDL ───────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    fingerprint   TEXT PRIMARY KEY,
    movie         TEXT NOT NULL,
    movie_id      TEXT NOT NULL,
    date          TEXT NOT NULL,
    cinema        TEXT NOT NULL,
    cinema_id     TEXT NOT NULL,
    showtime      TEXT NOT NULL,
    format        TEXT,
    category      TEXT NOT NULL,
    language      TEXT,
    price         INTEGER NOT NULL,
    last_price    INTEGER,
    booking_url   TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint   TEXT NOT NULL,
    movie         TEXT NOT NULL,
    date          TEXT NOT NULL,
    cinema        TEXT NOT NULL,
    showtime      TEXT NOT NULL,
    category      TEXT NOT NULL,
    alert_type    TEXT NOT NULL,
    price_from    INTEGER,
    price_to      INTEGER NOT NULL,
    booking_url   TEXT,
    sent_at       TEXT NOT NULL
);
"""

# ── Alert types ───────────────────────────────────────────────────────────────

ALERT_NEW_CHEAP   = "new_cheap"     # brand-new slot at or below threshold
ALERT_PRICE_DROP  = "price_drop"    # existing slot got cheaper
ALERT_PRICE_UP    = "price_up"      # existing slot got more expensive (logged only)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Client wrapper ────────────────────────────────────────────────────────────

class TursoClient:
    def __init__(self, url: str, token: str):
        self._url   = url
        self._token = token
        self._client: Optional[libsql_client.Client] = None

    async def __aenter__(self):
        self._client = libsql_client.create_client(
            url=self._url,
            auth_token=self._token,
        )
        await self._ensure_schema()
        return self

    async def __aexit__(self, *_):
        if self._client:
            await self._client.close()

    async def _ensure_schema(self):
        """Create tables if they don't exist yet (idempotent)."""
        for statement in SCHEMA.strip().split(";"):
            statement = statement.strip()
            if statement:
                await self._client.execute(statement)

    # ── Core operations ───────────────────────────────────────────────────

    async def get_slot(self, fingerprint: str) -> Optional[dict]:
        """Return the stored row for a fingerprint, or None."""
        rs = await self._client.execute(
            "SELECT * FROM prices WHERE fingerprint = ?",
            [fingerprint],
        )
        if rs.rows:
            row = rs.rows[0]
            return dict(zip(rs.columns, row))
        return None

    async def upsert_slot(self, slot: ShowSlot, fetch_time: str) -> dict:
        """
        Insert or update a ShowSlot row.
        Returns a dict with:
          - 'action': 'inserted' | 'price_drop' | 'price_up' | 'unchanged'
          - 'previous_price': int or None
        """
        existing = await self.get_slot(slot.fingerprint)

        if existing is None:
            # Brand-new slot
            await self._client.execute(
                """
                INSERT INTO prices
                    (fingerprint, movie, movie_id, date, cinema, cinema_id,
                     showtime, format, category, language, price, last_price,
                     booking_url, first_seen, last_seen)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                [
                    slot.fingerprint, slot.movie, slot.movie_id, slot.date,
                    slot.cinema, slot.cinema_id, slot.showtime, slot.format,
                    slot.category, slot.language, slot.price, None,
                    slot.booking_url, fetch_time, fetch_time,
                ],
            )
            return {"action": "inserted", "previous_price": None}

        # Existing slot — update last_seen and price if changed
        prev_price = existing["price"]
        await self._client.execute(
            "UPDATE prices SET last_seen=?, price=?, last_price=? WHERE fingerprint=?",
            [fetch_time, slot.price, prev_price, slot.fingerprint],
        )

        if slot.price < prev_price:
            return {"action": "price_drop", "previous_price": prev_price}
        elif slot.price > prev_price:
            return {"action": "price_up", "previous_price": prev_price}
        else:
            return {"action": "unchanged", "previous_price": prev_price}

    async def delete_stale_slots(self, fetch_start_time: str) -> int:
        """
        Delete all rows whose last_seen is before this fetch cycle started.
        These slots no longer appear on BookMyShow — showtime is gone / sold out.
        Returns the count of deleted rows.
        """
        rs = await self._client.execute(
            "SELECT COUNT(*) FROM prices WHERE last_seen < ?",
            [fetch_start_time],
        )
        count = rs.rows[0][0] if rs.rows else 0

        await self._client.execute(
            "DELETE FROM prices WHERE last_seen < ?",
            [fetch_start_time],
        )
        return count

    async def log_alert(
        self,
        slot: ShowSlot,
        alert_type: str,
        price_from: Optional[int],
        sent_at: str,
    ):
        """Append an entry to the alerts audit log (never deleted)."""
        await self._client.execute(
            """
            INSERT INTO alerts
                (fingerprint, movie, date, cinema, showtime, category,
                 alert_type, price_from, price_to, booking_url, sent_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            [
                slot.fingerprint, slot.movie, slot.date, slot.cinema,
                slot.showtime, slot.category, alert_type,
                price_from, slot.price, slot.booking_url, sent_at,
            ],
        )


def get_turso_client() -> TursoClient:
    """Build TursoClient from environment variables."""
    url   = os.environ.get("TURSO_URL", "")
    token = os.environ.get("TURSO_TOKEN", "")
    if not url or not token:
        raise RuntimeError("TURSO_URL and TURSO_TOKEN environment variables must be set.")
    return TursoClient(url=url, token=token)
