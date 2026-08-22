#!/usr/bin/env python3
"""
1_collect_appids.py — Collect Steam game app IDs from SteamSpy.

Fetches games across a wide range of popularity levels and saves them
into three tier-based JSON files:
  - data/apps_top.json     (successful games, 500K+ owners)
  - data/apps_mid.json     (medium games, 50K–500K owners)
  - data/apps_low.json     (unsuccessful / niche games, <50K owners)

Also saves the combined list to data/apps_all.json.

Usage:
    python 1_collect_appids.py [--pages 30]
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone

import requests

STEAMSPY_API = "https://steamspy.com/api.php"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Rate limit between API requests (seconds) — conservative 2.0s pause
RATE_LIMIT_DELAY = 2.0

# Tier thresholds (by estimated owners)
TOP_TIER_MIN_OWNERS = 500_000         # 500K+ owners = successful
MID_TIER_MIN_OWNERS = 50_000          # 50K–500K owners = medium
# Below 50K = low tier / unsuccessful / niche


def parse_owner_range(owner_str: str) -> int:
    """
    SteamSpy returns owners as a range like '20,000,000 .. 50,000,000'.
    We parse the midpoint as an estimate.
    """
    if not owner_str or owner_str == "0":
        return 0

    parts = owner_str.replace(",", "").split(" .. ")
    try:
        if len(parts) == 2:
            low = int(parts[0])
            high = int(parts[1])
            return (low + high) // 2
        else:
            return int(parts[0])
    except (ValueError, IndexError):
        return 0


def classify_tier(owners_estimate: int) -> str:
    """Classify a game into a tier based on estimated owners."""
    if owners_estimate >= TOP_TIER_MIN_OWNERS:
        return "top"
    elif owners_estimate >= MID_TIER_MIN_OWNERS:
        return "mid"
    else:
        return "low"


def fetch_page(page: int, retries: int = 3) -> dict:
    """Fetch a single page from SteamSpy's 'all' endpoint."""
    params = {"request": "all", "page": page}

    for attempt in range(retries):
        try:
            print(f"  Fetching page {page}...", end=" ", flush=True)
            resp = requests.get(STEAMSPY_API, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            print(f"got {len(data)} apps")
            return data
        except requests.exceptions.RequestException as e:
            print(f"error: {e}")
            if attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Giving up on page {page}")
                return {}
        except json.JSONDecodeError:
            print(f"  Invalid JSON response, skipping page {page}")
            return {}


def load_existing_apps() -> dict:
    """Load existing apps_all.json if present to enable incremental non-destructive updates."""
    filepath = os.path.join(DATA_DIR, "apps_all.json")
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            apps = data.get("apps", [])
            print(f"📖 Loaded {len(apps):,} existing games from {filepath}")
            return {a["appid"]: a for a in apps}
    except Exception as e:
        print(f"⚠️  Could not load existing apps: {e}")
        return {}


def collect_apps(num_pages: int = 100, start_page: int = 0) -> list:
    """Fetch pages from SteamSpy, merging into the existing dataset non-destructively."""
    all_apps = load_existing_apps()
    existing_count = len(all_apps)

    print(f"\n📦 Fetching up to {num_pages} pages from SteamSpy (starting at page {start_page})...\n")

    empty_pages = 0
    for page in range(start_page, start_page + num_pages):
        data = fetch_page(page)

        if not data:
            empty_pages += 1
            if empty_pages >= 3:
                print(f"\n  🏁 Reached end of catalog (3 empty pages in a row at page {page}). Stopping.")
                break
        else:
            empty_pages = 0

            for appid_str, info in data.items():
                try:
                    appid = int(appid_str)
                except ValueError:
                    continue

                owners_est = parse_owner_range(info.get("owners", "0"))

                all_apps[appid] = {
                    "appid": appid,
                    "name": info.get("name", "Unknown"),
                    "owners_estimate": owners_est,
                    "players_forever": info.get("players_forever", 0),
                    "average_playtime_forever": info.get("average_forever", 0),
                    "positive_reviews": info.get("positive", 0),
                    "negative_reviews": info.get("negative", 0),
                    "tier": classify_tier(owners_est),
                }

        time.sleep(RATE_LIMIT_DELAY)

    # Sort by estimated owners (descending)
    apps_list = list(all_apps.values())
    apps_list.sort(key=lambda x: x["owners_estimate"], reverse=True)

    new_count = len(apps_list) - existing_count
    print(f"\n✨ Dataset expanded: {existing_count:,} → {len(apps_list):,} games (+{new_count:,} new games)")

    return apps_list


def save_tier(apps: list, tier: str, label: str):
    """Save a tier's apps to its own JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"apps_{tier}.json")

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "tier": tier,
        "tier_label": label,
        "total_apps": len(apps),
        "source": "SteamSpy API (request=all)",
        "apps": apps,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  💾 {label}: {len(apps):,} games → {filepath}")


def save_all(apps: list):
    """Save all apps combined to apps_all.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, "apps_all.json")

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_apps": len(apps),
        "source": "SteamSpy API (request=all)",
        "tier_thresholds": {
            "top": f"{TOP_TIER_MIN_OWNERS:,}+ owners",
            "mid": f"{MID_TIER_MIN_OWNERS:,}–{TOP_TIER_MIN_OWNERS:,} owners",
            "low": f"<{MID_TIER_MIN_OWNERS:,} owners",
        },
        "apps": apps,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  💾 Combined: {len(apps):,} games → {filepath}")


def print_summary(apps: list):
    """Print a summary with tier breakdown."""
    if not apps:
        print("\n⚠️  No apps collected!")
        return

    top = [a for a in apps if a["tier"] == "top"]
    mid = [a for a in apps if a["tier"] == "mid"]
    low = [a for a in apps if a["tier"] == "low"]

    print(f"\n{'='*60}")
    print(f"📊 Collection Summary")
    print(f"{'='*60}")
    print(f"  Total games collected: {len(apps):,}")
    print()
    print(f"  🏆 Top tier (500K+ owners):   {len(top):,} games")
    if top:
        print(f"     Best:  {top[0]['name']} (~{top[0]['owners_estimate']/1e6:.0f}M)")
        print(f"     Worst: {top[-1]['name']} (~{top[-1]['owners_estimate']/1e3:.0f}K)")
    print(f"  📊 Mid tier (50K–500K):       {len(mid):,} games")
    if mid:
        print(f"     Best:  {mid[0]['name']} (~{mid[0]['owners_estimate']/1e3:.0f}K)")
        print(f"     Worst: {mid[-1]['name']} (~{mid[-1]['owners_estimate']/1e3:.0f}K)")
    print(f"  📉 Low tier (<50K):           {len(low):,} games")
    if low:
        print(f"     Best:  {low[0]['name']} (~{low[0]['owners_estimate']/1e3:.0f}K)")
        print(f"     Worst: {low[-1]['name']} (~{low[-1]['owners_estimate']/1e3:.0f}K)")
    print(f"{'='*60}")

    return top, mid, low


def main():
    parser = argparse.ArgumentParser(
        description="Collect Steam game app IDs from SteamSpy"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=100,
        help="Max number of pages to fetch (each page ~ 1,000 games). Default: 100 (auto-stops at end of catalog)",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=0,
        help="Page to start fetching from. Default: 0",
    )
    args = parser.parse_args()

    print("🎮 Steam Capsulu — App ID Collector")
    print(f"   Pages to fetch: {args.pages} (starting at page {args.start_page})")
    print(f"   Tier thresholds:")
    print(f"     🏆 Top:  {TOP_TIER_MIN_OWNERS:,}+ owners")
    print(f"     📊 Mid:  {MID_TIER_MIN_OWNERS:,}–{TOP_TIER_MIN_OWNERS:,} owners")
    print(f"     📉 Low:  <{MID_TIER_MIN_OWNERS:,} owners")

    apps = collect_apps(num_pages=args.pages, start_page=args.start_page)
    result = print_summary(apps)

    if result:
        top, mid, low = result

        print(f"\n💾 Saving results...\n")
        save_tier(top, "top", "Top tier (successful)")
        save_tier(mid, "mid", "Mid tier (medium)")
        save_tier(low, "low", "Low tier (unsuccessful/niche)")
        save_all(apps)

        print(f"\n✅ Done! Files saved to {DATA_DIR}/")


if __name__ == "__main__":
    main()
