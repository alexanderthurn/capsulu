#!/usr/bin/env python3
"""
8_prepare_rated_images.py — Score & Organize All Capsule Images by Rating

Runs the canonical Capsulu scoring engine on every image in data/images/,
then copies each image to output/rated_capsules/ with a descriptive filename:

    {overall}_{contrast}_{warmth}_{entropy}_{edge}_{focus}_{text}_{appid}.jpg

Also exports output/rated_capsules/scores.csv with the full breakdown.

Usage:
    python 8_prepare_rated_images.py [--limit 100] [--workers 4]

Output:
    output/rated_capsules/{overall}_{c}_{w}_{e}_{ed}_{f}_{t}_{appid}.jpg
    output/rated_capsules/scores.csv
"""

import argparse
import csv
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "data", "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "rated_capsules")
SCORES_CSV = os.path.join(OUTPUT_DIR, "scores.csv")

CSV_HEADER = [
    "appid",
    "overallScore",
    "contrastScore",
    "warmthScore",
    "entropyScore",
    "edgeScore",
    "focusScore",
    "textScore",
    "tier",
    "brightnessStd",
    "warmPct",
    "entropy",
    "edgeDensity",
    "spotlightRatio",
    "isCenterFocused",
    "titleContrast",
    "titleZoneKey",
    "titleSizePct",
    "titleReadability",
    "filename",
]


def score_single_image(appid: int) -> dict:
    """Score a single image and return the result dict."""
    img_path = os.path.join(IMAGES_DIR, f"{appid}.jpg")

    if not os.path.exists(img_path):
        return {"appid": appid, "status": "no_image"}

    try:
        # Import inside worker to avoid pickling issues with multiprocessing
        from capsulu_scoring import score_image

        result = score_image(img_path)

        overall  = result["overallScore"]
        contrast = result["contrastScore"]
        warmth   = result["warmthScore"]
        entropy  = result["entropyScore"]
        edge     = result["edgeScore"]
        focus    = result["focusScore"]
        text     = result["textScore"]

        filename = f"{overall}_{contrast}_{warmth}_{entropy}_{edge}_{focus}_{text}_{appid}.jpg"

        return {
            "appid": appid,
            "status": "success",
            "overallScore": overall,
            "contrastScore": contrast,
            "warmthScore": warmth,
            "entropyScore": entropy,
            "edgeScore": edge,
            "focusScore": focus,
            "textScore": text,
            "tier": result["tier"],
            "brightnessStd": result["metrics"]["brightnessStd"],
            "warmPct": result["metrics"]["warmPct"],
            "entropy": result["metrics"]["entropy"],
            "edgeDensity": result["metrics"]["edgeDensity"],
            "spotlightRatio": result["metrics"]["spotlightRatio"],
            "isCenterFocused": result["metrics"]["isCenterFocused"],
            "titleContrast": result["metrics"]["titleContrast"],
            "titleZoneKey": result["metrics"]["titleZoneKey"],
            "titleSizePct": result["metrics"]["titleSizePct"],
            "titleReadability": result["metrics"]["titleReadability"],
            "filename": filename,
            "src_path": img_path,
        }
    except Exception as e:
        return {"appid": appid, "status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Score all Steam capsule images and organize by rating"
    )
    parser.add_argument("--limit", type=int, default=0,
                        help="Max images to process. 0 = all.")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel workers. Default: 4")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Discover all images
    all_images = []
    for fname in os.listdir(IMAGES_DIR):
        if fname.endswith(".jpg"):
            try:
                appid = int(fname.replace(".jpg", ""))
                all_images.append(appid)
            except ValueError:
                pass

    all_images.sort()

    # Load already-scored from CSV for resumability
    already_scored = set()
    if os.path.exists(SCORES_CSV):
        with open(SCORES_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    already_scored.add(int(row["appid"]))
                except (ValueError, KeyError):
                    pass

    # Filter out already-scored
    todo = [a for a in all_images if a not in already_scored]

    if args.limit > 0:
        todo = todo[:args.limit]

    print("🎨 Capsulu — Rated Image Preparation")
    print(f"   Total images:     {len(all_images):,}")
    print(f"   Already scored:   {len(already_scored):,}")
    print(f"   Remaining:        {len(todo):,}")
    print(f"   Workers:          {args.workers}")
    print(f"   Output:           {OUTPUT_DIR}/")
    print()

    if not todo:
        print("✅ All images already scored!")
        return

    # Open CSV in append mode
    write_header = not os.path.exists(SCORES_CSV) or os.path.getsize(SCORES_CSV) == 0
    csv_file = open(SCORES_CSV, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADER)
    if write_header:
        writer.writeheader()

    stats = {"success": 0, "errors": 0, "no_image": 0}
    completed = 0
    start_time = time.time()

    try:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(score_single_image, appid): appid
                for appid in todo
            }

            for future in as_completed(futures):
                completed += 1
                try:
                    result = future.result()
                    status = result["status"]

                    if status == "success":
                        stats["success"] += 1

                        # Copy image with rated filename
                        dst = os.path.join(OUTPUT_DIR, result["filename"])
                        shutil.copy2(result["src_path"], dst)

                        # Write CSV row
                        row = {k: result[k] for k in CSV_HEADER if k in result}
                        writer.writerow(row)
                        csv_file.flush()

                    elif status == "no_image":
                        stats["no_image"] += 1
                    else:
                        stats["errors"] += 1
                        if "error" in result:
                            print(f"  ⚠️  {result['appid']}: {result['error']}")

                except Exception as e:
                    stats["errors"] += 1
                    print(f"  ❌ Worker exception: {e}")

                if completed % 100 == 0 or completed == len(todo):
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (len(todo) - completed) / rate if rate > 0 else 0
                    print(
                        f"  [{completed:,}/{len(todo):,}] "
                        f"✅ {stats['success']} "
                        f"❌ {stats['errors']} "
                        f"📭 {stats['no_image']} — "
                        f"{rate:.1f} img/s, ETA: {eta:.0f}s"
                    )
    finally:
        csv_file.close()

    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"📊 Rated Image Preparation Summary")
    print(f"{'='*60}")
    print(f"  Scored & copied: {stats['success']:,}")
    print(f"  Previously done: {len(already_scored):,}")
    print(f"  No image:        {stats['no_image']:,}")
    print(f"  Errors:          {stats['errors']:,}")
    print(f"  Time:            {elapsed:.1f}s ({stats['success'] / max(1, elapsed):.1f} img/s)")
    print(f"  Output:          {OUTPUT_DIR}/")
    print(f"  CSV:             {SCORES_CSV}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
