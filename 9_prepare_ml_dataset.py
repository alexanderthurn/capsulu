#!/usr/bin/env python3
"""
9_prepare_ml_dataset.py — Organize Steam Capsule Artwork into ML Training Tiers

Creates two specialized PyTorch ImageFolder datasets (with train/val splits):

1. data/ml_global/ (Macro Steam Market - 5 Commercial Tiers)
   - 5_megahits/        (500K+ owners or >5K reviews)
   - 4_solid_indies/    (50K–500K owners or 500–5K reviews)
   - 3_moderate/        (10K–50K owners or 100–500 reviews)
   - 2_low_visibility/  (1K–10K owners or 10–100 reviews)
   - 1_flops/           (<1K owners or <10 reviews)

2. data/ml_indie_milestones/ (Indie Milestone Focus - 5 Review Brackets)
   - indie_0_zero/      (0 reviews)
   - indie_1_to_5/      (1 – 5 reviews)
   - indie_6_to_10/     (6 – 10 reviews)
   - indie_11_to_100/   (11 – 100 reviews)
   - indie_100_to_500/  (100 – 500 reviews)

Usage:
    python 9_prepare_ml_dataset.py [--sample-per-class 500] [--val-split 0.2] [--copy]
"""

import argparse
import json
import os
import random
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
APPS_FILE = os.path.join(DATA_DIR, "apps_all.json")

GLOBAL_DIR = os.path.join(DATA_DIR, "ml_global")
INDIE_DIR = os.path.join(DATA_DIR, "ml_indie_milestones")


def classify_global_tier(app: dict) -> str:
    """Classify into 5 macro commercial tiers based on owners & review volume."""
    owners = app.get("owners_estimate", 0)
    total_rev = app.get("positive_reviews", 0) + app.get("negative_reviews", 0)

    if owners >= 500_000 or total_rev >= 5_000:
        return "5_megahits"
    elif owners >= 50_000 or total_rev >= 500:
        return "4_solid_indies"
    elif owners >= 10_000 or total_rev >= 100:
        return "3_moderate"
    elif owners >= 1_000 or total_rev >= 10:
        return "2_low_visibility"
    else:
        return "1_flops"


def classify_indie_milestone(app: dict) -> str:
    """Classify indie games strictly into micro review milestone tiers (<= 500 reviews)."""
    total_rev = app.get("positive_reviews", 0) + app.get("negative_reviews", 0)

    if total_rev == 0:
        return "indie_0_zero"
    elif 1 <= total_rev <= 5:
        return "indie_1_to_5"
    elif 6 <= total_rev <= 10:
        return "indie_6_to_10"
    elif 11 <= total_rev <= 100:
        return "indie_11_to_100"
    elif 101 <= total_rev <= 500:
        return "indie_100_to_500"
    else:
        return None  # Games above 500 reviews are handled in the global model


def build_split(items: list, target_dir: str, val_split: float, copy_files: bool):
    """Create train/val folder structure and populate with image symlinks/copies."""
    random.seed(42)
    random.shuffle(items)

    val_count = int(len(items) * val_split)
    val_items = items[:val_count]
    train_items = items[val_count:]

    splits = {"train": train_items, "val": val_items}

    for split_name, split_data in splits.items():
        for item in split_data:
            cls_name = item["class"]
            appid = item["appid"]
            src_path = item["img_path"]

            dest_folder = os.path.join(target_dir, split_name, cls_name)
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, f"{appid}.jpg")

            if os.path.exists(dest_path):
                continue

            if copy_files:
                shutil.copy2(src_path, dest_path)
            else:
                try:
                    os.symlink(os.path.relpath(src_path, dest_folder), dest_path)
                except OSError:
                    shutil.copy2(src_path, dest_path)


def main():
    parser = argparse.ArgumentParser(description="Prepare ML Training Datasets for Steam Capsules")
    parser.add_argument("--sample-per-class", type=int, default=500,
                        help="Max samples per class (for fast prototyping). 0 = all. Default: 500")
    parser.add_argument("--val-split", type=float, default=0.2,
                        help="Validation split ratio. Default: 0.2 (20%)")
    parser.add_argument("--copy", action="store_true",
                        help="Copy files instead of symlinks. Default: false")
    args = parser.parse_args()

    if not os.path.exists(APPS_FILE):
        print(f"❌ {APPS_FILE} not found.")
        sys.exit(1)

    with open(APPS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    apps = data.get("apps", [])

    print("🎮 Capsulu — ML Dataset Preparation")
    print(f"   Total Apps in Catalog: {len(apps):,}")
    print(f"   Sample Per Class:      {'ALL' if args.sample_per_class == 0 else args.sample_per_class}")
    print(f"   Validation Ratio:      {args.val_split * 100:.0f}%")
    print(f"   Link Mode:             {'Copy' if args.copy else 'Symlink'}")
    print()

    # Filter to apps that have downloaded images
    valid_apps = []
    for a in apps:
        appid = a["appid"]
        img_path = os.path.join(IMAGES_DIR, f"{appid}.jpg")
        if os.path.exists(img_path) and os.path.getsize(img_path) > 1000:
            valid_apps.append({**a, "img_path": img_path})

    print(f"🖼️ Found {len(valid_apps):,} games with valid downloaded images.")

    # -----------------------------------------------------------------------
    # 1. Global Model Dataset
    # -----------------------------------------------------------------------
    print("\n📦 Building Global Commercial Dataset (data/ml_global/)...")
    global_buckets = {}
    for a in valid_apps:
        cls_name = classify_global_tier(a)
        if cls_name not in global_buckets:
            global_buckets[cls_name] = []
        global_buckets[cls_name].append({"appid": a["appid"], "img_path": a["img_path"], "class": cls_name})

    sampled_global = []
    for cls_name, items in sorted(global_buckets.items()):
        count_before = len(items)
        if args.sample_per_class > 0 and len(items) > args.sample_per_class:
            random.seed(42)
            items = random.sample(items, args.sample_per_class)
        sampled_global.extend(items)
        print(f"   • {cls_name:18s}: {len(items):,} games (from {count_before:,} total)")

    build_split(sampled_global, GLOBAL_DIR, args.val_split, args.copy)
    print(f"   ✅ Global Dataset ready at {GLOBAL_DIR}/ ({len(sampled_global):,} images)")

    # -----------------------------------------------------------------------
    # 2. Indie Milestone Dataset
    # -----------------------------------------------------------------------
    print("\n🎨 Building Indie Milestones Dataset (data/ml_indie_milestones/)...")
    indie_buckets = {}
    for a in valid_apps:
        cls_name = classify_indie_milestone(a)
        if not cls_name:
            continue
        if cls_name not in indie_buckets:
            indie_buckets[cls_name] = []
        indie_buckets[cls_name].append({"appid": a["appid"], "img_path": a["img_path"], "class": cls_name})

    sampled_indie = []
    for cls_name, items in sorted(indie_buckets.items()):
        count_before = len(items)
        if args.sample_per_class > 0 and len(items) > args.sample_per_class:
            random.seed(42)
            items = random.sample(items, args.sample_per_class)
        sampled_indie.extend(items)
        print(f"   • {cls_name:18s}: {len(items):,} games (from {count_before:,} total)")

    build_split(sampled_indie, INDIE_DIR, args.val_split, args.copy)
    print(f"   ✅ Indie Milestones Dataset ready at {INDIE_DIR}/ ({len(sampled_indie):,} images)")

    print(f"\n🎉 Dataset Preparation Complete! Ready for PyTorch Training.")


if __name__ == "__main__":
    main()
