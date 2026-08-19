#!/usr/bin/env python3
"""
export_benchmarks.py — Compile statistical benchmarks from clean, verified Steam games
(excluding error/corrupt records) into benchmarks.json, including Sales Tiers and Genre Profiles.
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

# 1. Sales Tier Benchmarks
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

# 2. Genre-Specific Statistical Benchmarks
tracked_genres = {
    "Action": {
        "label": "Action / Shooter / Hack & Slash",
        "tip": "High dynamic lighting and warm rim-lighting are critical to pop against fast-paced Steam browse feeds."
    },
    "Adventure": {
        "label": "Adventure / Narrative / Exploration",
        "tip": "Atmospheric lighting with high tonal entropy and clear environmental depth performs best."
    },
    "RPG": {
        "label": "RPG / CRPG / Roguelike RPG",
        "tip": "Deep textural richness and unobstructed character silhouettes with prominent title branding."
    },
    "Strategy": {
        "label": "Strategy / Tactics / Deckbuilder",
        "tip": "Sharp typographic contrast and distinct iconography. Avoid oversaturated neon washes."
    },
    "Simulation": {
        "label": "Simulation / Management / Sandbox",
        "tip": "Balanced, inviting color temperatures with crisp line art and clear theme cues."
    },
    "Casual": {
        "label": "Casual / Puzzle / Cozy",
        "tip": "Vibrant, cheerful color palettes with higher average brightness and clean geometric shapes."
    },
    "Indie": {
        "label": "Indie Highlights",
        "tip": "Distinct stylized visual identity with strong hero focus to stand out from AAA realism."
    }
}

genre_benchmarks = {}

for g_key, g_meta in tracked_genres.items():
    if g_key == "Indie":
        sub = clean_df[clean_df["all_genres"].fillna("").str.contains("Indie", case=False, regex=False)]
    else:
        sub = clean_df[
            (clean_df["primary_genre"] == g_key) | 
            clean_df["all_genres"].fillna("").str.contains(g_key, case=False, regex=False)
        ]
    
    n = len(sub)
    if n < 10:
        continue

    # Get top performers in this genre
    top_sub = sub[sub["tier"].isin(["mega_hit", "successful"])]
    if len(top_sub) < 5:
        top_sub = sub

    genre_benchmarks[g_key] = {
        "name": g_meta["label"],
        "count": int(n),
        "tip": g_meta["tip"],
        "contrast": {
            "mean": round(float(sub["brightness_std"].mean()), 2),
            "median": round(float(sub["brightness_std"].median()), 2),
            "top_tier_mean": round(float(top_sub["brightness_std"].mean()), 2),
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
            "top_tier_mean": round(float(top_sub["entropy"].mean()), 2),
        },
        "edge_density": {
            "mean": round(float(sub["edge_density"].mean() * 100), 2),
            "median": round(float(sub["edge_density"].median() * 100), 2),
            "top_tier_mean": round(float(top_sub["edge_density"].mean() * 100), 2),
        },
        "warm_palette_pct": round(float((sub["palette_type"] == "warm").mean() * 100), 1),
        "neutral_palette_pct": round(float((sub["palette_type"] == "neutral").mean() * 100), 1),
        "cool_palette_pct": round(float((sub["palette_type"] == "cool").mean() * 100), 1),
        "center_focus_pct": round(float((sub["focus"] == "center").mean() * 100), 1),
    }

# 3. Overall dataset stats
overall_stats = {
    "total_games_analyzed": total_valid,
    "contrast_p90": round(float(clean_df["brightness_std"].quantile(0.90)), 2),
    "contrast_p10": round(float(clean_df["brightness_std"].quantile(0.10)), 2),
    "entropy_p90": round(float(clean_df["entropy"].quantile(0.90)), 2),
    "entropy_p10": round(float(clean_df["entropy"].quantile(0.10)), 2),
    "edge_density_p90": round(float(clean_df["edge_density"].quantile(0.90) * 100), 2),
    "edge_density_p10": round(float(clean_df["edge_density"].quantile(0.10) * 100), 2),
}

# 4. Curated sample presets & genre lineups
sample_presets = [
    {
        "id": "diception",
        "name": "DICEPTION",
        "appid": 4429000,
        "tier": "custom",
        "tier_label": "🎲 DICEPTION",
        "image_url": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4429000/56bd8aa0cf2d865acbae5501824e33c4dd8c2269/header.jpg?t=1785770104",
        "price": "4,99€",
        "tags": ["Indie", "Strategy"]
    },
    {
        "id": "melodan",
        "name": "Melodan",
        "appid": 4987230,
        "tier": "custom",
        "tier_label": "⚔️ Melodan",
        "image_url": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4987230/833a1d7f3a40629d6c8edd334ad871425ccd644b/header.jpg?t=1786736037",
        "price": "Coming Soon",
        "tags": ["Action", "Indie", "Strategy"]
    },
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
        "id": "balatro",
        "name": "Balatro",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>80k reviews)",
        "appid": 2379780,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg",
        "price": "$14.99",
        "tags": ["Roguelike Deckbuilder", "Strategy", "Indie"]
    },
    {
        "id": "stardew",
        "name": "Stardew Valley",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>600k reviews)",
        "appid": 413150,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg",
        "price": "$14.99",
        "tags": ["Farming Sim", "Simulation", "Pixel Graphics", "Co-op"]
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
        "id": "hollow_knight",
        "name": "Hollow Knight",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>350k reviews)",
        "appid": 367520,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg",
        "price": "$14.99",
        "tags": ["Metroidvania", "Adventure", "Souls-like", "2D"]
    },
    {
        "id": "sample_modest",
        "name": "Ironcast",
        "tier": "moderate",
        "tier_label": "📊 Moderate (~500 reviews)",
        "appid": 327670,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/327670/header.jpg",
        "price": "$14.99",
        "tags": ["Match 3", "Steampunk", "Strategy"]
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

# 5. Genre-specific catalog for dynamic 3x3 competitor simulator
genre_competitor_catalogs = {
    "Action": [
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "ULTRAKILL", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1229490/header.jpg", "appid": 1229490},
        {"name": "DOOM Eternal", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/782330/header.jpg", "appid": 782330},
        {"name": "Monster Hunter: World", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/582010/header.jpg", "appid": 582010},
        {"name": "Risk of Rain 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632360/header.jpg", "appid": 632360},
        {"name": "Vampire Survivors", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1794680/header.jpg", "appid": 1794680},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500}
    ],
    "RPG": [
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Baldur's Gate 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", "appid": 1086940},
        {"name": "The Witcher 3: Wild Hunt", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg", "appid": 292030},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "Persona 5 Royal", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1687950/header.jpg", "appid": 1687950},
        {"name": "Divinity: Original Sin 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/435150/header.jpg", "appid": 435150},
        {"name": "Dark Souls III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/374320/header.jpg", "appid": 374320},
        {"name": "Skyrim Special Edition", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/489830/header.jpg", "appid": 489830}
    ],
    "Strategy": [
        {"name": "Balatro", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", "appid": 2379780},
        {"name": "Slay the Spire", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/646570/header.jpg", "appid": 646570},
        {"name": "Sid Meier's Civilization VI", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/289070/header.jpg", "appid": 289070},
        {"name": "Stellaris", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/281990/header.jpg", "appid": 281990},
        {"name": "Manor Lords", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1363080/header.jpg", "appid": 1363080},
        {"name": "Against the Storm", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1336490/header.jpg", "appid": 1336490},
        {"name": "Hearts of Iron IV", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/394360/header.jpg", "appid": 394360},
        {"name": "DICEPTION", "imageUrl": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4429000/56bd8aa0cf2d865acbae5501824e33c4dd8c2269/header.jpg?t=1785770104", "appid": 4429000}
    ],
    "Adventure": [
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Outer Wilds", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/753640/header.jpg", "appid": 753640},
        {"name": "Stray", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1332010/header.jpg", "appid": 1332010},
        {"name": "Subnautica", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/264710/header.jpg", "appid": 264710},
        {"name": "TUNIC", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/553420/header.jpg", "appid": 553420},
        {"name": "Ori and the Will of the Wisps", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1057090/header.jpg", "appid": 1057090},
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600},
        {"name": "Sea of Thieves", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1172620/header.jpg", "appid": 1172620}
    ],
    "Simulation": [
        {"name": "Stardew Valley", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", "appid": 413150},
        {"name": "RimWorld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/294100/header.jpg", "appid": 294100},
        {"name": "Cities: Skylines", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/255710/header.jpg", "appid": 255710},
        {"name": "Euro Truck Simulator 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/227300/header.jpg", "appid": 227300},
        {"name": "Slime Rancher", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/433340/header.jpg", "appid": 433340},
        {"name": "Planet Coaster", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/493340/header.jpg", "appid": 493340},
        {"name": "Factorio", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/427520/header.jpg", "appid": 427520},
        {"name": "House Flipper", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/613100/header.jpg", "appid": 613100}
    ],
    "Casual": [
        {"name": "Dorfromantik", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1455840/header.jpg", "appid": 1455840},
        {"name": "Unpacking", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1058650/header.jpg", "appid": 1058650},
        {"name": "A Short Hike", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1055540/header.jpg", "appid": 1055540},
        {"name": "Peglin", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1296610/header.jpg", "appid": 1296610},
        {"name": "Townscaper", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1291340/header.jpg", "appid": 1291340},
        {"name": "Donut County", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/702670/header.jpg", "appid": 702670},
        {"name": "Untitled Goose Game", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/837470/header.jpg", "appid": 837470},
        {"name": "Sticky Business", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2303350/header.jpg", "appid": 2303350}
    ],
    "Indie": [
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Balatro", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", "appid": 2379780},
        {"name": "Celeste", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/504230/header.jpg", "appid": 504230},
        {"name": "Undertale", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/391540/header.jpg", "appid": 391540},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Vampire Survivors", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1794680/header.jpg", "appid": 1794680},
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600}
    ]
}

output_payload = {
    "generated_at": pd.Timestamp.now().isoformat(),
    "overall": overall_stats,
    "tiers": tier_benchmarks,
    "genres": genre_benchmarks,
    "presets": sample_presets,
    "genre_competitors": genre_competitor_catalogs
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2)

print(f"✅ Generated {OUTPUT_JSON} with {total_valid:,} records & {len(genre_benchmarks)} genre benchmarks.")
