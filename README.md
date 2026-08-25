# BMS Price Tracker

Monitors BookMyShow (Bhubaneswar) for cheap tickets and sends push notifications via ntfy when prices drop below your threshold.

## How it works

1. **GitHub Actions** runs every 30 minutes (free)
2. Fetches all shows from BookMyShow for the next 7 days
3. Compares prices against what's stored in **Turso** (libSQL)
4. Sends a **ntfy** push notification to your phone when:
   - A new show appears below ₹100
   - An existing show drops below ₹100
5. Cleans up show slots that are no longer available

## Stack

| Component | Technology |
|-----------|-----------|
| Scraping | Playwright / httpx |
| Database | Turso (libSQL/SQLite) |
| Scheduling | GitHub Actions cron |
| Notifications | ntfy.sh |

## Setup

### 1. Add GitHub Secrets

Go to **Settings → Secrets → Actions** and add:

| Secret | Value |
|--------|-------|
| `TURSO_URL` | Your Turso database URL |
| `TURSO_TOKEN` | Your Turso auth token |
| `NTFY_TOPIC` | Your ntfy topic name |

### 2. Subscribe on your phone

Install the ntfy app and subscribe to your topic.

### 3. Configure

Edit `config.yaml`:
```yaml
price_threshold: 100   # alert when price ≤ this
days_ahead: 7          # how many days to check
```

## Milestones

- [x] **M1** — Network discovery (`discover_bms.py`)
- [ ] **M2** — Single movie extractor (`app/bms/client.py`)
- [ ] **M3** — All movies discovery
- [ ] **M4** — All dates
- [ ] **M5** — Price engine + Turso
- [ ] **M6** — ntfy alerts
- [ ] **M7** — GitHub Actions cron (persistent monitoring)

## Running locally

```bash
pip install -r requirements.txt
playwright install chromium

# Milestone 1: discover BMS API
python discover_bms.py

# Full monitor (after implementing client.py)
TURSO_URL=... TURSO_TOKEN=... NTFY_TOPIC=... python -m app.main
```
