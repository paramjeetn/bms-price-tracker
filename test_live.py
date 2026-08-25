"""Live end-to-end test: fetch slots for Awarapan 2 using curl_cffi."""
import asyncio
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# Make sure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test():
    from app.bms.client import BMSClient

    client = BMSClient()

    print("=== Testing get_slots for Awarapan 2 (2026-08-25) ===")
    slots = await client.get_slots(
        movie_id="ET00439318",
        movie_name="Awarapan 2",
        date="2026-08-25",
        booking_url="https://in.bookmyshow.com/movies/bhubaneswar/awarapan-2/buytickets/ET00439318/20260825",
    )

    print(f"Total slots found: {len(slots)}")
    for s in slots[:15]:
        avail = "YES" if s.available else "NO"
        print(f"  [{avail}] {s.cinema:<45} | {s.showtime:<10} | {s.category:<12} | Rs.{s.price}")

    cheap = [s for s in slots if s.price <= 100 and s.available]
    print(f"\nCheap + available slots (<=Rs.100): {len(cheap)}")
    for s in cheap:
        print(f"  *** {s.cinema} | {s.showtime} | {s.category} | Rs.{s.price}")

    print("\n=== Testing get_all_movies ===")
    movies = await client.get_all_movies()
    print(f"Movies found in Bhubaneswar: {len(movies)}")
    for m in movies[:10]:
        print(f"  {m['movie_id']} | {m['title']}")

if __name__ == "__main__":
    asyncio.run(test())
