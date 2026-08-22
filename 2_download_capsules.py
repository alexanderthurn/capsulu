#!/usr/bin/env python3
"""
2_download_capsules.py — Download header capsule art from the Steam CDN.

Reads app IDs from data/apps_all.json and downloads the header image
for each game into a flat folder as {appid}.jpg.

Usage:
    python 2_download_capsules.py [--limit 10] [--workers 5] [--tier all]

Output:
    data/images/{appid}.jpg
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
APPS_FILE = os.path.join(DATA_DIR, "apps_all.json")

CDN_BASE = "https://cdn.akamai.steamstatic.com/steam/apps"

# Request timeout (seconds)
TIMEOUT = 15


def load_apps(tier: str) -> list:
    """Load app list from the JSON file, optionally filtered by tier."""
    if not os.path.exists(APPS_FILE):
        print(f"❌ {APPS_FILE} not found. Run 1_collect_appids.py first.")
        sys.exit(1)

    with open(APPS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    apps = data["apps"]

    if tier != "all":
        apps = [a for a in apps if a.get("tier") == tier]

    return apps


def download_header(appid: int) -> dict:
    """Download the header image for a single game with automatic CDN fallbacks."""
    filepath = os.path.join(IMAGES_DIR, f"{appid}.jpg")

    # Skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return {
            "appid": appid,
            "status": "skipped",
            "size": os.path.getsize(filepath),
        }

    # Candidate URLs: primary static CDN, shared store assets CDN, and raw_store JSON if present
    candidate_urls = [
        f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg",
        f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg",
    ]

    # Check if we already have exact hashed URL in raw_store
    store_file = os.path.join(DATA_DIR, "raw_store", f"{appid}.json")
    if os.path.exists(store_file):
        try:
            with open(store_file, "r", encoding="utf-8") as sf:
                s_data = json.load(sf)
                exact_url = s_data.get("raw_response", {}).get(str(appid), {}).get("data", {}).get("header_image")
                if exact_url and exact_url not in candidate_urls:
                    candidate_urls.insert(0, exact_url)
        except Exception:
            pass

    for url in candidate_urls:
        try:
            resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                if "image" in content_type or len(resp.content) >= 1000:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    return {
                        "appid": appid,
                        "status": "downloaded",
                        "size": len(resp.content),
                    }
        except Exception:
            continue

    return {"appid": appid, "status": "not_found", "size": 0}


def format_size(size_bytes: int) -> str:
    """Format bytes into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def main():
    parser = argparse.ArgumentParser(
        description="Download Steam header capsule art from CDN"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max number of games to download. 0 = all. Default: 0",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of parallel download workers. Default: 5",
    )
    parser.add_argument(
        "--tier",
        choices=["all", "top", "mid", "low"],
        default="all",
        help="Which tier to download. Default: all",
    )
    args = parser.parse_args()

    apps = load_apps(args.tier)
    if args.limit > 0:
        apps = apps[:args.limit]

    total_games = len(apps)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    print("🎨 Steam Capsulu — Header Capsule Downloader")
    print(f"   Games to process: {total_games:,}")
    print(f"   Image type:       header.jpg (460×215)")
    print(f"   Workers:          {args.workers}")
    print(f"   Tier filter:      {args.tier}")
    print(f"   Output dir:       {IMAGES_DIR}/")
    print(f"   Naming:           {{appid}}.jpg")
    print()

    stats = {
        "downloaded": 0,
        "skipped": 0,
        "not_found": 0,
        "errors": 0,
        "total_bytes": 0,
    }
    completed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(download_header, app["appid"]): app
            for app in apps
        }

        for future in as_completed(futures):
            app = futures[future]
            completed += 1

            try:
                r = future.result()
                if r["status"] == "downloaded":
                    stats["downloaded"] += 1
                    stats["total_bytes"] += r["size"]
                elif r["status"] == "skipped":
                    stats["skipped"] += 1
                    stats["total_bytes"] += r["size"]
                elif r["status"] == "not_found":
                    stats["not_found"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                stats["errors"] += 1

            if completed % 100 == 0 or completed == total_games:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (total_games - completed) / rate if rate > 0 else 0
                print(
                    f"  [{completed:,}/{total_games:,}] "
                    f"✅ {stats['downloaded']} ⏭️ {stats['skipped']} "
                    f"❌ {stats['not_found']} — "
                    f"{format_size(stats['total_bytes'])} — "
                    f"ETA: {eta:.0f}s"
                )

    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"📊 Download Summary")
    print(f"{'='*60}")
    print(f"  Games processed:    {completed:,}")
    print(f"  Downloaded:         {stats['downloaded']:,}")
    print(f"  Skipped:            {stats['skipped']:,} (already existed)")
    print(f"  Not found (404):    {stats['not_found']:,}")
    print(f"  Errors:             {stats['errors']:,}")
    print(f"  Total size:         {format_size(stats['total_bytes'])}")
    print(f"  Time elapsed:       {elapsed:.1f}s")

    if completed > 0:
        with open(APPS_FILE, "r", encoding="utf-8") as f:
            full_count = json.load(f)["total_apps"]

        if full_count > completed:
            avg_bytes = stats["total_bytes"] / completed
            projected = avg_bytes * full_count
            print(f"\n  📐 Projected size for ALL {full_count:,} games:")
            print(f"     ~{format_size(int(projected))}")

    print(f"{'='*60}")


if __name__ == "__main__":
    main()
