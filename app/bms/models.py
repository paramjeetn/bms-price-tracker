from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import hashlib


@dataclass
class ShowSlot:
    """
    A single bookable unit: one movie × one date × one cinema × one showtime × one seat category.
    This is the atomic unit of our price tracking system.
    """
    movie: str
    movie_id: str          # BMS event code, e.g. ET00439318
    date: str              # ISO date: 2026-08-25
    cinema: str
    cinema_id: str
    showtime: str          # e.g. "10:30 AM"
    format: str            # e.g. "2D", "3D", "IMAX"
    category: str          # e.g. "Classic", "Premium", "Gold"
    price: int             # in ₹, integer
    available: bool
    booking_url: str
    language: str = ""
    observed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def fingerprint(self) -> str:
        """
        Deterministic SHA-256 key for this exact slot.
        Stable across fetches — used as primary key in Turso.
        """
        key = f"{self.movie_id}|{self.date}|{self.cinema_id}|{self.showtime}|{self.category}"
        return hashlib.sha256(key.encode()).hexdigest()

    def __repr__(self) -> str:
        return (
            f"ShowSlot({self.movie!r} @ {self.cinema!r} "
            f"{self.date} {self.showtime} [{self.category} ₹{self.price}])"
        )
