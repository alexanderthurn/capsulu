#!/usr/bin/env python3
"""
export_benchmarks.py — Compile statistical benchmarks from clean, verified Steam games
(excluding error/corrupt records) into benchmarks.json, including Sales Tiers, Broad Genres,
and High-Interest Subcategories & Subgenres (Auto Battlers, Deckbuilders, Metroidvanias, etc.).
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

# 2. Comprehensive Genre & High-Interest Subcategory Definitions
tracked_categories = {
    # Sub-genres
    "Auto Battler": {
        "label": "Auto Battler / Auto Chess",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy|Simulation|Casual", case=False, regex=True)],
        "tip": "Auto Battlers require crisp unit silhouette contrast and distinct character color coding so armies are readable at small scale."
    },
    "Roguelike Deckbuilder": {
        "label": "Roguelike Deckbuilder / Card Game",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy|Indie", case=False, regex=True)],
        "tip": "High typographic contrast and bold card/rune iconography with warm accent glows create an addictive visual presence."
    },
    "Action Roguelike": {
        "label": "Action Roguelike / Survivors-like",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|Indie", case=False, regex=True)],
        "tip": "Punchy kinetic lighting with warm bursts (embers, lightning, magic) anchored by a prominent central protagonist."
    },
    "Metroidvania": {
        "label": "Metroidvania / 2D Platformer",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Adventure|Action|Indie", case=False, regex=True)],
        "tip": "Deep multi-plane atmospheric lighting and distinct silhouetted landscapes with rich textural depth."
    },
    "Souls-like": {
        "label": "Souls-like / Dark Fantasy",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("RPG|Action", case=False, regex=True)],
        "tip": "Deep chiaroscuro shadows with piercing key highlights (golden grace, bonfires, arcane glow) and monolithic scale."
    },
    "Survival Horror": {
        "label": "Survival Horror / Psychological",
        "filter_query": lambda d: d[(d["all_genres"].fillna("").str.contains("Action|Adventure", case=False, regex=True)) & (d["dark_ratio"] > 0.20)],
        "tip": "Heavy dark-ratio edge vignetting with isolated warm flashlight/crimson illumination on the threat subject."
    },
    "Cozy Sim": {
        "label": "Cozy & Farming Sim",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Simulation|Casual", case=False, regex=True)],
        "tip": "Vibrant, inviting color temperatures with warm golden hour tones and soft, welcoming character design."
    },
    "Turn-Based Tactics": {
        "label": "Turn-Based Tactics / Strategy",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy", case=False, regex=True)],
        "tip": "Clean isometric/grid clarity with deliberate edge line density and clear faction heraldry."
    },
    "City Builder": {
        "label": "City Builder / Colony Sim",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Simulation|Strategy", case=False, regex=True)],
        "tip": "Expansive landscape panoramas with rich structural edge density and natural environmental lighting."
    },
    "Retro FPS": {
        "label": "Boomer Shooter / Retro FPS",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action", case=False, regex=True)],
        "tip": "Saturated, aggressive color palettes with fiery contrast and high-velocity central focus."
    },
    # Broad Genres
    "Action": {
        "label": "Action / Shooter / Hack & Slash",
        "filter_query": lambda d: d[(d["primary_genre"] == "Action") | d["all_genres"].fillna("").str.contains("Action", case=False, regex=False)],
        "tip": "High dynamic lighting and warm rim-lighting are critical to pop against fast-paced Steam browse feeds."
    },
    "Adventure": {
        "label": "Adventure / Narrative / Exploration",
        "filter_query": lambda d: d[(d["primary_genre"] == "Adventure") | d["all_genres"].fillna("").str.contains("Adventure", case=False, regex=False)],
        "tip": "Atmospheric lighting with high tonal entropy and clear environmental depth performs best."
    },
    "RPG": {
        "label": "RPG / CRPG / JRPG",
        "filter_query": lambda d: d[(d["primary_genre"] == "RPG") | d["all_genres"].fillna("").str.contains("RPG", case=False, regex=False)],
        "tip": "Deep textural richness and unobstructed character silhouettes with prominent title branding."
    },
    "Strategy": {
        "label": "Strategy / Grand Strategy / Tactics",
        "filter_query": lambda d: d[(d["primary_genre"] == "Strategy") | d["all_genres"].fillna("").str.contains("Strategy", case=False, regex=False)],
        "tip": "Sharp typographic contrast and distinct iconography. Avoid oversaturated neon washes."
    },
    "Simulation": {
        "label": "Simulation / Management / Sandbox",
        "filter_query": lambda d: d[(d["primary_genre"] == "Simulation") | d["all_genres"].fillna("").str.contains("Simulation", case=False, regex=False)],
        "tip": "Balanced, inviting color temperatures with crisp line art and clear theme cues."
    },
    "Casual": {
        "label": "Casual / Puzzle / Cozy",
        "filter_query": lambda d: d[(d["primary_genre"] == "Casual") | d["all_genres"].fillna("").str.contains("Casual", case=False, regex=False)],
        "tip": "Vibrant, cheerful color palettes with higher average brightness and clean geometric shapes."
    },
    "Indie": {
        "label": "Indie Highlights",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Indie", case=False, regex=False)],
        "tip": "Distinct stylized visual identity with strong hero focus to stand out from AAA realism."
    }
}

genre_benchmarks = {}

for g_key, g_meta in tracked_categories.items():
    sub = g_meta["filter_query"](clean_df)
    n = len(sub)
    if n < 10:
        continue

    # Get top performers in this category
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

# 4. Curated sample presets
sample_presets = [
    {
        "id": "diception",
        "name": "DICEPTION",
        "appid": 4429000,
        "tier": "custom",
        "tier_label": "🎲 DICEPTION",
        "image_url": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4429000/56bd8aa0cf2d865acbae5501824e33c4dd8c2269/header.jpg?t=1785770104",
        "price": "4,99€",
        "tags": ["Indie", "Strategy", "Auto Battler", "Roguelike Deckbuilder"]
    },
    {
        "id": "melodan",
        "name": "Melodan",
        "appid": 4987230,
        "tier": "custom",
        "tier_label": "⚔️ Melodan",
        "image_url": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4987230/833a1d7f3a40629d6c8edd334ad871425ccd644b/header.jpg?t=1786736037",
        "price": "Coming Soon",
        "tags": ["Auto Battler", "Action", "Indie", "Strategy", "Turn-Based Tactics"]
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
        "tags": ["Farming Sim", "Cozy Sim", "Simulation", "Pixel Graphics"]
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
    }
]

# 5. Genre & Subcategory competitor catalogs for dynamic 3x3 simulator
genre_competitor_catalogs = {
    "Auto Battler": [
        {"name": "Backpack Battles", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2427700/header.jpg", "appid": 2427700},
        {"name": "Mechabellum", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/983870/header.jpg", "appid": 983870},
        {"name": "Super Auto Pets", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1714040/header.jpg", "appid": 1714040},
        {"name": "Despot's Game", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1399700/header.jpg", "appid": 1399700},
        {"name": "Legion TD 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/469600/header.jpg", "appid": 469600},
        {"name": "Slice & Dice", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1875880/header.jpg", "appid": 1875880},
        {"name": "Melodan", "imageUrl": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4987230/833a1d7f3a40629d6c8edd334ad871425ccd644b/header.jpg?t=1786736037", "appid": 4987230},
        {"name": "DICEPTION", "imageUrl": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4429000/56bd8aa0cf2d865acbae5501824e33c4dd8c2269/header.jpg?t=1785770104", "appid": 4429000}
    ],
    "Roguelike Deckbuilder": [
        {"name": "Balatro", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", "appid": 2379780},
        {"name": "Slay the Spire", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/646570/header.jpg", "appid": 646570},
        {"name": "Monster Train", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1102190/header.jpg", "appid": 1102190},
        {"name": "Inscryption", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1092790/header.jpg", "appid": 1092790},
        {"name": "Wildfrost", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1811990/header.jpg", "appid": 1811990},
        {"name": "Across the Obelisk", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1385380/header.jpg", "appid": 1385380},
        {"name": "Peglin", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1296610/header.jpg", "appid": 1296610},
        {"name": "Cobalt Core", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2179850/header.jpg", "appid": 2179850}
    ],
    "Action Roguelike": [
        {"name": "Vampire Survivors", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1794680/header.jpg", "appid": 1794680},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Risk of Rain 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632360/header.jpg", "appid": 632360},
        {"name": "Brotato", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1942280/header.jpg", "appid": 1942280},
        {"name": "Death Must Die", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2334730/header.jpg", "appid": 2334730},
        {"name": "20 Minutes Till Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1966900/header.jpg", "appid": 1966900},
        {"name": "Enter the Gungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/311690/header.jpg", "appid": 311690}
    ],
    "Metroidvania": [
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Ori and the Will of the Wisps", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1057090/header.jpg", "appid": 1057090},
        {"name": "Blasphemous 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2114740/header.jpg", "appid": 2114740},
        {"name": "Nine Sols", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1809540/header.jpg", "appid": 1809540},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Bloodstained: Ritual of the Night", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/692850/header.jpg", "appid": 692850},
        {"name": "Animal Well", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/813230/header.jpg", "appid": 813230},
        {"name": "Ender Lilies", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1368030/header.jpg", "appid": 1368030}
    ],
    "Souls-like": [
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Dark Souls III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/374320/header.jpg", "appid": 374320},
        {"name": "Lies of P", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1627720/header.jpg", "appid": 1627720},
        {"name": "Lords of the Fallen", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1501750/header.jpg", "appid": 1501750},
        {"name": "Remnant II", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1282100/header.jpg", "appid": 1282100},
        {"name": "Nioh 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1326470/header.jpg", "appid": 1326470},
        {"name": "Sekiro: Shadows Die Twice", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/814380/header.jpg", "appid": 814380},
        {"name": "Black Myth: Wukong", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2358720/header.jpg", "appid": 2358720}
    ],
    "Survival Horror": [
        {"name": "Resident Evil 4", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2050650/header.jpg", "appid": 2050650},
        {"name": "Dead Space", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1693980/header.jpg", "appid": 1693980},
        {"name": "Phasmophobia", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/739630/header.jpg", "appid": 739630},
        {"name": "Lethal Company", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1966720/header.jpg", "appid": 1966720},
        {"name": "Sons of the Forest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1326470/header.jpg", "appid": 1326470},
        {"name": "Outlast", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/238320/header.jpg", "appid": 238320},
        {"name": "Signalis", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1262350/header.jpg", "appid": 1262350},
        {"name": "Alan Wake 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2427700/header.jpg", "appid": 2427700}
    ],
    "Cozy Sim": [
        {"name": "Stardew Valley", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", "appid": 413150},
        {"name": "Slime Rancher", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/433340/header.jpg", "appid": 433340},
        {"name": "Dave the Diver", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1868140/header.jpg", "appid": 1868140},
        {"name": "Coral Island", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1158160/header.jpg", "appid": 1158160},
        {"name": "Sun Haven", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1434910/header.jpg", "appid": 1434910},
        {"name": "Roots of Pacha", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245590/header.jpg", "appid": 1245590},
        {"name": "Fae Farm", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2230110/header.jpg", "appid": 2230110},
        {"name": "Fields of Mistria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2142790/header.jpg", "appid": 2142790}
    ],
    "Turn-Based Tactics": [
        {"name": "Into the Breach", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/590380/header.jpg", "appid": 590380},
        {"name": "Wartales", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1527950/header.jpg", "appid": 1527950},
        {"name": "Tactics Ogre: Reborn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1451040/header.jpg", "appid": 1451040},
        {"name": "Marvel's Midnight Suns", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/368260/header.jpg", "appid": 368260},
        {"name": "Songs of Conquest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/867210/header.jpg", "appid": 867210},
        {"name": "Battle Brothers", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/365360/header.jpg", "appid": 365360},
        {"name": "Triangle Strategy", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1850510/header.jpg", "appid": 1850510},
        {"name": "XCOM 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/268500/header.jpg", "appid": 268500}
    ],
    "City Builder": [
        {"name": "Manor Lords", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1363080/header.jpg", "appid": 1363080},
        {"name": "Cities: Skylines", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/255710/header.jpg", "appid": 255710},
        {"name": "RimWorld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/294100/header.jpg", "appid": 294100},
        {"name": "Frostpunk", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/323190/header.jpg", "appid": 323190},
        {"name": "Against the Storm", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1336490/header.jpg", "appid": 1336490},
        {"name": "Workers & Resources", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/784150/header.jpg", "appid": 784150},
        {"name": "Timberborn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1062090/header.jpg", "appid": 1062090},
        {"name": "Farthest Frontier", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1044720/header.jpg", "appid": 1044720}
    ],
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

print(f"✅ Generated {OUTPUT_JSON} with {total_valid:,} records & {len(genre_benchmarks)} category/subgenre benchmarks.")
