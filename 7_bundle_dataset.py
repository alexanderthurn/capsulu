#!/usr/bin/env python3
"""
Bundle Complete Open-Source Dataset
Generates:
1. steam_capsules_full_dataset.json (Unified enriched JSON with store & CV metrics for 28,762 games)
2. steam_capsules_images.zip (ZIP archive containing all 28,762 capsule images)
Outputs to data/export/ and links to web/export/ for web downloads.
"""

import os
import sys
import json
import zipfile
import shutil
import glob
from datetime import datetime
import pandas as pd
from tqdm import tqdm

DATA_DIR = "data"
IMAGES_DIR = os.path.join(DATA_DIR, "images")
RAW_STORE_DIR = os.path.join(DATA_DIR, "raw_store")
RAW_ANALYSIS_DIR = os.path.join(DATA_DIR, "raw_analysis")
AGGREGATED_CSV = os.path.join(DATA_DIR, "aggregated_dataset.csv")

EXPORT_DIR = os.path.join(DATA_DIR, "export")
WEB_EXPORT_DIR = os.path.join("web", "export")

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(WEB_EXPORT_DIR, exist_ok=True)

def generate_full_json():
    print("\n📦 Generating steam_capsules_full_dataset.json...")
    
    # Load aggregated CSV as base if available
    df = None
    if os.path.exists(AGGREGATED_CSV):
        df = pd.read_csv(AGGREGATED_CSV)
        df_map = df.set_index('appid').to_dict(orient='index')
    else:
        df_map = {}

    analysis_files = glob.glob(os.path.join(RAW_ANALYSIS_DIR, "*.json"))
    print(f"Found {len(analysis_files)} raw analysis files.")

    games_list = []

    for af in tqdm(analysis_files, desc="Bundling Game Data"):
        appid_str = os.path.splitext(os.path.basename(af))[0]
        try:
            appid = int(appid_str)
        except ValueError:
            continue

        with open(af, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        # Load store data if present
        store_file = os.path.join(RAW_STORE_DIR, f"{appid}.json")
        store_details = {}
        if os.path.exists(store_file):
            try:
                with open(store_file, 'r', encoding='utf-8') as sf:
                    s_raw = json.load(sf)
                    if s_raw.get("api_success") and str(appid) in s_raw.get("raw_response", {}):
                        store_details = s_raw["raw_response"][str(appid)].get("data", {})
            except Exception:
                pass

        csv_row = df_map.get(appid, {})

        game_entry = {
            "appid": appid,
            "name": csv_row.get("name") or store_details.get("name") or f"App {appid}",
            "sales_tier": csv_row.get("tier", "unknown"),
            "reviews": {
                "total": int(csv_row.get("total_reviews", 0)) if pd.notna(csv_row.get("total_reviews")) else 0,
                "positive": int(csv_row.get("positive_reviews", 0)) if pd.notna(csv_row.get("positive_reviews")) else 0,
                "negative": int(csv_row.get("negative_reviews", 0)) if pd.notna(csv_row.get("negative_reviews")) else 0,
                "score_desc": csv_row.get("review_score", "Unknown")
            },
            "store_info": {
                "is_free": bool(store_details.get("is_free", False)),
                "price": str(csv_row.get("price", "N/A")),
                "release_date": str(csv_row.get("release_date", "N/A")),
                "genres": [g["description"] for g in store_details.get("genres", [])] if store_details.get("genres") else [str(csv_row.get("primary_genre", "Unknown"))],
                "developers": store_details.get("developers", []),
                "publishers": store_details.get("publishers", [])
            },
            "cv_metrics": {
                "avg_brightness": round(float(csv_row.get("avg_brightness", analysis_data.get("color", {}).get("avg_brightness", 0))), 2),
                "contrast_std": round(float(csv_row.get("brightness_std", analysis_data.get("color", {}).get("brightness_std", 0))), 2),
                "avg_saturation": round(float(csv_row.get("avg_saturation", analysis_data.get("color", {}).get("avg_saturation", 0))), 2),
                "warm_share_pct": round(float(analysis_data.get("color", {}).get("warm_share", 0)) * 100, 2),
                "cool_share_pct": round(float(analysis_data.get("color", {}).get("cool_share", 0)) * 100, 2),
                "neutral_share_pct": round(float(analysis_data.get("color", {}).get("neutral_share", 0)) * 100, 2),
                "shannon_entropy": round(float(csv_row.get("entropy", analysis_data.get("detail", {}).get("entropy", 0))), 3),
                "edge_density_pct": round(float(csv_row.get("edge_density", analysis_data.get("detail", {}).get("edge_density", 0))), 2),
                "center_spotlight_ratio": round(float(csv_row.get("center_vs_edge_brightness", analysis_data.get("composition", {}).get("center_vs_edge_brightness", 0))), 2),
                "dominant_palette": analysis_data.get("color", {}).get("dominant_colors", [])
            },
            "image_filename": f"{appid}.jpg"
        }

        games_list.append(game_entry)

    dataset_bundle = {
        "metadata": {
            "title": "Steam Capsule Art Empirical Dataset",
            "version": "1.0.0",
            "total_games": len(games_list),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": "Comprehensive empirical dataset of 28,762 Steam game capsules with Computer Vision metrics and Steam store metadata across 5 commercial sales tiers.",
            "license": "MIT License",
            "attribution": "Capsulu (https://github.com/alexanderthurn/steam-capsulu)"
        },
        "games": games_list
    }

    out_json_path = os.path.join(EXPORT_DIR, "steam_capsules_full_dataset.json")
    with open(out_json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset_bundle, f, indent=2)

    # Copy to web/export
    web_json_path = os.path.join(WEB_EXPORT_DIR, "steam_capsules_full_dataset.json")
    shutil.copyfile(out_json_path, web_json_path)

    json_size_mb = os.path.getsize(out_json_path) / (1024 * 1024)
    print(f"✅ Generated {out_json_path} ({json_size_mb:.2f} MB, {len(games_list)} games)")
    print(f"✅ Copied to {web_json_path}")
    return out_json_path


def generate_images_zip():
    print("\n🖼️ Packaging steam_capsules_images.zip...")
    image_files = glob.glob(os.path.join(IMAGES_DIR, "*.jpg")) + glob.glob(os.path.join(IMAGES_DIR, "*.png"))
    print(f"Found {len(image_files)} capsule images in {IMAGES_DIR}.")

    out_zip_path = os.path.join(EXPORT_DIR, "steam_capsules_images.zip")

    with zipfile.ZipFile(out_zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for img_path in tqdm(image_files, desc="Compressing Capsule Images"):
            arcname = os.path.basename(img_path)
            zipf.write(img_path, arcname=arcname)

    # Copy to web/export
    web_zip_path = os.path.join(WEB_EXPORT_DIR, "steam_capsules_images.zip")
    shutil.copyfile(out_zip_path, web_zip_path)

    zip_size_mb = os.path.getsize(out_zip_path) / (1024 * 1024)
    print(f"✅ Generated {out_zip_path} ({zip_size_mb:.2f} MB, {len(image_files)} images)")
    print(f"✅ Copied to {web_zip_path}")
    return out_zip_path


if __name__ == "__main__":
    json_path = generate_full_json()
    zip_path = generate_images_zip()
    print("\n🎉 Dataset Bundling Complete!")
