#!/usr/bin/env python3
"""
4_mosaic.py — Generate mosaic grid images per tier with advanced color sorting.

Creates a large composite image for each tier (top/mid/low) by tiling
all header capsule images into a grid with perceptual color ordering.

Usage:
    python 4_mosaic.py                              # Default: Stepped Rainbow (best)
    python 4_mosaic.py --sort-by rainbow --tier top
    python 4_mosaic.py --sort-by brightness --tier top
    python 4_mosaic.py --sort-by warmth --tier all
    python 4_mosaic.py --tier top --thumb-width 200

Output:
    output/mosaic_top.jpg
    output/mosaic_mid.jpg
    output/mosaic_low.jpg
"""

import argparse
import colorsys
import json
import math
import os
import sys
import time

from PIL import Image

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
RAW_ANALYSIS_DIR = os.path.join(DATA_DIR, "raw_analysis")
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


def load_app_analysis(appid: int) -> dict:
    """Load raw image analysis JSON if available."""
    json_path = os.path.join(RAW_ANALYSIS_DIR, f"{appid}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def extract_color_features(app: dict) -> dict:
    """
    Extract or calculate color features (RGB, HSV, Luminance, Saturation) for sorting.
    Uses precomputed raw_analysis if available, otherwise samples thumbnail.
    """
    appid = app["appid"]
    analysis = load_app_analysis(appid)

    r, g, b = 0, 0, 0
    brightness = 0.0
    saturation = 0.0
    has_analysis = False

    if analysis and "color" in analysis:
        c_data = analysis["color"]
        dom_colors = c_data.get("dominant_colors", [])
        if dom_colors:
            # Pick the most prominent dominant color
            primary = dom_colors[0]
            rgb = primary.get("rgb", [0, 0, 0])
            r, g, b = rgb[0], rgb[1], rgb[2]
            brightness = float(c_data.get("avg_brightness", (0.2126 * r + 0.7152 * g + 0.0722 * b)))
            saturation = float(c_data.get("avg_saturation", 0)) / 255.0
            has_analysis = True

    if not has_analysis:
        img_path = os.path.join(IMAGES_DIR, f"{appid}.jpg")
        try:
            with Image.open(img_path) as img:
                small = img.resize((1, 1), Image.BOX).convert("RGB")
                r, g, b = small.getpixel((0, 0))
                brightness = 0.2126 * r + 0.7152 * g + 0.0722 * b
                h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                saturation = s
        except Exception:
            r, g, b = 0, 0, 0
            brightness = 0.0
            saturation = 0.0

    # Calculate normalized HSV
    norm_r, norm_g, norm_b = r / 255.0, g / 255.0, b / 255.0
    h, s, v = colorsys.rgb_to_hsv(norm_r, norm_g, norm_b)
    hue_deg = h * 360.0  # 0 to 360 degrees
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Warmth metric: Red/Amber positive, Blue/Cyan negative
    warmth = (r - b) / 255.0

    return {
        "r": r, "g": g, "b": b,
        "hue": hue_deg,
        "sat": s if s > 0 else saturation,
        "val": v,
        "lum": lum,
        "brightness": brightness,
        "warmth": warmth,
    }


def sort_apps(apps: list, sort_by: str) -> list:
    """
    Sort games according to the chosen strategy.
    
    'rainbow' (Recommended): Stepped perceptual color clustering:
      1. Dark / Noir covers (L < 35) sorted by brightness
      2. Vibrant chromatic spectrum sorted by Hue (Red -> Yellow -> Green -> Blue -> Purple)
         with sub-sorting by luminance to create beautiful continuous gradients
      3. Grayscale / Light covers sorted by lightness
    """
    print(f"  Sorting by '{sort_by}'...", end=" ", flush=True)
    start_t = time.time()

    if sort_by == "owners":
        apps.sort(key=lambda x: x.get("owners_estimate", 0), reverse=True)
    elif sort_by == "reviews":
        apps.sort(key=lambda x: x.get("positive_reviews", 0), reverse=True)
    elif sort_by == "name":
        apps.sort(key=lambda x: x.get("name", "").lower())
    elif sort_by == "random":
        import random
        random.shuffle(apps)
    else:
        # Extract color features for all apps
        features = {}
        for app in apps:
            features[app["appid"]] = extract_color_features(app)

        if sort_by == "rainbow":
            # Perceptual stepped rainbow: eliminates muddy gray/black artifacts from the rainbow
            def rainbow_key(app):
                f = features[app["appid"]]
                lum = f["lum"]
                sat = f["sat"]
                hue = f["hue"]

                # Group 0: Very dark / noir / near-black
                if lum < 35 or (lum < 55 and sat < 0.20):
                    return (0, 0, lum, 0)
                
                # Group 2: Low saturation grayscale / high-key white
                if sat < 0.18 and lum >= 55:
                    return (2, 0, lum, 0)

                # Group 1: Chromatic vibrant spectrum
                # Quantize into smooth 36-step hue buckets (~10 degrees each)
                hue_bucket = int(hue / 10.0)
                return (1, hue_bucket, -lum, -sat)

            apps.sort(key=rainbow_key)

        elif sort_by == "hue":
            # Pure continuous 0-360 hue sort
            apps.sort(key=lambda x: (features[x["appid"]]["hue"], features[x["appid"]]["lum"]))

        elif sort_by == "brightness":
            # Dark to light gradient
            apps.sort(key=lambda x: features[x["appid"]]["lum"])

        elif sort_by == "brightness_desc":
            # Light to dark gradient
            apps.sort(key=lambda x: features[x["appid"]]["lum"], reverse=True)

        elif sort_by == "saturation":
            # Desaturated/Monochrome to Super-Vibrant
            apps.sort(key=lambda x: (features[x["appid"]]["sat"], features[x["appid"]]["lum"]))

        elif sort_by == "warmth":
            # Warm (Red/Gold) to Cool (Deep Blue/Teal)
            apps.sort(key=lambda x: features[x["appid"]]["warmth"], reverse=True)

    print(f"done ({time.time() - start_t:.2f}s)")
    return apps


def build_mosaic(apps: list, tier: str, thumb_width: int, serpentine: bool = True, sort_by: str = "rainbow") -> str:
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
    if serpentine:
        print(f"  Layout:      Serpentine snake flow (seamless color transitions at row edges)")
    print(f"  Building...", end=" ", flush=True)

    # Create the mosaic canvas (dark Steam slate background)
    mosaic = Image.new("RGB", (mosaic_width, mosaic_height), (18, 24, 32))

    placed = 0
    errors = 0
    start = time.time()

    for i, app in enumerate(apps):
        img_path = os.path.join(IMAGES_DIR, f"{app['appid']}.jpg")

        row = i // cols
        col_in_row = i % cols
        
        # In serpentine mode, odd rows flow right-to-left so colors connect seamlessly
        if serpentine and (row % 2 == 1):
            col = cols - 1 - col_in_row
        else:
            col = col_in_row

        x = col * thumb_width
        y = row * thumb_height

        try:
            with Image.open(img_path) as img:
                img = img.convert("RGB")
                img = img.resize((thumb_width, thumb_height), Image.LANCZOS)
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
    suffix = f"_{sort_by}" if sort_by not in ("owners", "rainbow") else ""
    output_path = os.path.join(OUTPUT_DIR, f"mosaic_{tier}{suffix}.jpg")
    mosaic.save(output_path, "JPEG", quality=90)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved:       {output_path} ({file_size:.1f} MB)")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate mosaic grid images per success tier with advanced color sorting"
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
        choices=[
            "rainbow",
            "hue",
            "brightness",
            "brightness_desc",
            "saturation",
            "warmth",
            "owners",
            "reviews",
            "name",
            "random",
        ],
        default="rainbow",
        help=(
            "How to sort images: "
            "'rainbow' (Recommended: stepped chromatic spectrum + clean grayscales), "
            "'hue' (continuous 0-360 spectrum), "
            "'brightness' (dark to light), "
            "'warmth' (warm reds to cool blues), "
            "'saturation' (muted to neon), "
            "'owners', 'reviews', 'name', 'random'"
        ),
    )
    parser.add_argument(
        "--no-serpentine",
        action="store_true",
        help="Disable serpentine (snake) row flow and use standard left-to-right rows.",
    )
    args = parser.parse_args()

    tiers = ["top", "mid", "low"] if args.tier == "all" else [args.tier]
    serpentine = not args.no_serpentine

    print("🖼️  Steam Capsulu — Mosaic Generator")
    print(f"  🎨 Sort Strategy: {args.sort_by}")
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

        # Sort apps using chosen strategy
        apps = sort_apps(apps, args.sort_by)

        # Determine thumbnail width
        thumb_w = args.thumb_width if args.thumb_width > 0 else DEFAULT_THUMB_WIDTHS.get(tier, 80)

        build_mosaic(apps, tier, thumb_w, serpentine=serpentine, sort_by=args.sort_by)
        print()

    print("✅ Done!")


if __name__ == "__main__":
    main()
