"""
Response parser — converts raw BMS API JSON into ShowSlot objects.

STATUS: Placeholder — to be implemented after Milestone 1 reveals
the exact shape of the BookMyShow API response.

The parser is intentionally separated from the client so that
if BMS changes its API structure, only this file needs updating.
"""

from app.bms.models import ShowSlot


def parse_slots(
    raw: dict,
    movie_id: str,
    movie_name: str,
    date: str,
    booking_url: str,
) -> list[ShowSlot]:
    """
    Parse a raw BMS API response into a flat list of ShowSlot objects.

    One ShowSlot = one (cinema × showtime × seat_category) combination.

    TODO: implement once discover_bms.py reveals the actual response structure.

    Expected raw structure (hypothetical — will be filled in after Milestone 1):

    {
      "BookMyShow": {
        "arrEvents": [
          {
            "VenueName": "PVR XYZ",
            "VenueCode": "PVRX",
            "ShowDetails": [
              {
                "ShowTime": "10:30 AM",
                "ShowDate": "20260825",
                "AvailableCat": [
                  { "CategoryName": "Classic", "CurrencyCode": "Rs.", "PriceRange": "₹ 100" },
                  { "CategoryName": "Premium", "CurrencyCode": "Rs.", "PriceRange": "₹ 150" }
                ]
              }
            ]
          }
        ]
      }
    }
    """
    raise NotImplementedError(
        "Implement after Milestone 1. See discover_bms.py and discovery/responses/."
    )


def _parse_price(price_str: str) -> int:
    """
    Extract integer price from strings like '₹ 100', 'Rs. 99', '100.00'.
    """
    import re
    digits = re.sub(r"[^\d]", "", price_str)
    return int(digits) if digits else 0
