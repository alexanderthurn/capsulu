#!/usr/bin/env python3
"""
4_mosaic.py — Generate mosaic grid images per tier.

Creates a large composite image for each tier (top/mid/low) by tiling
all header capsule images into a grid. Useful for visual pattern
recognition across success tiers.

Usage:
    python 4_mosaic.py [--thumb-width 120] [--tier all]
    python 4_mosaic.py --tier top --thumb-width 200
    python 4_mosaic.py --tier low --thumb-width 60

Output:
    output/mosaic_top.jpg
    output/mosaic_mid.jpg
    output/mosaic_low.jpg
"""

import argparse
import json
import math
import os
import sys
import time

from PIL import Image

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# Header image original aspect ratio (460x215)
HEADER_ASPECT = 215 / 460  # ~0.467

# Default thumbnail widths per tier (larger for smaller sets)
DEFAULT_THUMB_WIDTHS = {
    "top": 150,
    "mid": 80,
    "low": 80,
}


def load_tier_apps(tier: str) -> list:
    """Load app IDs for a specific tier."""
    filepath = os.path.join(DATA_DIR, f"apps_{tier}.json")
    if not os.path.exists(filepath):
        print(f"❌ {filepath} not found. Run 1_collect_appids.py first.")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["apps"]


def get_available_images(apps: list) -> list:
    """Filter apps to only those with downloaded images."""
    available = []
    for app in apps:
        img_path = os.path.join(IMAGES_DIR, f"{app['appid']}.jpg")
        if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
            available.append(app)
    return available


def build_mosaic(apps: list, tier: str, thumb_width: int) -> str:
    """Build a mosaic image for a tier and return the output path."""
    thumb_height = int(thumb_width * HEADER_ASPECT)
    total = len(apps)

    # Calculate grid dimensions (aim for roughly square)
    cols = math.ceil(math.sqrt(total * (thumb_width / thumb_height)))
    rows = math.ceil(total / cols)

    mosaic_width = cols * thumb_width
    mosaic_height = rows * thumb_height

    print(f"  Grid:        {cols} × {rows} = {cols * rows} slots ({total} images)")
    print(f"  Thumb size:  {thumb_width} × {thumb_height} px")
    print(f"  Mosaic size: {mosaic_width:,} × {mosaic_height:,} px")
    print(f"  Building...", end=" ", flush=True)

    # Create the mosaic canvas (black background)
    mosaic = Image.new("RGB", (mosaic_width, mosaic_height), (0, 0, 0))

    placed = 0
    errors = 0
    start = time.time()

    for i, app in enumerate(apps):
        img_path = os.path.join(IMAGES_DIR, f"{app['appid']}.jpg")

        try:
            with Image.open(img_path) as img:
                img = img.convert("RGB")
                img = img.resize((thumb_width, thumb_height), Image.LANCZOS)

                col = i % cols
                row = i // cols
                x = col * thumb_width
                y = row * thumb_height

                mosaic.paste(img, (x, y))
                placed += 1

        except Exception as e:
            errors += 1

        if (i + 1) % 500 == 0:
            print(f"{i + 1}...", end=" ", flush=True)

    elapsed = time.time() - start
    print(f"done! ({elapsed:.1f}s)")

    if errors > 0:
        print(f"  ⚠️  {errors} images failed to load")

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"mosaic_{tier}.jpg")
    mosaic.save(output_path, "JPEG", quality=90)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved:       {output_path} ({file_size:.1f} MB)")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate mosaic grid images per success tier"
    )
    parser.add_argument(
        "--thumb-width",
        type=int,
        default=0,
        help="Thumbnail width in pixels. 0 = auto (150 for top, 80 for mid/low)",
    )
    parser.add_argument(
        "--tier",
        choices=["all", "top", "mid", "low"],
        default="all",
        help="Which tier(s) to generate. Default: all",
    )
    parser.add_argument(
        "--sort-by",
        choices=["owners", "reviews", "name", "random"],
        default="owners",
        help="How to sort images in the grid. Default: owners (descending)",
    )
    args = parser.parse_args()

    tiers = ["top", "mid", "low"] if args.tier == "all" else [args.tier]

    print("🖼️  Steam Capsulu — Mosaic Generator")
    print()

    for tier in tiers:
        print(f"{'='*60}")
        tier_labels = {"top": "🏆 Top (successful)", "mid": "📊 Mid (medium)", "low": "📉 Low (niche)"}
        print(f"  {tier_labels.get(tier, tier)}")
        print(f"{'='*60}")

        apps = load_tier_apps(tier)
        if not apps:
            continue

        apps = get_available_images(apps)
        print(f"  Images:      {len(apps):,} available")

        if not apps:
            print(f"  ⚠️  No images found for this tier. Run 2_download_capsules.py first.")
            continue

        # Sort
        if args.sort_by == "owners":
            apps.sort(key=lambda x: x.get("owners_estimate", 0), reverse=True)
        elif args.sort_by == "reviews":
            apps.sort(key=lambda x: x.get("positive_reviews", 0), reverse=True)
        elif args.sort_by == "name":
            apps.sort(key=lambda x: x.get("name", "").lower())
        elif args.sort_by == "random":
            import random
            random.shuffle(apps)

        # Determine thumbnail width
        thumb_w = args.thumb_width if args.thumb_width > 0 else DEFAULT_THUMB_WIDTHS.get(tier, 80)

        build_mosaic(apps, tier, thumb_w)
        print()

    print("✅ Done!")


if __name__ == "__main__":
    main()
