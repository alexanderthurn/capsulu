#!/usr/bin/env python3
"""
3_fetch_metrics.py — Fetch full store data from Steam's appdetails API.

Saves the COMPLETE raw API response per game so no data is lost.
Each game's full response is saved as an individual JSON file in
data/raw_store/{appid}.json for easy resumability.

The Steam Store API is heavily rate-limited (~200 requests per 5 minutes).
This script respects that with configurable delays and automatic backoff.

Usage:
    python 3_fetch_metrics.py [--limit 100] [--delay 1.5] [--tier all]

Output:
    data/raw_store/{appid}.json   (one per game, full raw response)
    data/fetch_progress.json      (checkpoint for resumability)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw_store")
APPS_FILE = os.path.join(DATA_DIR, "apps_all.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "fetch_progress.json")

STORE_API = "https://store.steampowered.com/api/appdetails"

# Default delay between requests (seconds) — conservative 2.0s pause for Steam API (30 req/min, well under 200/5min limit)
DEFAULT_DELAY = 2.0

# Backoff settings
INITIAL_BACKOFF = 60       # Wait 60s on first rate limit
MAX_BACKOFF = 300           # Max 5 minutes
BACKOFF_MULTIPLIER = 2      # Double backoff each time

# Max consecutive errors before stopping
MAX_CONSECUTIVE_ERRORS = 10


def load_apps(tier: str) -> list:
    """Load app list, optionally filtered by tier."""
    if not os.path.exists(APPS_FILE):
        print(f"❌ {APPS_FILE} not found. Run 1_collect_appids.py first.")
        sys.exit(1)

    with open(APPS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    apps = data["apps"]
    if tier != "all":
        apps = [a for a in apps if a.get("tier") == tier]

    return apps


def is_already_fetched(appid: int) -> bool:
    """Check if we already have this game's raw data."""
    filepath = os.path.join(RAW_DIR, f"{appid}.json")
    return os.path.exists(filepath) and os.path.getsize(filepath) > 0


def fetch_app_details(appid: int, delay: float) -> dict:
    """
    Fetch full store details for a single app.
    Returns a status dict with the result.
    """
    filepath = os.path.join(RAW_DIR, f"{appid}.json")

    try:
        resp = requests.get(
            STORE_API,
            params={"appids": appid, "l": "english"},
            timeout=30,
            headers={"User-Agent": "SteamCapsulu/1.0 (research project)"}
        )

        # Rate limited
        if resp.status_code == 429:
            return {"appid": appid, "status": "rate_limited"}

        # Permanent 4xx errors (game delisted, removed, region locked, or 404)
        if resp.status_code in (400, 403, 404):
            raw_output = {
                "appid": appid,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "http_status": resp.status_code,
                "api_success": False,
                "raw_response": {"error": f"HTTP {resp.status_code}"},
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(raw_output, f, indent=2, ensure_ascii=False)
            return {"appid": appid, "status": f"not_found_{resp.status_code}"}

        # Other HTTP errors (e.g. 500/502/503 server errors)
        if resp.status_code != 200:
            return {
                "appid": appid,
                "status": f"http_error_{resp.status_code}",
            }

        # Parse response
        try:
            data = resp.json() or {}
        except json.JSONDecodeError:
            data = {"error": "invalid_json"}

        # Steam returns {"{appid}": {"success": true/false, "data": {...}}}
        app_data = data.get(str(appid), {}) if isinstance(data, dict) else {}

        # Save the FULL raw response regardless of success
        raw_output = {
            "appid": appid,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "http_status": resp.status_code,
            "api_success": app_data.get("success", False) if isinstance(app_data, dict) else False,
            "raw_response": data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(raw_output, f, indent=2, ensure_ascii=False)

        if isinstance(app_data, dict) and app_data.get("success"):
            return {"appid": appid, "status": "success"}
        else:
            return {"appid": appid, "status": "api_failed"}

    except requests.exceptions.Timeout:
        return {"appid": appid, "status": "timeout"}
    except requests.exceptions.ConnectionError:
        return {"appid": appid, "status": "connection_error"}
    except requests.exceptions.RequestException as e:
        return {"appid": appid, "status": "error", "error": str(e)}


def save_progress(stats: dict, completed: int, total: int):
    """Save progress checkpoint."""
    progress = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "completed": completed,
        "total": total,
        "stats": stats,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def main():
    parser = argparse.ArgumentParser(
        description="Fetch raw store data from Steam API"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max games to fetch. 0 = all. Default: 0",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Seconds between requests. Default: {DEFAULT_DELAY}",
    )
    parser.add_argument(
        "--tier",
        choices=["all", "top", "mid", "low"],
        default="all",
        help="Which tier to fetch. Default: all",
    )
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)

    apps = load_apps(args.tier)
    if args.limit > 0:
        apps = apps[:args.limit]

    # Filter out already-fetched apps
    total_before_filter = len(apps)
    apps_to_fetch = [a for a in apps if not is_already_fetched(a["appid"])]
    already_done = total_before_filter - len(apps_to_fetch)

    total = len(apps_to_fetch)
    estimated_time = total * args.delay

    print("📊 Steam Capsulu — Raw Store Data Fetcher")
    print(f"   Total in scope:     {total_before_filter:,}")
    print(f"   Already fetched:    {already_done:,}")
    print(f"   Remaining:          {total:,}")
    print(f"   Delay per request:  {args.delay}s")
    print(f"   Estimated time:     {format_time(estimated_time)}")
    print(f"   Tier filter:        {args.tier}")
    print(f"   Output dir:         {RAW_DIR}/")
    print(f"   Saves:              FULL raw API response per game")
    print()

    if total == 0:
        print("✅ All games already fetched!")
        return

    stats = {
        "success": 0,
        "api_failed": 0,
        "rate_limited": 0,
        "errors": 0,
        "skipped": already_done,
    }
    completed = 0
    consecutive_errors = 0
    current_backoff = INITIAL_BACKOFF
    start_time = time.time()

    for app in apps_to_fetch:
        appid = app["appid"]
        name = app["name"]

        result = fetch_app_details(appid, args.delay)
        completed += 1

        if result["status"] == "success":
            stats["success"] += 1
            consecutive_errors = 0
            current_backoff = INITIAL_BACKOFF

        elif result["status"] == "rate_limited":
            stats["rate_limited"] += 1
            consecutive_errors += 1
            print(f"\n  ⚠️  Rate limited! Backing off for {current_backoff}s...")
            save_progress(stats, completed + already_done, total_before_filter)
            time.sleep(current_backoff)
            current_backoff = min(current_backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)

            # Retry this one
            result = fetch_app_details(appid, args.delay)
            if result["status"] == "success":
                stats["success"] += 1
                consecutive_errors = 0
            else:
                stats["errors"] += 1

        elif result["status"] == "api_failed":
            stats["api_failed"] += 1
            consecutive_errors = 0  # API responded, just no data

        else:
            stats["errors"] += 1
            consecutive_errors += 1

        # Stop if too many consecutive errors
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            print(f"\n  ❌ {MAX_CONSECUTIVE_ERRORS} consecutive errors. Stopping.")
            print(f"     Re-run the script to resume from where we left off.")
            break

        # Progress update & checkpoint every 10 games
        if completed % 10 == 0 or completed == total:
            save_progress(stats, completed + already_done, total_before_filter)
            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            eta = (total - completed) / rate if rate > 0 else 0
            print(
                f"  [{completed:,}/{total:,}] "
                f"✅ {stats['success']} "
                f"⛔ {stats['api_failed']} "
                f"🚫 {stats['rate_limited']} "
                f"❌ {stats['errors']} — "
                f"ETA: {format_time(eta)}"
            )

        # Respect rate limit
        time.sleep(args.delay)

    elapsed = time.time() - start_time
    save_progress(stats, completed + already_done, total_before_filter)

    # Calculate raw data size
    raw_size = sum(
        os.path.getsize(os.path.join(RAW_DIR, f))
        for f in os.listdir(RAW_DIR)
        if f.endswith(".json")
    )

    print(f"\n{'='*60}")
    print(f"📊 Fetch Summary")
    print(f"{'='*60}")
    print(f"  Processed:       {completed:,}")
    print(f"  Successful:      {stats['success']:,}")
    print(f"  API failed:      {stats['api_failed']:,} (game exists but no store data)")
    print(f"  Rate limited:    {stats['rate_limited']:,}")
    print(f"  Errors:          {stats['errors']:,}")
    print(f"  Already had:     {stats['skipped']:,}")
    print(f"  Raw data size:   {raw_size / (1024*1024):.1f} MB")
    print(f"  Time elapsed:    {format_time(elapsed)}")
    print(f"  Files saved to:  {RAW_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
