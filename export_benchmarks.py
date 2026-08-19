#!/usr/bin/env python3
"""
export_benchmarks.py — Compile statistical benchmarks from clean, verified Steam games
(excluding error/corrupt records) into benchmarks.json.
"""

import json
import os
import numpy as np
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
WEB_DIR = os.path.join(PROJECT_DIR, "web")
CSV_PATH = os.path.join(DATA_DIR, "aggregated_dataset.csv")
OUTPUT_JSON = os.path.join(WEB_DIR, "benchmarks.json")

os.makedirs(WEB_DIR, exist_ok=True)

print(f"📊 Reading {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)

# Clean filter: Remove any rows with missing or zero contrast/entropy/edge values
clean_df = df[
    df['brightness_std'].notna() & 
    df['entropy'].notna() & 
    df['edge_density'].notna() & 
    (df['brightness_std'] > 5.0) &
    df['name'].notna()
].copy()

total_valid = len(clean_df)
print(f"  Total valid, verified games: {total_valid:,}")

tiers = ["mega_hit", "successful", "moderate", "struggling", "near_zero"]
tier_labels = {
    "mega_hit": "Mega-Hit (>10k reviews)",
    "successful": "Successful (1k-10k reviews)",
    "moderate": "Moderate (100-1k reviews)",
    "struggling": "Struggling (10-100 reviews)",
    "near_zero": "Near-Zero (<10 reviews)"
}

tier_benchmarks = {}

for t in tiers:
    sub = clean_df[clean_df["tier"] == t]
    n = len(sub)
    if n == 0:
        continue

    tier_benchmarks[t] = {
        "name": tier_labels[t],
        "count": int(n),
        "contrast": {
            "mean": round(float(sub["brightness_std"].mean()), 2),
            "median": round(float(sub["brightness_std"].median()), 2),
            "p25": round(float(sub["brightness_std"].quantile(0.25)), 2),
            "p75": round(float(sub["brightness_std"].quantile(0.75)), 2),
        },
        "brightness": {
            "mean": round(float(sub["avg_brightness"].mean()), 2),
            "median": round(float(sub["avg_brightness"].median()), 2),
        },
        "saturation": {
            "mean": round(float(sub["avg_saturation"].mean()), 2),
            "median": round(float(sub["avg_saturation"].median()), 2),
        },
        "entropy": {
            "mean": round(float(sub["entropy"].mean()), 2),
            "median": round(float(sub["entropy"].median()), 2),
        },
        "edge_density": {
            "mean": round(float(sub["edge_density"].mean() * 100), 2),
            "median": round(float(sub["edge_density"].median() * 100), 2),
        },
        "warm_palette_pct": round(float((sub["palette_type"] == "warm").mean() * 100), 1),
        "neutral_palette_pct": round(float((sub["palette_type"] == "neutral").mean() * 100), 1),
        "cool_palette_pct": round(float((sub["palette_type"] == "cool").mean() * 100), 1),
        "center_focus_pct": round(float((sub["focus"] == "center").mean() * 100), 1),
        "dark_ratio": round(float(sub["dark_ratio"].mean() * 100), 1),
        "light_ratio": round(float(sub["light_ratio"].mean() * 100), 1),
    }

# Overall dataset stats
overall_stats = {
    "total_games_analyzed": total_valid,
    "contrast_p90": round(float(clean_df["brightness_std"].quantile(0.90)), 2),
    "contrast_p10": round(float(clean_df["brightness_std"].quantile(0.10)), 2),
    "entropy_p90": round(float(clean_df["entropy"].quantile(0.90)), 2),
    "entropy_p10": round(float(clean_df["entropy"].quantile(0.10)), 2),
    "edge_density_p90": round(float(clean_df["edge_density"].quantile(0.90) * 100), 2),
    "edge_density_p10": round(float(clean_df["edge_density"].quantile(0.10) * 100), 2),
}

# Curated sample presets
sample_presets = [
    {
        "id": "elden_ring",
        "name": "ELDEN RING",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>800k reviews)",
        "appid": 1245620,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg",
        "price": "$59.99",
        "tags": ["Souls-like", "RPG", "Dark Fantasy", "Open World"]
    },
    {
        "id": "hades",
        "name": "Hades",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>230k reviews)",
        "appid": 1145360,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg",
        "price": "$24.99",
        "tags": ["Action Roguelike", "Hack and Slash", "Indie"]
    },
    {
        "id": "stardew",
        "name": "Stardew Valley",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>600k reviews)",
        "appid": 413150,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg",
        "price": "$14.99",
        "tags": ["Farming Sim", "Pixel Graphics", "Co-op", "Relaxing"]
    },
    {
        "id": "cyberpunk",
        "name": "Cyberpunk 2077",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>700k reviews)",
        "appid": 1091500,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg",
        "price": "$59.99",
        "tags": ["Cyberpunk", "Open World", "RPG", "Sci-fi"]
    },
    {
        "id": "sample_modest",
        "name": "Ironcast",
        "tier": "moderate",
        "tier_label": "📊 Moderate (~500 reviews)",
        "appid": 327670,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/327670/header.jpg",
        "price": "$14.99",
        "tags": ["Match 3", "Steampunk", "Turn-Based Strategy"]
    },
    {
        "id": "sample_flop",
        "name": "Putridum Horror",
        "tier": "near_zero",
        "tier_label": "🕳️ Near-Zero (3 reviews)",
        "appid": 2294100,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/2294100/header.jpg",
        "price": "$1.99",
        "tags": ["Horror", "Action", "Indie"]
    }
]

output_payload = {
    "generated_at": pd.Timestamp.now().isoformat(),
    "overall": overall_stats,
    "tiers": tier_benchmarks,
    "presets": sample_presets
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2)

print(f"✅ Generated {OUTPUT_JSON} with {total_valid:,} clean verified records.")
