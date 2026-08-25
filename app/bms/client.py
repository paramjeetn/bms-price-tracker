"""
BookMyShow API client.

STATUS: Placeholder — will be implemented after Milestone 1 (discover_bms.py)
reveals which API endpoints BookMyShow uses internally.

The interface is fixed:
    client = BMSClient(config)
    slots = await client.get_slots(movie_id, date, city_code)

Returns a list of ShowSlot objects.
"""

from __future__ import annotations
import httpx
from typing import Any
from app.bms.models import ShowSlot
from app.bms.parser import parse_slots


class BMSClient:
    """
    HTTP client for BookMyShow.

    After running discover_bms.py, fill in the real API URL and
    request/response structure in this class and in parser.py.
    """

    BASE_URL = "https://in.bookmyshow.com"

    # TODO: Replace with the real endpoint discovered in Milestone 1
    # Common patterns seen in BMS apps:
    #   /serv/getData?cmd=GETQUICKBOOK&...
    #   /api/v1/venue/shows?...
    #   /api/movies-by-city/...
    SHOWS_ENDPOINT = "/serv/getData"

    def __init__(self, city_code: str = "BHU"):
        self.city_code = city_code
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://in.bookmyshow.com/",
            "x-bms-id": "IN-BMS",
            "x-region-code": city_code,
            "x-region-slug": "bhubaneswar",
        }

    async def get_all_movies(self) -> list[dict]:
        """
        Discover all currently bookable movies in the configured city.

        TODO: implement after Milestone 1 reveals the movies-listing endpoint.
        """
        raise NotImplementedError(
            "Run discover_bms.py first (Milestone 1) to find the correct API endpoint."
        )

    async def get_slots(
        self,
        movie_id: str,
        movie_name: str,
        date: str,
        booking_url: str,
    ) -> list[ShowSlot]:
        """
        Fetch all ShowSlots for a given movie + date.

        TODO: implement after Milestone 1 reveals the correct API endpoint
        and response structure.

        Args:
            movie_id:    BMS event code, e.g. "ET00439318"
            movie_name:  Human-readable title, e.g. "Awarapan 2"
            date:        ISO date string, e.g. "2026-08-25"
            booking_url: BMS booking URL for this movie

        Returns:
            List of ShowSlot objects (one per cinema × showtime × category).
        """
        # TODO: Replace with actual API call discovered in Milestone 1
        # Example of what this might look like:
        #
        # async with httpx.AsyncClient(headers=self._headers) as client:
        #     resp = await client.get(
        #         f"{self.BASE_URL}{self.SHOWS_ENDPOINT}",
        #         params={
        #             "cmd": "GETQUICKBOOK",
        #             "code": movie_id,
        #             "mtype": "MT",
        #             "city": self.city_code,
        #             "date": date.replace("-", ""),
        #             "output": "json",
        #         },
        #     )
        #     resp.raise_for_status()
        #     raw = resp.json()
        #     return parse_slots(raw, movie_id, movie_name, date, booking_url)

        raise NotImplementedError(
            "Run discover_bms.py first (Milestone 1) to find the correct API endpoint."
        )
