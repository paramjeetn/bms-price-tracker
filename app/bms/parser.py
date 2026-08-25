"""
BookMyShow response parser -- converts raw BMS SSR JSON into ShowSlot objects.

The data comes from window.__INITIAL_STATE__ embedded in the HTML page.
Traversal path:
  state["showtimesFunctionalApi"]["queries"]["fetchPrimaryDynamic-..."]["data"]["data"]
  -> showtimeWidgets -> groupList -> venueGroup -> venue-card -> shows -> bottomSheetData
"""

from __future__ import annotations
import re
from typing import Any

from app.bms.models import ShowSlot


def _parse_price(val: Any) -> int:
    """
    Extract integer price from float, int, or strings like:
      'Rs. 149.00', 'Rs.149', 'INR 149', '149.00'
    Returns 0 on failure.
    """
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(round(float(val)))
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return 0
        try:
            return int(round(float(val)))
        except ValueError:
            match = re.search(r"(\d+(?:\.\d+)?)", val)
            if match:
                try:
                    return int(round(float(match.group(1))))
                except ValueError:
                    return 0
    return 0


def _parse_format(format_str: str) -> tuple[str, str]:
    """
    Parse format string like 'Hindi - 2D' into (language, format).

    Examples:
        'Hindi - 2D'   -> ('Hindi', '2D')
        'Hindi - IMAX' -> ('Hindi', 'IMAX')
        'English - 3D' -> ('English', '3D')
        '2D'           -> ('', '2D')
        ''             -> ('', '')
    """
    if not format_str:
        return ("", "")
    format_str = format_str.strip()
    # BMS uses ' • ' (bullet) or ' - ' as separator between language and format
    for sep in (" \u2022 ", " - ", "\u2022", "-"):
        if sep in format_str:
            parts = format_str.split(sep, 1)
            return (parts[0].strip(), parts[1].strip())
    return ("", format_str)


def _is_valid_showtime(show_time_str: str) -> bool:
    """
    Check if a showtime string (e.g., '10:30 AM', '06:15 PM', '2:00 PM') falls within
    the allowed window of 6:00 AM to 4:00 PM (06:00 to 16:00).
    Ignores any showtimes between 6:00 PM and 6:00 AM.
    """
    if not show_time_str:
        return True
    match = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", show_time_str, re.IGNORECASE)
    if not match:
        return True

    hour = int(match.group(1))
    minute = int(match.group(2))
    period = match.group(3).upper()

    if period == "AM":
        if hour == 12:
            hour = 0
    else:  # PM
        if hour != 12:
            hour += 12

    show_time_minutes = hour * 60 + minute
    start_minutes = 6 * 60       # 06:00 AM (360)
    end_minutes = 16 * 60        # 04:00 PM (960)

    return start_minutes <= show_time_minutes <= end_minutes


def parse_slots(
    raw: dict,
    movie_id: str,
    movie_name: str,
    date: str,
    booking_url: str,
) -> list[ShowSlot]:
    """
    Parse BMS __INITIAL_STATE__ data block into a flat list of ShowSlot objects.
    One ShowSlot = one (venue x showtime x seat_category) combination.

    Primary path  : raw["showtimeWidgets"] (modern BMS structure)
    Fallback path : raw["venues"] (legacy BMS API structure)
    """
    if not isinstance(raw, dict):
        return []

    slots: list[ShowSlot] = []

    # ── Primary: modern showtimeWidgets structure ──────────────────────────
    showtime_widgets = raw.get("showtimeWidgets")
    if showtime_widgets is None and isinstance(raw.get("data"), dict):
        showtime_widgets = raw["data"].get("showtimeWidgets")

    if isinstance(showtime_widgets, list):
        for widget in showtime_widgets:
            if not isinstance(widget, dict) or widget.get("type") != "groupList":
                continue
            for group in widget.get("data", []):
                if not isinstance(group, dict) or group.get("type") != "venueGroup":
                    continue
                for venue_card in group.get("data", []):
                    if not isinstance(venue_card, dict):
                        continue

                    venue_ad = venue_card.get("additionalData", {})
                    venue_name = venue_ad.get("venueName", "")
                    venue_code = venue_ad.get("venueCode", "")

                    sections = venue_card.get("showtimesSections") or venue_card.get("showGroup") or []
                    if not isinstance(sections, list):
                        continue

                    for section in sections:
                        if not isinstance(section, dict):
                            continue
                        for show in section.get("showtimes", section.get("shows", [])):
                            if not isinstance(show, dict):
                                continue

                            show_ad = show.get("additionalData", {})
                            show_time = show.get("title", "") or show_ad.get("showTime", "")
                            show_date_code = show_ad.get("showDateCode", "")

                            if not _is_valid_showtime(show_time):
                                continue

                            # Resolve date: prefer passed-in date, fallback to showDateCode
                            show_date = date
                            if not show_date and show_date_code and len(show_date_code) == 8:
                                d = show_date_code
                                show_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"

                            # Navigate to seat categories via bottomSheetData
                            bottom_sheet = (
                                show.get("customGestureCTA", {})
                                .get("additionalData", {})
                                .get("bottomSheetData", {})
                            )
                            bsw = bottom_sheet.get("widgets", []) if isinstance(bottom_sheet, dict) else []

                            # First pass: grab format string
                            format_str = ""
                            for w in bsw:
                                if isinstance(w, dict) and w.get("layoutId") == "format-container":
                                    format_str = w.get("variableData", {}).get("format", "")
                                    break

                            language, fmt = _parse_format(format_str)
                            if not fmt:
                                fmt = "2D"  # safe default

                            # Second pass: one ShowSlot per seat category
                            for w in bsw:
                                if not isinstance(w, dict):
                                    continue
                                if "seat-category" not in w.get("layoutId", ""):
                                    continue

                                vd = w.get("variableData", {})
                                seat_type  = vd.get("seatType", "")
                                seat_cost  = vd.get("seatCost", "")
                                # BMS has a typo: "seatAvalibility" (missing 'i')
                                seat_avail = vd.get("seatAvalibility", "")

                                price = _parse_price(seat_cost)
                                if price <= 0:
                                    continue

                                avail_upper = str(seat_avail).upper()
                                available = "AVAILABLE" in avail_upper and "SOLD" not in avail_upper

                                slots.append(ShowSlot(
                                    movie      = movie_name,
                                    movie_id   = movie_id,
                                    date       = show_date,
                                    cinema     = venue_name,
                                    cinema_id  = venue_code,
                                    showtime   = show_time,
                                    format     = fmt,
                                    category   = seat_type,
                                    price      = price,
                                    available  = available,
                                    booking_url= booking_url,
                                    language   = language,
                                ))
        return slots

    # ── Fallback: legacy venues structure ──────────────────────────────────
    venues = raw.get("venues") or (raw.get("data", {}).get("venues") if isinstance(raw.get("data"), dict) else None)
    if isinstance(venues, list):
        for venue in venues:
            if not isinstance(venue, dict):
                continue
            venue_code = str(venue.get("venueCode") or venue.get("VenueCode") or "")
            venue_name = str(venue.get("venueName") or venue.get("VenueName") or "")
            for show in (venue.get("shows") or venue.get("Shows") or []):
                if not isinstance(show, dict):
                    continue
                show_time  = str(show.get("showTime") or show.get("ShowTime") or "")
                if not _is_valid_showtime(show_time):
                    continue
                show_date  = str(show.get("showDate") or date or "")
                fmt        = str(show.get("experience") or show.get("format") or "2D")
                language   = str(show.get("language") or "")
                for cat in (show.get("categories") or show.get("Categories") or []):
                    if not isinstance(cat, dict):
                        continue
                    cat_name = str(cat.get("categoryName") or cat.get("name") or "")
                    price    = _parse_price(cat.get("price"))
                    if price <= 0:
                        continue
                    available = not bool(cat.get("isSoldOut"))
                    slots.append(ShowSlot(
                        movie      = movie_name,
                        movie_id   = movie_id,
                        date       = show_date,
                        cinema     = venue_name,
                        cinema_id  = venue_code,
                        showtime   = show_time,
                        format     = fmt,
                        category   = cat_name,
                        price      = price,
                        available  = available,
                        booking_url= booking_url,
                        language   = language,
                    ))

    return slots


def parse_movies_response(raw: dict | list) -> list[dict]:
    """
    Parse movies discovery response into a list of movie dicts.

    Input:  {"data": [{"eventCode": ..., "eventTitle": ..., "slug": ..., "languages": [...]}]}
    Output: [{"movie_id": ..., "title": ..., "slug": ..., "languages": [...], "booking_url": ""}]
    """
    if isinstance(raw, list):
        raw_list = raw
    elif isinstance(raw, dict):
        raw_list = raw.get("data") or raw.get("movies") or []
    else:
        return []

    if not isinstance(raw_list, list):
        return []

    movies: list[dict] = []
    seen_ids: set[str] = set()

    for item in raw_list:
        if not isinstance(item, dict):
            continue
        movie_id = str(item.get("eventCode") or item.get("movie_id") or item.get("code") or "").strip()
        title    = str(item.get("eventTitle") or item.get("title") or item.get("name") or "").strip()
        slug     = str(item.get("slug") or item.get("eventSlug") or "").strip()

        if not slug and title:
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()

        langs = item.get("languages") or item.get("language") or []
        if isinstance(langs, str):
            languages = [langs.strip()] if langs.strip() else []
        elif isinstance(langs, (list, tuple)):
            languages = [str(l).strip() for l in langs if l]
        else:
            languages = []

        if not movie_id and not title:
            continue
        if movie_id and movie_id in seen_ids:
            continue
        if movie_id:
            seen_ids.add(movie_id)

        movies.append({
            "movie_id":    movie_id,
            "title":       title,
            "slug":        slug,
            "languages":   languages,
            "booking_url": str(item.get("booking_url") or ""),
        })

    return movies
