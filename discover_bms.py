"""
BookMyShow network discovery script - Milestone 1.

Run this FIRST before anything else. It opens the Awarapan 2 booking page
using Playwright, intercepts every network response, and prints all JSON
responses from BookMyShow's internal APIs.

Goal: find out exactly which API endpoint(s) return cinema/show/price data
so we can hit them directly with httpx instead of scraping the visual UI.

Usage:
    python discover_bms.py

Output:
    - List of all JSON API responses captured from the page
    - Saved to discovery/responses/ for manual inspection
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    console = Console(force_terminal=False)
except ImportError:
    class Console:
        def print(self, *a, **k): print(*a)
        def rule(self, *a, **k): print("=" * 60)
    console = Console()

# -- Config --------------------------------------------------------------------

TARGET_URL = (
    "https://in.bookmyshow.com/movies/bhubaneswar/awarapan-2/"
    "buytickets/ET00439318/20260825"
)

OUTPUT_DIR = Path("discovery") / "responses" / datetime.now().strftime("%Y%m%d_%H%M%S")

# Keywords that suggest a response is interesting
INTERESTING_KEYWORDS = [
    "venue", "show", "price", "seat", "ticket", "cinema",
    "schedule", "book", "avail", "category", "slot", "hall",
    "quickbook", "getdata", "serv",
]

# -- Helpers -------------------------------------------------------------------

def is_interesting(url: str, body: dict | list) -> bool:
    """Heuristic: is this response likely to contain show/price data?"""
    url_lower = url.lower()
    if any(kw in url_lower for kw in INTERESTING_KEYWORDS):
        return True
    # Check if the JSON body looks like it has show/price fields
    body_str = json.dumps(body).lower()
    if any(kw in body_str for kw in ["price", "venue", "showtime", "category"]):
        return True
    return False


def save_response(url: str, body: dict | list, index: int) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = url.split("?")[0].split("/")[-1] or "response"
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in safe_name)
    filename = OUTPUT_DIR / f"{index:03d}_{safe_name}.json"
    filename.write_text(json.dumps({"url": url, "body": body}, indent=2), encoding="utf-8")
    return filename

# -- Main ----------------------------------------------------------------------

async def discover():
    console.rule("[bold cyan]BOOKMYSHOW NETWORK DISCOVERY - Milestone 1")
    console.print(f"\n[yellow]Target URL:[/] {TARGET_URL}")
    console.print(f"[yellow]Output dir:[/] {OUTPUT_DIR}\n")

    captured = []       # all JSON responses
    interesting = []    # responses we think contain show/price data

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        page = await context.new_page()

        # -- Intercept every response --------------------------------------
        async def on_response(response):
            try:
                url = response.url
                # Skip non-BMS and non-JSON
                if "bookmyshow" not in url:
                    return
                content_type = response.headers.get("content-type", "")
                if "json" not in content_type:
                    return
                try:
                    body = await response.json()
                except Exception:
                    return

                entry = {"url": url, "status": response.status, "body": body}
                captured.append(entry)
                if is_interesting(url, body):
                    interesting.append(entry)
                    print(f"  [+] Interesting: {url[:100]}")
                else:
                    print(f"      Captured: {url[:100]}")
            except Exception:
                pass

        page.on("response", on_response)

        # -- Load the page -------------------------------------------------
        console.print("[bold]Loading page...[/]")
        try:
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30_000)
        except Exception as e:
            console.print(f"[red]Page load warning:[/] {e}")

        # Wait a bit more for lazy-loaded data
        await page.wait_for_timeout(3000)

        # Try clicking on a showtime if visible, to trigger price data loading
        try:
            show_buttons = await page.query_selector_all("[class*='show-time'], [class*='showtime'], [data-testid*='show']")
            if show_buttons:
                await show_buttons[0].click()
                console.print("[yellow]Clicked first showtime button - waiting for price data...[/]")
                await page.wait_for_timeout(3000)
        except Exception:
            pass

        await browser.close()

    # -- Report ------------------------------------------------------------
    console.rule()
    console.print(f"\n[bold]Total JSON responses captured:[/] {len(captured)}")
    console.print(f"[bold green]Interesting responses:[/] {len(interesting)}\n")

    if not interesting:
        console.print("[red]No interesting responses found. Showing all captured responses instead.[/]")
        interesting = captured

    for i, entry in enumerate(interesting):
        console.rule(f"[{i+1}] {entry['url'][:80]}")
        body_str = json.dumps(entry["body"], indent=2)
        # Show first 800 chars
        preview = body_str[:800] + ("..." if len(body_str) > 800 else "")
        try:
            console.print(Syntax(preview, "json", theme="monokai"))
        except Exception:
            console.print(preview)

        path = save_response(entry["url"], entry["body"], i + 1)
        console.print(f"  [dim]Saved -> {path}[/]")

    console.rule()
    console.print(
        "\n[bold yellow]Next step:[/] Inspect the saved files in "
        f"[cyan]{OUTPUT_DIR}[/] and identify which response contains "
        "cinema / showtime / category / price data.\n"
        "Then update [cyan]app/bms/client.py[/] to call that endpoint directly."
    )


if __name__ == "__main__":
    asyncio.run(discover())
