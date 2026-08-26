"""
BookMyShow client -- fetches movies and showtimes using curl_cffi with
Chrome TLS impersonation to bypass Cloudflare WAF.

Strategy:
  1. Fetch SSR HTML page with curl_cffi (impersonate='chrome124')
  2. Extract window.__INITIAL_STATE__ JSON from the HTML
  3. Navigate state["showtimesFunctionalApi"]["queries"]["fetchPrimaryDynamic-..."]
  4. Call parser.parse_slots() on the extracted data block

No direct JSON API calls -- they all return 403 from Cloudflare.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any, Optional

from curl_cffi import requests as cffi_requests

from app.bms.models import ShowSlot
from app.bms.parser import parse_slots, parse_movies_response

logger = logging.getLogger(__name__)


class BMSClient:
    """
    BookMyShow client.

    Uses curl_cffi with impersonate='chrome124' to bypass Cloudflare,
    then extracts embedded JSON from the SSR HTML.
    """

    BASE_URL = "https://in.bookmyshow.com"

    def __init__(
        self,
        city_slug: str = "bhubaneswar",
        city_code: str = "BHU",
        region_code: str = "BHUB",   # used in __INITIAL_STATE__ query key
        timeout: float = 20.0,
    ):
        self.city_slug   = city_slug
        self.city_code   = city_code
        self.region_code = region_code
        self.timeout     = timeout
        self._headers    = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://in.bookmyshow.com/",
            "x-region-code": self.city_code,
            "x-region-slug": self.city_slug,
        }
        self._playwright = None
        self._browser = None
        self._context = None

    def _get_browser_context(self):
        if self._context is None:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            self._context = self._browser.new_context(
                user_agent=self._headers["User-Agent"],
                locale="en-IN",
                timezone_id="Asia/Kolkata",
            )
            self._context.add_cookies([
                {"name": "RRC", "value": self.city_code, "domain": "in.bookmyshow.com", "path": "/"},
                {"name": "regionCode", "value": self.city_code, "domain": "in.bookmyshow.com", "path": "/"},
                {"name": "regionSlug", "value": self.city_slug, "domain": "in.bookmyshow.com", "path": "/"},
            ])
        return self._context

    def close(self):
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

    # ── Internal helpers ───────────────────────────────────────────────────

    def _sync_fetch(self, url: str) -> str:
        """Synchronous fetch with Chrome TLS impersonation, falling back to Playwright if needed."""
        try:
            resp = cffi_requests.get(
                url,
                headers=self._headers,
                impersonate="chrome124",
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"curl_cffi returned {resp.status_code} for {url}. Attempting Playwright fallback...")
        except Exception as e:
            logger.warning(f"curl_cffi exception for {url}: {e}. Attempting Playwright fallback...")

        # Playwright fallback (works reliably in datacenter environments / GitHub Actions)
        try:
            context = self._get_browser_context()
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1000)
            html = page.content()
            page.close()
            if "window.__INITIAL_STATE__" in html or "__NEXT_DATA__" in html or "bookmyshow" in html:
                return html
        except Exception as pe:
            logger.error(f"Playwright fallback failed for {url}: {pe}")

        raise RuntimeError(f"Failed to fetch {url} via both curl_cffi and Playwright")

    @staticmethod
    def _extract_initial_state(html: str) -> dict | None:
        """Extract window.__INITIAL_STATE__ JSON embedded in HTML."""
        # Method 1: raw_decode from assignment position
        pos = html.find("window.__INITIAL_STATE__ =")
        if pos != -1:
            sub = html[pos + len("window.__INITIAL_STATE__ ="):].strip()
            try:
                state, _ = json.JSONDecoder().raw_decode(sub)
                return state
            except Exception as e:
                logger.debug(f"raw_decode __INITIAL_STATE__ failed: {e}")

        # Method 2: __NEXT_DATA__ script tag
        m = re.search(
            r'<script\b[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
            html, re.DOTALL | re.IGNORECASE,
        )
        if m:
            try:
                return json.loads(m.group(1).strip())
            except Exception:
                pass

        # Method 3: regex fallback
        m2 = re.search(r'__INITIAL_STATE__\s*=\s*({.*?});\s*</script>', html, re.DOTALL)
        if m2:
            try:
                return json.loads(m2.group(1).strip())
            except Exception:
                pass

        return None

    def _slug_from(self, movie_name: str, booking_url: str = "") -> str:
        """Derive URL slug from booking_url or movie title."""
        if booking_url:
            m = re.search(r"/movies/[^/]+/([^/]+)/buytickets/", booking_url)
            if m:
                return m.group(1)
        return re.sub(r"[^a-zA-Z0-9]+", "-", movie_name).strip("-").lower() or "movie"

    # ── Public API ─────────────────────────────────────────────────────────

    async def get_all_movies(self) -> list[dict]:
        """
        Discover all currently bookable movies in the configured city.

        Fetches: https://in.bookmyshow.com/explore/movies-{city_slug}?cat=MT
        Returns: list[dict] with keys: movie_id, title, slug, languages, booking_url
        """
        url      = f"{self.BASE_URL}/explore/movies-{self.city_slug}?cat=MT"
        today    = datetime.now().strftime("%Y%m%d")
        last_err : Exception | None = None

        for attempt in range(1, 4):
            try:
                html  = await asyncio.to_thread(self._sync_fetch, url)
                state = self._extract_initial_state(html)

                movies: list[dict] = []
                seen:   set[str]   = set()

                # ── 1. Try __INITIAL_STATE__ Functional APIs ──────────
                if state and isinstance(state, dict):
                    for api_key in (
                        "moviesListFunctionalApi",
                        "exploreFunctionalApi",
                        "showtimesFunctionalApi",
                        "exploreApi",
                    ):
                        queries = state.get(api_key, {}).get("queries", {})
                        for q_val in queries.values():
                            if not isinstance(q_val, dict):
                                continue
                            items = q_val.get("data", {})
                            if isinstance(items, dict):
                                items = items.get("data", [])
                            if isinstance(items, list):
                                for m in parse_movies_response(items):
                                    if m["movie_id"] and m["movie_id"] not in seen:
                                        seen.add(m["movie_id"])
                                        if not m.get("booking_url"):
                                            m["booking_url"] = (
                                                f"{self.BASE_URL}/movies/{self.city_slug}/"
                                                f"{m['slug']}/buytickets/{m['movie_id']}/{today}"
                                            )
                                        movies.append(m)

                    # ── 2. Try SEO schema & footer in __INITIAL_STATE__ ──
                    seo_queries = state.get("seo", {}).get("queries", {})
                    for q_val in seo_queries.values():
                        if not isinstance(q_val, dict):
                            continue
                        data = q_val.get("data", {})
                        if not isinstance(data, dict):
                            continue

                        # ldSchema itemListElement (has structured movie title and URL)
                        item_list = (
                            data.get("ldSchema", {})
                            .get("itemListSchema", {})
                            .get("itemListElement", [])
                        )
                        if isinstance(item_list, list):
                            for item in item_list:
                                if not isinstance(item, dict):
                                    continue
                                item_url = item.get("url", "")
                                item_name = item.get("name", "")
                                m_match = re.search(
                                    r'/(?:movies/)?([a-z0-9-]+)/(ET\d+)',
                                    item_url,
                                    re.IGNORECASE,
                                )
                                if m_match:
                                    slug, event_code = m_match.group(1), m_match.group(2)
                                    if event_code not in seen:
                                        seen.add(event_code)
                                        movies.append({
                                            "movie_id": event_code,
                                            "title": item_name or slug.replace("-", " ").title(),
                                            "slug": slug,
                                            "languages": [],
                                            "booking_url": (
                                                f"{self.BASE_URL}/movies/{self.city_slug}/"
                                                f"{slug}/buytickets/{event_code}/{today}"
                                            ),
                                        })

                        # footer links (e.g. Movies Now Showing in {City})
                        footer_links = data.get("footer", {}).get("links", [])
                        if isinstance(footer_links, list):
                            for sec in footer_links:
                                if not isinstance(sec, dict):
                                    continue
                                for it in sec.get("items", []):
                                    if not isinstance(it, dict):
                                        continue
                                    link = it.get("link", "")
                                    label = it.get("label", "")
                                    m_match = re.search(
                                        r'/(?:movies/)?([a-z0-9-]+)/(ET\d+)',
                                        link,
                                        re.IGNORECASE,
                                    )
                                    if m_match:
                                        slug, event_code = m_match.group(1), m_match.group(2)
                                        if event_code not in seen:
                                            seen.add(event_code)
                                            movies.append({
                                                "movie_id": event_code,
                                                "title": label or slug.replace("-", " ").title(),
                                                "slug": slug,
                                                "languages": [],
                                                "booking_url": (
                                                    f"{self.BASE_URL}/movies/{self.city_slug}/"
                                                    f"{slug}/buytickets/{event_code}/{today}"
                                                ),
                                            })

                # ── 3. HTML regex fallback: extract ET codes + slugs ──
                regex_patterns = [
                    re.compile(r'href=["\'](?:https?://[^/]+)?/movies/([a-z0-9-]+)/(ET\d+)["\']', re.IGNORECASE),
                    re.compile(r'href=["\'](?:https?://[^/]+)?/[^/]+/movies/([a-z0-9-]+)/(ET\d+)["\']', re.IGNORECASE),
                    re.compile(r'href=["\'](?:https?://[^/]+)?/movies/[^/]+/([a-z0-9-]+)/buytickets/(ET\d+)', re.IGNORECASE),
                    re.compile(r'/(?:movies/)?([a-z0-9-]+)/(ET\d{8})', re.IGNORECASE),
                ]
                for p in regex_patterns:
                    for slug, event_code in p.findall(html):
                        if event_code not in seen:
                            seen.add(event_code)
                            movies.append({
                                "movie_id": event_code,
                                "title": slug.replace("-", " ").title(),
                                "slug": slug,
                                "languages": [],
                                "booking_url": (
                                    f"{self.BASE_URL}/movies/{self.city_slug}/"
                                    f"{slug}/buytickets/{event_code}/{today}"
                                ),
                            })

                if movies:
                    logger.info(f"Discovered {len(movies)} movies in {self.city_slug}")
                    return movies

                logger.warning(f"[{attempt}/3] No movies found from {url}")

            except Exception as e:
                logger.warning(f"[{attempt}/3] get_all_movies error: {e}")
                last_err = e

            if attempt < 3:
                await asyncio.sleep(2)

        logger.error(f"get_all_movies failed after 3 attempts. Last: {last_err}")
        return []

    async def get_slots(
        self,
        movie_id:   str,
        movie_name: str,
        date:       str,           # ISO: '2026-08-25'
        booking_url: str = "",
    ) -> list[ShowSlot]:
        """
        Fetch all ShowSlots for a movie + date.

        Steps:
          1. Build SSR page URL
          2. Fetch HTML with Chrome impersonation
          3. Extract __INITIAL_STATE__
          4. Find fetchPrimaryDynamic query key
          5. Parse via parse_slots()
        """
        # Normalise date to both formats
        date_clean = date.replace("-", "")
        date_iso   = f"{date_clean[:4]}-{date_clean[4:6]}-{date_clean[6:8]}" if "-" not in date else date

        slug     = self._slug_from(movie_name, booking_url)
        page_url = f"{self.BASE_URL}/movies/{self.city_slug}/{slug}/buytickets/{movie_id}/{date_clean}"
        if not booking_url:
            booking_url = page_url

        last_err: Exception | None = None

        for attempt in range(1, 4):
            try:
                html  = await asyncio.to_thread(self._sync_fetch, page_url)
                state = self._extract_initial_state(html)

                if not state or not isinstance(state, dict):
                    logger.warning(f"[{attempt}/3] No __INITIAL_STATE__ at {page_url}")
                    if attempt < 3:
                        await asyncio.sleep(2)
                    continue

                queries    = state.get("showtimesFunctionalApi", {}).get("queries", {})

                # Exact key first
                target_key = f"fetchPrimaryDynamic-{movie_id}---{date_clean}-{self.region_code}"
                query_obj  = queries.get(target_key)

                # Fuzzy fallback: any key containing the movie_id or fetchPrimaryDynamic
                if not query_obj:
                    for k, v in queries.items():
                        if "fetchPrimaryDynamic" in k or movie_id in k:
                            query_obj = v
                            logger.debug(f"Used fuzzy key: {k}")
                            break

                raw_data: dict = {}
                if isinstance(query_obj, dict):
                    inner = query_obj.get("data", {})
                    raw_data = inner.get("data", inner) if isinstance(inner, dict) else {}

                slots = parse_slots(
                    raw        = raw_data,
                    movie_id   = movie_id,
                    movie_name = movie_name,
                    date       = date_iso,
                    booking_url= booking_url,
                )

                if slots:
                    logger.info(f"Got {len(slots)} slots for {movie_name} on {date_iso}")
                    return slots

                logger.info(f"[{attempt}/3] 0 slots for {movie_name} ({movie_id}) on {date_iso}")

            except Exception as e:
                logger.warning(f"[{attempt}/3] get_slots error for {movie_id}: {e}")
                last_err = e

            if attempt < 3:
                await asyncio.sleep(2)

        logger.error(f"get_slots failed for {movie_id} after 3 attempts. Last: {last_err}")
        return []
