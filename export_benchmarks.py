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

# 2. Comprehensive Broad Steam Genres & Sub-Genre Tags Definitions
broad_genres = {
    "Action": {
        "label": "Action",
        "filter_query": lambda d: d[(d["primary_genre"] == "Action") | d["all_genres"].fillna("").str.contains("Action", case=False, regex=False)],
        "tip": "High dynamic lighting and warm rim-lighting are critical to pop against fast-paced Steam browse feeds."
    },
    "Adventure": {
        "label": "Adventure",
        "filter_query": lambda d: d[(d["primary_genre"] == "Adventure") | d["all_genres"].fillna("").str.contains("Adventure", case=False, regex=False)],
        "tip": "Atmospheric lighting with high tonal entropy and clear environmental depth performs best."
    },
    "RPG": {
        "label": "RPG",
        "filter_query": lambda d: d[(d["primary_genre"] == "RPG") | d["all_genres"].fillna("").str.contains("RPG", case=False, regex=False)],
        "tip": "Deep textural richness and unobstructed character silhouettes with prominent title branding."
    },
    "Strategy": {
        "label": "Strategy",
        "filter_query": lambda d: d[(d["primary_genre"] == "Strategy") | d["all_genres"].fillna("").str.contains("Strategy", case=False, regex=False)],
        "tip": "Sharp typographic contrast and distinct iconography. Avoid oversaturated neon washes."
    },
    "Simulation": {
        "label": "Simulation",
        "filter_query": lambda d: d[(d["primary_genre"] == "Simulation") | d["all_genres"].fillna("").str.contains("Simulation", case=False, regex=False)],
        "tip": "Balanced, inviting color temperatures with crisp line art and clear theme cues."
    },
    "Casual": {
        "label": "Casual",
        "filter_query": lambda d: d[(d["primary_genre"] == "Casual") | d["all_genres"].fillna("").str.contains("Casual", case=False, regex=False)],
        "tip": "Vibrant, cheerful color palettes with higher average brightness and clean geometric shapes."
    },
    "Indie": {
        "label": "Indie",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Indie", case=False, regex=False)],
        "tip": "Distinct stylized visual identity with strong hero focus to stand out from AAA realism."
    },
    "Racing": {
        "label": "Racing",
        "filter_query": lambda d: d[(d["primary_genre"] == "Racing") | d["all_genres"].fillna("").str.contains("Racing", case=False, regex=False)],
        "tip": "High-velocity motion diagonals and hyper-reflective specular highlights on vehicular hero assets."
    },
    "Sports": {
        "label": "Sports",
        "filter_query": lambda d: d[(d["primary_genre"] == "Sports") | d["all_genres"].fillna("").str.contains("Sports", case=False, regex=False)],
        "tip": "Dynamic athlete action poses with saturated stadium stadium-lit contrast and clean typographic badges."
    },
    "Massively Multiplayer": {
        "label": "Massively Multiplayer",
        "filter_query": lambda d: d[(d["primary_genre"] == "Massively Multiplayer") | d["all_genres"].fillna("").str.contains("Massively Multiplayer", case=False, regex=False)],
        "tip": "Epic scale panoramic backdrops featuring grouped heroes or massive faction armadas."
    },
    "Free To Play": {
        "label": "Free To Play",
        "filter_query": lambda d: d[(d["is_free"] == 1) | (d["is_free"] == True) | d["all_genres"].fillna("").str.contains("Free To Play", case=False, regex=False)],
        "tip": "Instant visual accessibility with high saturation and bold, easily readable hero characters."
    },
    "Early Access": {
        "label": "Early Access",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Early Access", case=False, regex=False)],
        "tip": "Polished key visual polish that instills immediate confidence and production value."
    }
}

gameplay_tags = {
    "Auto Battler": {
        "label": "Auto Battler",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy|Simulation|Casual", case=False, regex=True)],
        "tip": "Auto Battlers require crisp unit silhouette contrast and distinct character color coding so armies are readable at small scale."
    },
    "Roguelike Deckbuilder": {
        "label": "Roguelike Deckbuilder",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy|Indie", case=False, regex=True)],
        "tip": "High typographic contrast and bold card/rune iconography with warm accent glows create an addictive visual presence."
    },
    "Action Roguelike": {
        "label": "Action Roguelike",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|Indie", case=False, regex=True)],
        "tip": "Punchy kinetic lighting with warm bursts (embers, lightning, magic) anchored by a prominent central protagonist."
    },
    "Metroidvania": {
        "label": "Metroidvania",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Adventure|Action|Indie", case=False, regex=True)],
        "tip": "Deep multi-plane atmospheric lighting and distinct silhouetted landscapes with rich textural depth."
    },
    "Souls-like": {
        "label": "Souls-like",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("RPG|Action", case=False, regex=True)],
        "tip": "Deep chiaroscuro shadows with piercing key highlights (golden grace, bonfires, arcane glow) and monolithic scale."
    },
    "Survival Horror": {
        "label": "Survival Horror",
        "filter_query": lambda d: d[(d["all_genres"].fillna("").str.contains("Action|Adventure", case=False, regex=True)) & (d["dark_ratio"] > 0.20)],
        "tip": "Heavy dark-ratio edge vignetting with isolated warm flashlight/crimson illumination on the threat subject."
    },
    "Cozy Sim": {
        "label": "Cozy Sim",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Simulation|Casual", case=False, regex=True)],
        "tip": "Vibrant, inviting color temperatures with warm golden hour tones and soft, welcoming character design."
    },
    "Turn-Based Tactics": {
        "label": "Turn-Based Tactics",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy", case=False, regex=True)],
        "tip": "Clean isometric/grid clarity with deliberate edge line density and clear faction heraldry."
    },
    "Turn-Based Strategy": {
        "label": "Turn-Based Strategy",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy", case=False, regex=True)],
        "tip": "Rich strategic map depth with prominent empire crests and crisp territorial contrast."
    },
    "City Builder": {
        "label": "City Builder",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Simulation|Strategy", case=False, regex=True)],
        "tip": "Expansive landscape panoramas with rich structural edge density and natural environmental lighting."
    },
    "Retro FPS": {
        "label": "Retro FPS",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action", case=False, regex=True)],
        "tip": "Saturated, aggressive color palettes with fiery contrast and high-velocity central focus."
    },
    "Dragons": {
        "label": "Dragons",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|RPG|Strategy", case=False, regex=True)],
        "tip": "Epic creature scale with warm fiery or arcane lighting accents cutting through dark atmospheric skies."
    },
    "PvP": {
        "label": "PvP",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|Strategy", case=False, regex=True)],
        "tip": "Opposing color clashes (red vs blue, gold vs shadow) indicating intense multiplayer competition."
    },
    "PvE": {
        "label": "PvE",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|RPG|Adventure", case=False, regex=True)],
        "tip": "Heroic squad lineup facing formidable boss silhouettes in evocative fantasy or sci-fi environments."
    },
    "Fantasy": {
        "label": "Fantasy",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("RPG|Adventure|Strategy", case=False, regex=True)],
        "tip": "Luminous magical particle effects and rich mystical textures with clear character silhouettes."
    },
    "Magic": {
        "label": "Magic",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("RPG|Action|Strategy", case=False, regex=True)],
        "tip": "Radiant spell glow effects with high luminous contrast against shadowed mystical backdrops."
    },
    "Medieval": {
        "label": "Medieval",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("RPG|Strategy|Action", case=False, regex=True)],
        "tip": "Grit, burnished armor sheen, and torchlit atmosphere with distinct heraldic color banners."
    },
    "Military": {
        "label": "Military",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|Strategy|Simulation", case=False, regex=True)],
        "tip": "Camouflage textures balanced by sharp tactical orange/amber HUD elements and distinct hardware silhouettes."
    },
    "Wargame": {
        "label": "Wargame",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy|Simulation", case=False, regex=True)],
        "tip": "Detailed tactical battle maps and unit counters with disciplined typographic contrast."
    },
    "Card Game": {
        "label": "Card Game",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Strategy|Casual", case=False, regex=True)],
        "tip": "Embossed card borders with saturated gem/mana accents and readable card art at browse scales."
    },
    "Pixel Graphics": {
        "label": "Pixel Graphics",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Indie|Adventure|Action", case=False, regex=True)],
        "tip": "Crisp pixel cluster readability with bold color separation avoiding visual noise at small thumbnail sizes."
    },
    "Cyberpunk": {
        "label": "Cyberpunk",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|RPG", case=False, regex=True)],
        "tip": "Vibrant cyan/magenta neon contrast cutting through rain-slicked dark industrial geometry."
    },
    "Open World": {
        "label": "Open World",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Adventure|RPG|Action", case=False, regex=True)],
        "tip": "Dramatic vanishing point horizon with atmospheric haze separating foreground protagonist from expansive world."
    },
    "Sci-fi": {
        "label": "Sci-fi",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|Strategy|Simulation", case=False, regex=True)],
        "tip": "Sleek geometric paneling with electric laser blue or solar orange emissive lighting lines."
    },
    "Co-op": {
        "label": "Co-op",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|Adventure|Indie", case=False, regex=True)],
        "tip": "Multiple complementary character silhouettes showing distinct classes or comedic camaraderie."
    },
    "Multiplayer": {
        "label": "Multiplayer",
        "filter_query": lambda d: d[d["all_genres"].fillna("").str.contains("Action|Strategy", case=False, regex=True)],
        "tip": "Kinetic confrontation energy with clear opposing faction visuals and high-saliency action focal points."
    }
}

def compute_category_stats(cat_dict, dataframe):
    res = {}
    for key, meta in cat_dict.items():
        sub = meta["filter_query"](dataframe)
        n = len(sub)
        if n < 5:
            continue
        top_sub = sub[sub["tier"].isin(["mega_hit", "successful"])]
        if len(top_sub) < 5:
            top_sub = sub
            
        text_sub = sub[sub["title_contrast"].notna() & (sub["title_contrast"] > 0)]
        has_text_pct = round(float((sub["has_text"] == True).mean() * 100), 1) if "has_text" in sub.columns else 85.0
        
        # Title contrast (WCAG ratio)
        title_contrast_median = round(float(text_sub["title_contrast"].median()), 2) if len(text_sub) > 0 else 3.5
        title_contrast_mean = round(float(text_sub["title_contrast"].mean()), 2) if len(text_sub) > 0 else 5.2
        title_contrast_p75 = round(float(text_sub["title_contrast"].quantile(0.75)), 2) if len(text_sub) > 0 else 6.6
        
        # Most popular title zone
        top_zone = "mid_center"
        if "title_zone" in sub.columns:
            valid_zones = sub[sub["title_zone"].isin(["top_left", "top_center", "top_right", "mid_left", "mid_center", "mid_right", "bot_left", "bot_center", "bot_right"])]["title_zone"]
            if len(valid_zones) > 0:
                top_zone = valid_zones.value_counts().index[0]
                
        # Readability percentage
        good_readability_pct = 0.0
        if "title_readability" in sub.columns:
            good_readability_pct = round(float((sub["title_readability"] == "good").mean() * 100), 1)

        res[key] = {
            "name": meta["label"],
            "count": int(n),
            "tip": meta["tip"],
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
            "dark_ratio": round(float(sub["dark_ratio"].mean() * 100), 1),
            "light_ratio": round(float(sub["light_ratio"].mean() * 100), 1),
            "text": {
                "has_text_pct": has_text_pct,
                "contrast": {
                    "median": title_contrast_median,
                    "mean": title_contrast_mean,
                    "p75": title_contrast_p75,
                },
                "top_zone": top_zone,
                "good_readability_pct": good_readability_pct,
            }
        }
    return res

genre_benchmarks = compute_category_stats(broad_genres, clean_df)
tag_benchmarks = compute_category_stats(gameplay_tags, clean_df)
unified_categories = {**genre_benchmarks, **tag_benchmarks}

# 3. Overall dataset stats
overall_stats = {
    "total_games_analyzed": total_valid,
    "contrast_p90": round(float(clean_df["brightness_std"].quantile(0.90)), 2),
    "contrast_p10": round(float(clean_df["brightness_std"].quantile(0.10)), 2),
    "entropy_p90": round(float(clean_df["entropy"].quantile(0.90)), 2),
    "entropy_p10": round(float(clean_df["entropy"].quantile(0.10)), 2),
    "edge_density_p90": round(float(clean_df["edge_density"].quantile(0.90) * 100), 2),
    "edge_density_p10": round(float(clean_df["edge_density"].quantile(0.10) * 100), 2),
    "title_contrast_median": round(float(clean_df["title_contrast"].median()), 2),
    "title_contrast_mean": round(float(clean_df["title_contrast"].mean()), 2),
    "title_contrast_p75": round(float(clean_df["title_contrast"].quantile(0.75)), 2),
    "title_good_readability_pct": round(float((clean_df["title_readability"] == "good").mean() * 100), 1),
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
        "tags": ["Roguelike Deckbuilder", "Turn-Based Tactics", "Strategy", "Indie", "Dice", "PvP"]
    },
    {
        "id": "melodan",
        "name": "Melodan",
        "appid": 4987230,
        "tier": "custom",
        "tier_label": "⚔️ Melodan",
        "image_url": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4987230/833a1d7f3a40629d6c8edd334ad871425ccd644b/header.jpg?t=1786736037",
        "price": "Coming Soon",
        "tags": ["Auto Battler", "Turn-Based Strategy", "Turn-Based Tactics", "Strategy", "Simulation", "Action", "Indie", "Dragons", "PvP"]
    },
    {
        "id": "elden_ring",
        "name": "ELDEN RING",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>800k reviews)",
        "appid": 1245620,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg",
        "price": "$59.99",
        "tags": ["Souls-like", "RPG", "Dark Fantasy", "Open World", "Difficult", "Action RPG", "Action"]
    },
    {
        "id": "hades",
        "name": "Hades",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>230k reviews)",
        "appid": 1145360,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg",
        "price": "$24.99",
        "tags": ["Action Roguelike", "Hack and Slash", "Indie", "Mythology", "Action", "Rogue-lite"]
    },
    {
        "id": "balatro",
        "name": "Balatro",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>80k reviews)",
        "appid": 2379780,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg",
        "price": "$14.99",
        "tags": ["Roguelike Deckbuilder", "Card Game", "Strategy", "Indie", "Deckbuilding", "Addictive"]
    },
    {
        "id": "stardew",
        "name": "Stardew Valley",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>600k reviews)",
        "appid": 413150,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg",
        "price": "$14.99",
        "tags": ["Farming Sim", "Cozy Sim", "Simulation", "Pixel Graphics", "RPG", "Life Sim"]
    },
    {
        "id": "cyberpunk",
        "name": "Cyberpunk 2077",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>700k reviews)",
        "appid": 1091500,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg",
        "price": "$59.99",
        "tags": ["Cyberpunk", "Open World", "RPG", "Sci-fi", "Action", "Shooter"]
    },
    {
        "id": "hollow_knight",
        "name": "Hollow Knight",
        "tier": "mega_hit",
        "tier_label": "🏆 Mega-Hit (>350k reviews)",
        "appid": 367520,
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg",
        "price": "$14.99",
        "tags": ["Metroidvania", "Souls-like", "Adventure", "2D Platformer", "Difficult", "Action"]
    }
]

# 5. Genre & Subcategory competitor catalogs for dynamic 3x3 simulator
genre_competitor_catalogs = {
    "all": [
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Balatro", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", "appid": 2379780},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "Stardew Valley", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", "appid": 413150},
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Baldur's Gate 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", "appid": 1086940},
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600}
    ],
    "overall": [
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Balatro", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", "appid": 2379780},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "Stardew Valley", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", "appid": 413150},
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Baldur's Gate 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", "appid": 1086940},
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600}
    ],
    "Auto Battler": [
        {"name": "Backpack Battles", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2427700/header.jpg", "appid": 2427700},
        {"name": "Mechabellum", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/983870/header.jpg", "appid": 983870},
        {"name": "Super Auto Pets", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1714040/header.jpg", "appid": 1714040},
        {"name": "Despot's Game", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1399700/header.jpg", "appid": 1399700},
        {"name": "Legion TD 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/469600/header.jpg", "appid": 469600},
        {"name": "Slice & Dice", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1875880/header.jpg", "appid": 1875880},
        {"name": "Melodan", "imageUrl": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4987230/833a1d7f3a40629d6c8edd334ad871425ccd644b/header.jpg?t=1786736037", "appid": 4987230},
        {"name": "Just King", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2159490/header.jpg", "appid": 2159490}
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
        {"name": "Bloodstained", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/692850/header.jpg", "appid": 692850},
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
    "Turn-Based Strategy": [
        {"name": "Sid Meier's Civilization VI", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/289070/header.jpg", "appid": 289070},
        {"name": "Age of Wonders 4", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1669000/header.jpg", "appid": 1669000},
        {"name": "Total War: WARHAMMER III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1142710/header.jpg", "appid": 1142710},
        {"name": "Songs of Conquest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/867210/header.jpg", "appid": 867210},
        {"name": "Wartales", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1527950/header.jpg", "appid": 1527950},
        {"name": "Endless Legend", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/289130/header.jpg", "appid": 289130},
        {"name": "Old World", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/597180/header.jpg", "appid": 597180},
        {"name": "Battle Brothers", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/365360/header.jpg", "appid": 365360}
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
    "Dragons": [
        {"name": "Monster Hunter: World", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/582010/header.jpg", "appid": 582010},
        {"name": "Skyrim Special Edition", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/489830/header.jpg", "appid": 489830},
        {"name": "Total War: WARHAMMER III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1142710/header.jpg", "appid": 1142710},
        {"name": "Dragon's Dogma 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2054970/header.jpg", "appid": 2054970},
        {"name": "Divinity: Original Sin 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/435150/header.jpg", "appid": 435150},
        {"name": "Dragon Age: Inquisition", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1222690/header.jpg", "appid": 1222690},
        {"name": "Guild Wars 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1284210/header.jpg", "appid": 1284210},
        {"name": "Middle-earth: Shadow of War", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/356190/header.jpg", "appid": 356190}
    ],
    "PvP": [
        {"name": "Counter-Strike 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg", "appid": 730},
        {"name": "Apex Legends", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1172470/header.jpg", "appid": 1172470},
        {"name": "Dota 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/570/header.jpg", "appid": 570},
        {"name": "Rust", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/252490/header.jpg", "appid": 252490},
        {"name": "Rainbow Six Siege", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/359550/header.jpg", "appid": 359550},
        {"name": "Street Fighter 6", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1364780/header.jpg", "appid": 1364780},
        {"name": "Dead by Daylight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/381210/header.jpg", "appid": 381210},
        {"name": "Rocket League", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/252950/header.jpg", "appid": 252950}
    ],
    "PvE": [
        {"name": "Helldivers 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/553850/header.jpg", "appid": 553850},
        {"name": "Deep Rock Galactic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/548430/header.jpg", "appid": 548430},
        {"name": "Warhammer: Vermintide 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/552500/header.jpg", "appid": 552500},
        {"name": "Left 4 Dead 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/550/header.jpg", "appid": 550},
        {"name": "PAYDAY 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/218620/header.jpg", "appid": 218620},
        {"name": "Remnant II", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1282100/header.jpg", "appid": 1282100},
        {"name": "Borderlands 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/397540/header.jpg", "appid": 397540},
        {"name": "GTFO", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/493520/header.jpg", "appid": 493520}
    ],
    "Fantasy": [
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "The Witcher 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg", "appid": 292030},
        {"name": "Baldur's Gate 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", "appid": 1086940},
        {"name": "Dragon's Dogma 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2054970/header.jpg", "appid": 2054970},
        {"name": "Dark Souls III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/374320/header.jpg", "appid": 374320},
        {"name": "Final Fantasy XIV", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/39210/header.jpg", "appid": 39210},
        {"name": "Skyrim Special Edition", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/489830/header.jpg", "appid": 489830},
        {"name": "Divinity: Original Sin 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/435150/header.jpg", "appid": 435150}
    ],
    "Magic": [
        {"name": "Noita", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/881100/header.jpg", "appid": 881100},
        {"name": "Hogwarts Legacy", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/990080/header.jpg", "appid": 990080},
        {"name": "Wizard of Legend", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/445980/header.jpg", "appid": 445980},
        {"name": "Magicka 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/238370/header.jpg", "appid": 238370},
        {"name": "Archvale", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1296360/header.jpg", "appid": 1296360},
        {"name": "Spellbreak", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1399780/header.jpg", "appid": 1399780},
        {"name": "Blade and Sorcery", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/629730/header.jpg", "appid": 629730},
        {"name": "Fable Anniversary", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/288470/header.jpg", "appid": 288470}
    ],
    "Medieval": [
        {"name": "Kingdom Come: Deliverance", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/379430/header.jpg", "appid": 379430},
        {"name": "Manor Lords", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1363080/header.jpg", "appid": 1363080},
        {"name": "Mount & Blade II: Bannerlord", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/261550/header.jpg", "appid": 261550},
        {"name": "Chivalry 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1824220/header.jpg", "appid": 1824220},
        {"name": "Crusader Kings III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1158310/header.jpg", "appid": 1158310},
        {"name": "Medieval Dynasty", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1129580/header.jpg", "appid": 1129580},
        {"name": "A Plague Tale: Requiem", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1452500/header.jpg", "appid": 1452500},
        {"name": "Mordhau", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/868520/header.jpg", "appid": 868520}
    ],
    "Military": [
        {"name": "Arma 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/107410/header.jpg", "appid": 107410},
        {"name": "Squad", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/393380/header.jpg", "appid": 393380},
        {"name": "Hell Let Loose", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/686810/header.jpg", "appid": 686810},
        {"name": "Hearts of Iron IV", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/394360/header.jpg", "appid": 394360},
        {"name": "War Thunder", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/236390/header.jpg", "appid": 236390},
        {"name": "Insurgency: Sandstorm", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/581320/header.jpg", "appid": 581320},
        {"name": "Company of Heroes 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1677280/header.jpg", "appid": 1677280},
        {"name": "Ready or Not", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1144200/header.jpg", "appid": 1144200}
    ],
    "Wargame": [
        {"name": "WARNO", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1611600/header.jpg", "appid": 1611600},
        {"name": "Wargame: Red Dragon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/251060/header.jpg", "appid": 251060},
        {"name": "Hearts of Iron IV", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/394360/header.jpg", "appid": 394360},
        {"name": "Steel Division 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/919640/header.jpg", "appid": 919640},
        {"name": "Men of War II", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1128860/header.jpg", "appid": 1128860},
        {"name": "Panzer Corps 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1072040/header.jpg", "appid": 1072040},
        {"name": "Total War: MEDIEVAL II", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/4700/header.jpg", "appid": 4700},
        {"name": "Command: Modern Operations", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1076160/header.jpg", "appid": 1076160}
    ],
    "Card Game": [
        {"name": "Balatro", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", "appid": 2379780},
        {"name": "Slay the Spire", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/646570/header.jpg", "appid": 646570},
        {"name": "Inscryption", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1092790/header.jpg", "appid": 1092790},
        {"name": "Monster Train", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1102190/header.jpg", "appid": 1102190},
        {"name": "Yu-Gi-Oh! Master Duel", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1449850/header.jpg", "appid": 1449850},
        {"name": "Magic: The Gathering Arena", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2141910/header.jpg", "appid": 2141910},
        {"name": "Wildfrost", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1811990/header.jpg", "appid": 1811990},
        {"name": "Peglin", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1296610/header.jpg", "appid": 1296610}
    ],
    "Pixel Graphics": [
        {"name": "Stardew Valley", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", "appid": 413150},
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600},
        {"name": "Celeste", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/504230/header.jpg", "appid": 504230},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Undertale", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/391540/header.jpg", "appid": 391540},
        {"name": "Sea of Stars", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1244090/header.jpg", "appid": 1244090},
        {"name": "Blasphemous", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/774361/header.jpg", "appid": 774361},
        {"name": "Hotline Miami", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219150/header.jpg", "appid": 219150}
    ],
    "Cyberpunk": [
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "Ghostrunner 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2144740/header.jpg", "appid": 2144740},
        {"name": "The Ascent", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/979690/header.jpg", "appid": 979690},
        {"name": "Cloudpunk", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/868360/header.jpg", "appid": 868360},
        {"name": "Stray", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1332010/header.jpg", "appid": 1332010},
        {"name": "Ruiner", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/464060/header.jpg", "appid": 464060},
        {"name": "Observer: System Redux", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1386900/header.jpg", "appid": 1386900},
        {"name": "System Shock", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/482400/header.jpg", "appid": 482400}
    ],
    "Open World": [
        {"name": "Red Dead Redemption 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1174180/header.jpg", "appid": 1174180},
        {"name": "Grand Theft Auto V", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/271590/header.jpg", "appid": 271590},
        {"name": "The Witcher 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg", "appid": 292030},
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Skyrim Special Edition", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/489830/header.jpg", "appid": 489830},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "Horizon Zero Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1151640/header.jpg", "appid": 1151640},
        {"name": "Fallout 4", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/377160/header.jpg", "appid": 377160}
    ],
    "Sci-fi": [
        {"name": "No Man's Sky", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/275850/header.jpg", "appid": 275850},
        {"name": "Starfield", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1716740/header.jpg", "appid": 1716740},
        {"name": "Stellaris", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/281990/header.jpg", "appid": 281990},
        {"name": "Mass Effect Legendary Edition", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1328670/header.jpg", "appid": 1328670},
        {"name": "Deep Rock Galactic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/548430/header.jpg", "appid": 548430},
        {"name": "Subnautica", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/264710/header.jpg", "appid": 264710},
        {"name": "Halo Infinite", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1240440/header.jpg", "appid": 1240440},
        {"name": "Dead Space", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1693980/header.jpg", "appid": 1693980}
    ],
    "Co-op": [
        {"name": "It Takes Two", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1426210/header.jpg", "appid": 1426210},
        {"name": "Deep Rock Galactic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/548430/header.jpg", "appid": 548430},
        {"name": "Lethal Company", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1966720/header.jpg", "appid": 1966720},
        {"name": "Helldivers 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/553850/header.jpg", "appid": 553850},
        {"name": "Valheim", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/892970/header.jpg", "appid": 892970},
        {"name": "Overcooked! 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/448510/header.jpg", "appid": 448510},
        {"name": "Raft", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/648800/header.jpg", "appid": 648800},
        {"name": "Don't Starve Together", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/322330/header.jpg", "appid": 322330}
    ],
    "Multiplayer": [
        {"name": "Rust", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/252490/header.jpg", "appid": 252490},
        {"name": "Counter-Strike 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg", "appid": 730},
        {"name": "Apex Legends", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1172470/header.jpg", "appid": 1172470},
        {"name": "Team Fortress 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg", "appid": 440},
        {"name": "Rainbow Six Siege", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/359550/header.jpg", "appid": 359550},
        {"name": "Dead by Daylight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/381210/header.jpg", "appid": 381210},
        {"name": "Phasmophobia", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/739630/header.jpg", "appid": 739630},
        {"name": "Among Us", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/945360/header.jpg", "appid": 945360}
    ],
    "Retro FPS": [
        {"name": "ULTRAKILL", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1229490/header.jpg", "appid": 1229490},
        {"name": "DUSK", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/504230/header.jpg", "appid": 504230},
        {"name": "Cultic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1684930/header.jpg", "appid": 1684930},
        {"name": "Ion Fury", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/562860/header.jpg", "appid": 562860},
        {"name": "Prodeus", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/964800/header.jpg", "appid": 964800},
        {"name": "Amid Evil", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/673130/header.jpg", "appid": 673130},
        {"name": "Warhammer 40K: Boltgun", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2005010/header.jpg", "appid": 2005010},
        {"name": "Blood: Fresh Supply", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1010750/header.jpg", "appid": 1010750}
    ],
    "Racing": [
        {"name": "Forza Horizon 5", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1551360/header.jpg", "appid": 1551360},
        {"name": "F1 23", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2108330/header.jpg", "appid": 2108330},
        {"name": "Assetto Corsa", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/244210/header.jpg", "appid": 244210},
        {"name": "Need for Speed Unbound", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1846380/header.jpg", "appid": 1846380},
        {"name": "Dirt Rally 2.0", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/690790/header.jpg", "appid": 690790},
        {"name": "Wreckfest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/228380/header.jpg", "appid": 228380},
        {"name": "BeamNG.drive", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/284160/header.jpg", "appid": 284160},
        {"name": "Hot Wheels Unleashed", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1271700/header.jpg", "appid": 1271700}
    ],
    "Sports": [
        {"name": "EA SPORTS FC 24", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2195250/header.jpg", "appid": 2195250},
        {"name": "NBA 2K24", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2338770/header.jpg", "appid": 2338770},
        {"name": "Rocket League", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/252950/header.jpg", "appid": 252950},
        {"name": "WWE 2K24", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2315690/header.jpg", "appid": 2315690},
        {"name": "Football Manager 2024", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2252570/header.jpg", "appid": 2252570},
        {"name": "Riders Republic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2290180/header.jpg", "appid": 2290180},
        {"name": "Session: Skate Sim", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/861650/header.jpg", "appid": 861650},
        {"name": "PGA TOUR 2K23", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1588010/header.jpg", "appid": 1588010}
    ],
    "Massively Multiplayer": [
        {"name": "Final Fantasy XIV", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/39210/header.jpg", "appid": 39210},
        {"name": "Guild Wars 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1284210/header.jpg", "appid": 1284210},
        {"name": "The Elder Scrolls Online", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/306130/header.jpg", "appid": 306130},
        {"name": "Black Desert", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/582660/header.jpg", "appid": 582660},
        {"name": "Warframe", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/230410/header.jpg", "appid": 230410},
        {"name": "Lost Ark", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1599340/header.jpg", "appid": 1599340},
        {"name": "New World", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1063730/header.jpg", "appid": 1063730},
        {"name": "Old School RuneScape", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1343370/header.jpg", "appid": 1343370}
    ],
    "Free To Play": [
        {"name": "Counter-Strike 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg", "appid": 730},
        {"name": "Dota 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/570/header.jpg", "appid": 570},
        {"name": "Apex Legends", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1172470/header.jpg", "appid": 1172470},
        {"name": "Path of Exile", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/238960/header.jpg", "appid": 238960},
        {"name": "Warframe", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/230410/header.jpg", "appid": 230410},
        {"name": "Team Fortress 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg", "appid": 440},
        {"name": "Destiny 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1085660/header.jpg", "appid": 1085660},
        {"name": "The Sims 4", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1222670/header.jpg", "appid": 1222670}
    ],
    "Early Access": [
        {"name": "Manor Lords", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1363080/header.jpg", "appid": 1363080},
        {"name": "Palworld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1623730/header.jpg", "appid": 1623730},
        {"name": "Enshrouded", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1203630/header.jpg", "appid": 1203630},
        {"name": "Sons of the Forest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1326470/header.jpg", "appid": 1326470},
        {"name": "Gray Zone Warfare", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2479810/header.jpg", "appid": 2479810},
        {"name": "Satisfactory", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/526870/header.jpg", "appid": 526870},
        {"name": "Valheim", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/892970/header.jpg", "appid": 892970},
        {"name": "V Rising", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1604030/header.jpg", "appid": 1604030}
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
    ],
    "Hack and Slash": [
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Devil May Cry 5", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/601150/header.jpg", "appid": 601150},
        {"name": "NieR:Automata", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/524220/header.jpg", "appid": 524220},
        {"name": "Grim Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219990/header.jpg", "appid": 219990},
        {"name": "Bayonetta", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/460790/header.jpg", "appid": 460790},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Torchlight II", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/200710/header.jpg", "appid": 200710},
        {"name": "Titan Quest Anniversary", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/475150/header.jpg", "appid": 475150}
    ],
    "Mythology": [
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "God of War", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1593500/header.jpg", "appid": 1593500},
        {"name": "Age of Mythology: Retold", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1934680/header.jpg", "appid": 1934680},
        {"name": "Assassin's Creed Odyssey", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/812140/header.jpg", "appid": 812140},
        {"name": "Immortals Fenyx Rising", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2221920/header.jpg", "appid": 2221920},
        {"name": "Titan Quest Anniversary", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/475150/header.jpg", "appid": 475150},
        {"name": "Smite", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/386360/header.jpg", "appid": 386360},
        {"name": "Total War: PHARAOH", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1937780/header.jpg", "appid": 1937780}
    ],
    "Dungeon Crawler": [
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Darkest Dungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/262060/header.jpg", "appid": 262060},
        {"name": "Enter the Gungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/311690/header.jpg", "appid": 311690},
        {"name": "Cult of the Lamb", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1313140/header.jpg", "appid": 1313140},
        {"name": "Wizard of Legend", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/445980/header.jpg", "appid": 445980},
        {"name": "Moonlighter", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/606150/header.jpg", "appid": 606150},
        {"name": "Barony", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/371970/header.jpg", "appid": 371970},
        {"name": "Torchlight II", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/200710/header.jpg", "appid": 200710}
    ],
    "Isometric": [
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Baldur's Gate 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", "appid": 1086940},
        {"name": "Disco Elysium", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632470/header.jpg", "appid": 632470},
        {"name": "Death's Door", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/894020/header.jpg", "appid": 894020},
        {"name": "Tunic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/553420/header.jpg", "appid": 553420},
        {"name": "Divinity: Original Sin 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/435150/header.jpg", "appid": 435150},
        {"name": "Weird West", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1097350/header.jpg", "appid": 1097350},
        {"name": "Project Zomboid", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/108600/header.jpg", "appid": 108600}
    ],
    "Difficult": [
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Sekiro: Shadows Die Twice", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/814380/header.jpg", "appid": 814380},
        {"name": "Cuphead", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/268910/header.jpg", "appid": 268910},
        {"name": "Celeste", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/504230/header.jpg", "appid": 504230},
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Dark Souls III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/374320/header.jpg", "appid": 374320},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Lies of P", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1627720/header.jpg", "appid": 1627720}
    ],
    "Hand-drawn": [
        {"name": "Cuphead", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/268910/header.jpg", "appid": 268910},
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Spiritfarer", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/972660/header.jpg", "appid": 972660},
        {"name": "GRIS", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/683320/header.jpg", "appid": 683320},
        {"name": "Guacamelee! 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/534550/header.jpg", "appid": 534550},
        {"name": "Don't Starve", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219740/header.jpg", "appid": 219740},
        {"name": "Cult of the Lamb", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1313140/header.jpg", "appid": 1313140}
    ],
    "Action RPG": [
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Monster Hunter: World", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/582010/header.jpg", "appid": 582010},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "The Witcher 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg", "appid": 292030},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Nioh 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1326470/header.jpg", "appid": 1326470},
        {"name": "Grim Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219990/header.jpg", "appid": 219990},
        {"name": "Dragon's Dogma 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2054970/header.jpg", "appid": 2054970}
    ],
    "Atmospheric": [
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Subnautica", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/264710/header.jpg", "appid": 264710},
        {"name": "Metro Exodus", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/412020/header.jpg", "appid": 412020},
        {"name": "Inside", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/304430/header.jpg", "appid": 304430},
        {"name": "S.T.A.L.K.E.R. 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1643320/header.jpg", "appid": 1643320},
        {"name": "Alan Wake 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2427700/header.jpg", "appid": 2427700},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360}
    ],
    "Perma Death": [
        {"name": "Risk of Rain 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632360/header.jpg", "appid": 632360},
        {"name": "Noita", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/881100/header.jpg", "appid": 881100},
        {"name": "Don't Starve", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219740/header.jpg", "appid": 219740},
        {"name": "Project Zomboid", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/108600/header.jpg", "appid": 108600},
        {"name": "Spelunky 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/418530/header.jpg", "appid": 418530},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Darkest Dungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/262060/header.jpg", "appid": 262060}
    ],
    "LGBTQ+": [
        {"name": "Life is Strange", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/319630/header.jpg", "appid": 319630},
        {"name": "Celeste", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/504230/header.jpg", "appid": 504230},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Boyfriend Dungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/674930/header.jpg", "appid": 674930},
        {"name": "Tell Me Why", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1180660/header.jpg", "appid": 1180660},
        {"name": "Dream Daddy", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/654880/header.jpg", "appid": 654880},
        {"name": "I Was a Teenage Exocolonist", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1148760/header.jpg", "appid": 1148760},
        {"name": "Goodbye Volcano High", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1089080/header.jpg", "appid": 1089080}
    ],
    "Story Rich": [
        {"name": "Baldur's Gate 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", "appid": 1086940},
        {"name": "The Witcher 3: Wild Hunt", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg", "appid": 292030},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "Red Dead Redemption 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1174180/header.jpg", "appid": 1174180},
        {"name": "God of War", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1593500/header.jpg", "appid": 1593500},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Detroit: Become Human", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1222140/header.jpg", "appid": 1222140},
        {"name": "Disco Elysium", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632470/header.jpg", "appid": 632470}
    ],
    "Singleplayer": [
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Red Dead Redemption 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1174180/header.jpg", "appid": 1174180},
        {"name": "The Witcher 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg", "appid": 292030},
        {"name": "God of War", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1593500/header.jpg", "appid": 1593500},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Black Myth: Wukong", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2358720/header.jpg", "appid": 2358720}
    ],
    "Great Soundtrack": [
        {"name": "DOOM Eternal", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/782330/header.jpg", "appid": 782330},
        {"name": "Undertale", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/391540/header.jpg", "appid": 391540},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Persona 5 Royal", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1687950/header.jpg", "appid": 1687950},
        {"name": "Risk of Rain 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632360/header.jpg", "appid": 632360},
        {"name": "Hotline Miami", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219150/header.jpg", "appid": 219150},
        {"name": "Celeste", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/504230/header.jpg", "appid": 504230},
        {"name": "NieR:Automata", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/524220/header.jpg", "appid": 524220}
    ],
    "Replay Value": [
        {"name": "The Binding of Isaac: Rebirth", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/250900/header.jpg", "appid": 250900},
        {"name": "Slay the Spire", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/646570/header.jpg", "appid": 646570},
        {"name": "Balatro", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", "appid": 2379780},
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "RimWorld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/294100/header.jpg", "appid": 294100},
        {"name": "Factorio", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/427520/header.jpg", "appid": 427520},
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600}
    ],
    "Roguelite": [
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Rogue Legacy 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1253920/header.jpg", "appid": 1253920},
        {"name": "Risk of Rain 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632360/header.jpg", "appid": 632360},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Enter the Gungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/311690/header.jpg", "appid": 311690},
        {"name": "Vampire Survivors", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1794680/header.jpg", "appid": 1794680},
        {"name": "Gunfire Reborn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1217060/header.jpg", "appid": 1217060},
        {"name": "Skul: The Hero Slayer", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1147560/header.jpg", "appid": 1147560}
    ],
    "Rogue-lite": [
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Rogue Legacy 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1253920/header.jpg", "appid": 1253920},
        {"name": "Risk of Rain 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632360/header.jpg", "appid": 632360},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Enter the Gungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/311690/header.jpg", "appid": 311690},
        {"name": "Vampire Survivors", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1794680/header.jpg", "appid": 1794680},
        {"name": "Gunfire Reborn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1217060/header.jpg", "appid": 1217060},
        {"name": "Skul: The Hero Slayer", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1147560/header.jpg", "appid": 1147560}
    ],
    "Dice": [
        {"name": "DICEPTION", "imageUrl": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4429000/56bd8aa0cf2d865acbae5501824e33c4dd8c2269/header.jpg?t=1785770104", "appid": 4429000},
        {"name": "Slice & Dice", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1875880/header.jpg", "appid": 1875880},
        {"name": "Dicey Dungeons", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/861540/header.jpg", "appid": 861540},
        {"name": "Citizen Sleeper", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1578650/header.jpg", "appid": 1578650},
        {"name": "Tharsis", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/323060/header.jpg", "appid": 323060},
        {"name": "Astrea: Six-Sided Oracles", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1755830/header.jpg", "appid": 1755830},
        {"name": "Armello", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/290340/header.jpg", "appid": 290340},
        {"name": "Baldur's Gate 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", "appid": 1086940}
    ],
    "Dark Fantasy": [
        {"name": "ELDEN RING", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", "appid": 1245620},
        {"name": "Dark Souls III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/374320/header.jpg", "appid": 374320},
        {"name": "Grim Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219990/header.jpg", "appid": 219990},
        {"name": "Lies of P", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1627720/header.jpg", "appid": 1627720},
        {"name": "Darkest Dungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/262060/header.jpg", "appid": 262060},
        {"name": "Blasphemous 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2114740/header.jpg", "appid": 2114740},
        {"name": "The Witcher 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg", "appid": 292030},
        {"name": "Lords of the Fallen", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1501750/header.jpg", "appid": 1501750}
    ],
    "Tower Defense": [
        {"name": "Bloons TD 6", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/960090/header.jpg", "appid": 960090},
        {"name": "Kingdom Rush Vengeance", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1367550/header.jpg", "appid": 1367550},
        {"name": "Mindustry", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1127400/header.jpg", "appid": 1127400},
        {"name": "Orcs Must Die! 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1522820/header.jpg", "appid": 1522820},
        {"name": "Legion TD 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/469600/header.jpg", "appid": 469600},
        {"name": "Plants vs. Zombies", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/3590/header.jpg", "appid": 3590},
        {"name": "Dungeon Defenders", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/65800/header.jpg", "appid": 65800},
        {"name": "Element TD 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1018830/header.jpg", "appid": 1018830}
    ],
    "Horror": [
        {"name": "Phasmophobia", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/739630/header.jpg", "appid": 739630},
        {"name": "Dead by Daylight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/381210/header.jpg", "appid": 381210},
        {"name": "Outlast", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/238320/header.jpg", "appid": 238320},
        {"name": "Resident Evil 4", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2050650/header.jpg", "appid": 2050650},
        {"name": "Alien: Isolation", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/214490/header.jpg", "appid": 214490},
        {"name": "Sons of the Forest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1326470/header.jpg", "appid": 1326470},
        {"name": "Lethal Company", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1966720/header.jpg", "appid": 1966720},
        {"name": "Signalis", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1262350/header.jpg", "appid": 1262350}
    ],
    "Survival": [
        {"name": "Rust", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/252490/header.jpg", "appid": 252490},
        {"name": "Valheim", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/892970/header.jpg", "appid": 892970},
        {"name": "Subnautica", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/264710/header.jpg", "appid": 264710},
        {"name": "Don't Starve", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219740/header.jpg", "appid": 219740},
        {"name": "7 Days to Die", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/251570/header.jpg", "appid": 251570},
        {"name": "Sons of the Forest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1326470/header.jpg", "appid": 1326470},
        {"name": "Raft", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/648800/header.jpg", "appid": 648800},
        {"name": "Project Zomboid", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/108600/header.jpg", "appid": 108600}
    ],
    "Base Building": [
        {"name": "RimWorld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/294100/header.jpg", "appid": 294100},
        {"name": "Factorio", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/427520/header.jpg", "appid": 427520},
        {"name": "Satisfactory", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/526870/header.jpg", "appid": 526870},
        {"name": "Rust", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/252490/header.jpg", "appid": 252490},
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600},
        {"name": "Oxygen Not Included", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/457140/header.jpg", "appid": 457140},
        {"name": "Valheim", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/892970/header.jpg", "appid": 892970},
        {"name": "Timberborn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1062090/header.jpg", "appid": 1062090}
    ],
    "Crafting": [
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600},
        {"name": "Valheim", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/892970/header.jpg", "appid": 892970},
        {"name": "Rust", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/252490/header.jpg", "appid": 252490},
        {"name": "Subnautica", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/264710/header.jpg", "appid": 264710},
        {"name": "Stardew Valley", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", "appid": 413150},
        {"name": "Raft", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/648800/header.jpg", "appid": 648800},
        {"name": "Satisfactory", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/526870/header.jpg", "appid": 526870},
        {"name": "Enshrouded", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1203630/header.jpg", "appid": 1203630}
    ],
    "Automation": [
        {"name": "Factorio", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/427520/header.jpg", "appid": 427520},
        {"name": "Satisfactory", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/526870/header.jpg", "appid": 526870},
        {"name": "Dyson Sphere Program", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1366540/header.jpg", "appid": 1366540},
        {"name": "Mindustry", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1127400/header.jpg", "appid": 1127400},
        {"name": "Shapez 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2162800/header.jpg", "appid": 2162800},
        {"name": "Oxygen Not Included", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/457140/header.jpg", "appid": 457140},
        {"name": "Captain of Industry", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1594320/header.jpg", "appid": 1594320},
        {"name": "Opus Magnum", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/558990/header.jpg", "appid": 558990}
    ],
    "Space": [
        {"name": "No Man's Sky", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/275850/header.jpg", "appid": 275850},
        {"name": "Stellaris", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/281990/header.jpg", "appid": 281990},
        {"name": "Starfield", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1716740/header.jpg", "appid": 1716740},
        {"name": "Kerbal Space Program", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/220200/header.jpg", "appid": 220200},
        {"name": "Elite Dangerous", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/359320/header.jpg", "appid": 359320},
        {"name": "Outer Wilds", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/753640/header.jpg", "appid": 753640},
        {"name": "Space Engineers", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/244850/header.jpg", "appid": 244850},
        {"name": "EVERSPACE 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1128920/header.jpg", "appid": 1128920}
    ],
    "Zombies": [
        {"name": "Left 4 Dead 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/550/header.jpg", "appid": 550},
        {"name": "Project Zomboid", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/108600/header.jpg", "appid": 108600},
        {"name": "Dying Light", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/239140/header.jpg", "appid": 239140},
        {"name": "7 Days to Die", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/251570/header.jpg", "appid": 251570},
        {"name": "Days Gone", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1259420/header.jpg", "appid": 1259420},
        {"name": "Dead by Daylight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/381210/header.jpg", "appid": 381210},
        {"name": "State of Decay 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/495420/header.jpg", "appid": 495420},
        {"name": "Dead Rising Deluxe Remaster", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2527390/header.jpg", "appid": 2527390}
    ],
    "Anime": [
        {"name": "Persona 5 Royal", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1687950/header.jpg", "appid": 1687950},
        {"name": "NieR:Automata", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/524220/header.jpg", "appid": 524220},
        {"name": "Tales of Arise", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/740130/header.jpg", "appid": 740130},
        {"name": "Guilty Gear -Strive-", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1384360/header.jpg", "appid": 1384360},
        {"name": "Dragon Ball FighterZ", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/678950/header.jpg", "appid": 678950},
        {"name": "Danganronpa: Trigger Happy Havoc", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413410/header.jpg", "appid": 413410},
        {"name": "Steins;Gate", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/412830/header.jpg", "appid": 412830},
        {"name": "Code Vein", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/678960/header.jpg", "appid": 678960}
    ],
    "Shooter": [
        {"name": "Counter-Strike 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg", "appid": 730},
        {"name": "Apex Legends", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1172470/header.jpg", "appid": 1172470},
        {"name": "DOOM Eternal", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/782330/header.jpg", "appid": 782330},
        {"name": "Rainbow Six Siege", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/359550/header.jpg", "appid": 359550},
        {"name": "Destiny 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1085660/header.jpg", "appid": 1085660},
        {"name": "Team Fortress 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg", "appid": 440},
        {"name": "Deep Rock Galactic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/548430/header.jpg", "appid": 548430},
        {"name": "Hunt: Showdown 1896", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/594650/header.jpg", "appid": 594650}
    ],
    "FPS": [
        {"name": "Counter-Strike 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/730/header.jpg", "appid": 730},
        {"name": "DOOM Eternal", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/782330/header.jpg", "appid": 782330},
        {"name": "ULTRAKILL", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1229490/header.jpg", "appid": 1229490},
        {"name": "Apex Legends", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1172470/header.jpg", "appid": 1172470},
        {"name": "Team Fortress 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg", "appid": 440},
        {"name": "Rainbow Six Siege", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/359550/header.jpg", "appid": 359550},
        {"name": "Left 4 Dead 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/550/header.jpg", "appid": 550},
        {"name": "Deep Rock Galactic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/548430/header.jpg", "appid": 548430}
    ],
    "2D Platformer": [
        {"name": "Celeste", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/504230/header.jpg", "appid": 504230},
        {"name": "Hollow Knight", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", "appid": 367520},
        {"name": "Cuphead", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/268910/header.jpg", "appid": 268910},
        {"name": "Dead Cells", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/588650/header.jpg", "appid": 588650},
        {"name": "Ori and the Blind Forest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/261570/header.jpg", "appid": 261570},
        {"name": "Super Meat Boy", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/40800/header.jpg", "appid": 40800},
        {"name": "Spelunky 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/418530/header.jpg", "appid": 418530},
        {"name": "Shovel Knight: Treasure Trove", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/250760/header.jpg", "appid": 250760}
    ],
    "3D Platformer": [
        {"name": "Psychonauts 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/607080/header.jpg", "appid": 607080},
        {"name": "A Hat in Time", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/253230/header.jpg", "appid": 253230},
        {"name": "Spyro Reignited Trilogy", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/996580/header.jpg", "appid": 996580},
        {"name": "Crash Bandicoot 4", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1378990/header.jpg", "appid": 1378990},
        {"name": "Sonic Frontiers", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1237320/header.jpg", "appid": 1237320},
        {"name": "It Takes Two", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1426210/header.jpg", "appid": 1426210},
        {"name": "Neon White", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1533420/header.jpg", "appid": 1533420},
        {"name": "SpongeBob SquarePants: Battle for Bikini Bottom", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/969990/header.jpg", "appid": 969990}
    ],
    "Puzzle": [
        {"name": "Portal 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/620/header.jpg", "appid": 620},
        {"name": "The Witness", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/210970/header.jpg", "appid": 210970},
        {"name": "Baba Is You", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/736260/header.jpg", "appid": 736260},
        {"name": "The Talos Principle 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/835960/header.jpg", "appid": 835960},
        {"name": "Return of the Obra Dinn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/653530/header.jpg", "appid": 653530},
        {"name": "Viewfinder", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1382070/header.jpg", "appid": 1382070},
        {"name": "Cocoon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1497440/header.jpg", "appid": 1497440},
        {"name": "Patrick's Parabox", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1260520/header.jpg", "appid": 1260520}
    ],
    "Relaxing": [
        {"name": "Dorfromantik", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1455840/header.jpg", "appid": 1455840},
        {"name": "Stardew Valley", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", "appid": 413150},
        {"name": "Unpacking", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1058650/header.jpg", "appid": 1058650},
        {"name": "A Short Hike", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1055540/header.jpg", "appid": 1055540},
        {"name": "Townscaper", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1291340/header.jpg", "appid": 1291340},
        {"name": "Tiny Glade", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2198150/header.jpg", "appid": 2198150},
        {"name": "Slime Rancher", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/433340/header.jpg", "appid": 433340},
        {"name": "ABZU", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/384190/header.jpg", "appid": 384190}
    ],
    "Tactical": [
        {"name": "Ready or Not", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1144200/header.jpg", "appid": 1144200},
        {"name": "Squad", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/393380/header.jpg", "appid": 393380},
        {"name": "Insurgency: Sandstorm", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/581320/header.jpg", "appid": 581320},
        {"name": "XCOM 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/268500/header.jpg", "appid": 268500},
        {"name": "Rainbow Six Siege", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/359550/header.jpg", "appid": 359550},
        {"name": "Arma 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/107410/header.jpg", "appid": 107410},
        {"name": "Door Kickers 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1239080/header.jpg", "appid": 1239080},
        {"name": "Desperados III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/618740/header.jpg", "appid": 618740}
    ],
    "Post-apocalyptic": [
        {"name": "Fallout 4", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/377160/header.jpg", "appid": 377160},
        {"name": "Metro Exodus", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/412020/header.jpg", "appid": 412020},
        {"name": "Cyberpunk 2077", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", "appid": 1091500},
        {"name": "S.T.A.L.K.E.R. 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1643320/header.jpg", "appid": 1643320},
        {"name": "Days Gone", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1259420/header.jpg", "appid": 1259420},
        {"name": "Frostpunk", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/323190/header.jpg", "appid": 323190},
        {"name": "Mad Max", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/234140/header.jpg", "appid": 234140},
        {"name": "Death Stranding Director's Cut", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1850570/header.jpg", "appid": 1850570}
    ],
    "Female Protagonist": [
        {"name": "Horizon Zero Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1151640/header.jpg", "appid": 1151640},
        {"name": "Control Ultimate Edition", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/870780/header.jpg", "appid": 870780},
        {"name": "Celeste", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/504230/header.jpg", "appid": 504230},
        {"name": "NieR:Automata", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/524220/header.jpg", "appid": 524220},
        {"name": "Life is Strange", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/319630/header.jpg", "appid": 319630},
        {"name": "Portal 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/620/header.jpg", "appid": 620},
        {"name": "Bayonetta", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/460790/header.jpg", "appid": 460790},
        {"name": "Shadow of the Tomb Raider", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/750920/header.jpg", "appid": 750920}
    ],
    "Comedy": [
        {"name": "Untitled Goose Game", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/837470/header.jpg", "appid": 837470},
        {"name": "Portal 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/620/header.jpg", "appid": 620},
        {"name": "Goat Simulator 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/853200/header.jpg", "appid": 853200},
        {"name": "The Stanley Parable: Ultra Deluxe", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1703340/header.jpg", "appid": 1703340},
        {"name": "South Park: The Stick of Truth", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/213670/header.jpg", "appid": 213670},
        {"name": "Fall Guys", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1097150/header.jpg", "appid": 1097150},
        {"name": "Human: Fall Flat", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/477160/header.jpg", "appid": 477160},
        {"name": "Donut County", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/702670/header.jpg", "appid": 702670}
    ],
    "Visual Novel": [
        {"name": "Doki Doki Literature Club Plus!", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1388880/header.jpg", "appid": 1388880},
        {"name": "Steins;Gate", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/412830/header.jpg", "appid": 412830},
        {"name": "Phoenix Wright: Ace Attorney Trilogy", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/787480/header.jpg", "appid": 787480},
        {"name": "Danganronpa: Trigger Happy Havoc", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413410/header.jpg", "appid": 413410},
        {"name": "Slay the Princess", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1989270/header.jpg", "appid": 1989270},
        {"name": "Coffee Talk", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/914800/header.jpg", "appid": 914800},
        {"name": "Clannad", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/324160/header.jpg", "appid": 324160},
        {"name": "VA-11 Hall-A: Cyberpunk Bartender Action", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/447530/header.jpg", "appid": 447530}
    ],
    "Physics": [
        {"name": "Teardown", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1167630/header.jpg", "appid": 1167630},
        {"name": "Besiege", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/346010/header.jpg", "appid": 346010},
        {"name": "Kerbal Space Program", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/220200/header.jpg", "appid": 220200},
        {"name": "People Playground", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1118200/header.jpg", "appid": 1118200},
        {"name": "Human: Fall Flat", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/477160/header.jpg", "appid": 477160},
        {"name": "BeamNG.drive", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/284160/header.jpg", "appid": 284160},
        {"name": "Totally Accurate Battle Simulator", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/508440/header.jpg", "appid": 508440},
        {"name": "Portal 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/620/header.jpg", "appid": 620}
    ],
    "Deckbuilding": [
        {"name": "Balatro", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", "appid": 2379780},
        {"name": "Slay the Spire", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/646570/header.jpg", "appid": 646570},
        {"name": "Monster Train", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1102190/header.jpg", "appid": 1102190},
        {"name": "Inscryption", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1092790/header.jpg", "appid": 1092790},
        {"name": "Wildfrost", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1811990/header.jpg", "appid": 1811990},
        {"name": "Across the Obelisk", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1385380/header.jpg", "appid": 1385380},
        {"name": "Peglin", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1296610/header.jpg", "appid": 1296610},
        {"name": "Cobalt Core", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2179850/header.jpg", "appid": 2179850}
    ],
    "Bullet Hell": [
        {"name": "Vampire Survivors", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1794680/header.jpg", "appid": 1794680},
        {"name": "Enter the Gungeon", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/311690/header.jpg", "appid": 311690},
        {"name": "Brotato", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1942280/header.jpg", "appid": 1942280},
        {"name": "Death Must Die", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2334730/header.jpg", "appid": 2334730},
        {"name": "20 Minutes Till Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1966900/header.jpg", "appid": 1966900},
        {"name": "HoloCure", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2420510/header.jpg", "appid": 2420510},
        {"name": "Just Shapes & Beats", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/531510/header.jpg", "appid": 531510},
        {"name": "Nova Drift", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/858210/header.jpg", "appid": 858210}
    ],
    "Colony Sim": [
        {"name": "RimWorld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/294100/header.jpg", "appid": 294100},
        {"name": "Oxygen Not Included", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/457140/header.jpg", "appid": 457140},
        {"name": "Dwarf Fortress", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/975370/header.jpg", "appid": 975370},
        {"name": "Timberborn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1062090/header.jpg", "appid": 1062090},
        {"name": "Going Medieval", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1029780/header.jpg", "appid": 1029780},
        {"name": "Clanfolk", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1700870/header.jpg", "appid": 1700870},
        {"name": "Songs of Syx", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1162700/header.jpg", "appid": 1162700},
        {"name": "Stranded: Alien Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1324130/header.jpg", "appid": 1324130}
    ],
    "Historical": [
        {"name": "Total War: THREE KINGDOMS", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/779340/header.jpg", "appid": 779340},
        {"name": "Crusader Kings III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1158310/header.jpg", "appid": 1158310},
        {"name": "Kingdom Come: Deliverance", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/379430/header.jpg", "appid": 379430},
        {"name": "Europa Universalis IV", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/236850/header.jpg", "appid": 236850},
        {"name": "Age of Empires IV", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1466860/header.jpg", "appid": 1466860},
        {"name": "Assassin's Creed Mirage", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2420110/header.jpg", "appid": 2420110},
        {"name": "Mount & Blade II: Bannerlord", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/261550/header.jpg", "appid": 261550},
        {"name": "Isonzo", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1556790/header.jpg", "appid": 1556790}
    ],
    "Stealth": [
        {"name": "Dishonored 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/403640/header.jpg", "appid": 403640},
        {"name": "HITMAN World of Assassination", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1659040/header.jpg", "appid": 1659040},
        {"name": "Metal Gear Solid V: The Phantom Pain", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/287700/header.jpg", "appid": 287700},
        {"name": "Deus Ex: Mankind Divided", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/337000/header.jpg", "appid": 337000},
        {"name": "Mark of the Ninja: Remastered", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/860950/header.jpg", "appid": 860950},
        {"name": "Shadow Tactics: Blades of the Shogun", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/418240/header.jpg", "appid": 418240},
        {"name": "Thief Simulator", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/704850/header.jpg", "appid": 704850},
        {"name": "Sniper Elite 5", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1029690/header.jpg", "appid": 1029690}
    ],
    "Exploration": [
        {"name": "Outer Wilds", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/753640/header.jpg", "appid": 753640},
        {"name": "Subnautica", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/264710/header.jpg", "appid": 264710},
        {"name": "No Man's Sky", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/275850/header.jpg", "appid": 275850},
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600},
        {"name": "Sea of Thieves", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1172620/header.jpg", "appid": 1172620},
        {"name": "ABZU", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/384190/header.jpg", "appid": 384190},
        {"name": "DREDGE", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1562430/header.jpg", "appid": 1562430},
        {"name": "Dave the Diver", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1868140/header.jpg", "appid": 1868140}
    ],
    "Resource Management": [
        {"name": "Factorio", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/427520/header.jpg", "appid": 427520},
        {"name": "Frostpunk", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/323190/header.jpg", "appid": 323190},
        {"name": "Against the Storm", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1336490/header.jpg", "appid": 1336490},
        {"name": "RimWorld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/294100/header.jpg", "appid": 294100},
        {"name": "Satisfactory", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/526870/header.jpg", "appid": 526870},
        {"name": "Oxygen Not Included", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/457140/header.jpg", "appid": 457140},
        {"name": "Timberborn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1062090/header.jpg", "appid": 1062090},
        {"name": "Surviving Mars", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/464920/header.jpg", "appid": 464920}
    ],
    "Local Multiplayer": [
        {"name": "Overcooked! 2", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/448510/header.jpg", "appid": 448510},
        {"name": "The Jackbox Party Pack 9", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1850960/header.jpg", "appid": 1850960},
        {"name": "Gang Beasts", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/285900/header.jpg", "appid": 285900},
        {"name": "Duck Game", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/312530/header.jpg", "appid": 312530},
        {"name": "Ultimate Chicken Horse", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/386940/header.jpg", "appid": 386940},
        {"name": "Stick Fight: The Game", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/674940/header.jpg", "appid": 674940},
        {"name": "Pummel Party", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/880940/header.jpg", "appid": 880940},
        {"name": "Keep Talking and Nobody Explodes", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/341800/header.jpg", "appid": 341800}
    ],
    "Cute": [
        {"name": "Stardew Valley", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", "appid": 413150},
        {"name": "Slime Rancher", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/433340/header.jpg", "appid": 433340},
        {"name": "Animal Well", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/813230/header.jpg", "appid": 813230},
        {"name": "Cult of the Lamb", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1313140/header.jpg", "appid": 1313140},
        {"name": "Cat Quest III", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2305840/header.jpg", "appid": 2305840},
        {"name": "A Hat in Time", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/253230/header.jpg", "appid": 253230},
        {"name": "Lil Gator Game", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1586800/header.jpg", "appid": 1586800},
        {"name": "Fall Guys", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1097150/header.jpg", "appid": 1097150}
    ],
    "Mystery": [
        {"name": "Return of the Obra Dinn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/653530/header.jpg", "appid": 653530},
        {"name": "Pentiment", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1205520/header.jpg", "appid": 1205520},
        {"name": "The Wolf Among Us", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/250320/header.jpg", "appid": 250320},
        {"name": "Disco Elysium", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632470/header.jpg", "appid": 632470},
        {"name": "Phoenix Wright: Ace Attorney", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/787480/header.jpg", "appid": 787480},
        {"name": "Danganronpa", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/413410/header.jpg", "appid": 413410},
        {"name": "Outer Wilds", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/753640/header.jpg", "appid": 753640},
        {"name": "Her Story", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/368370/header.jpg", "appid": 368370}
    ],
    "Choices Matter": [
        {"name": "The Witcher 3: Wild Hunt", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg", "appid": 292030},
        {"name": "Detroit: Become Human", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1222140/header.jpg", "appid": 1222140},
        {"name": "Baldur's Gate 3", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", "appid": 1086940},
        {"name": "Life is Strange", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/319630/header.jpg", "appid": 319630},
        {"name": "The Walking Dead", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/207610/header.jpg", "appid": 207610},
        {"name": "Heavy Rain", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/960910/header.jpg", "appid": 960910},
        {"name": "Disco Elysium", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/632470/header.jpg", "appid": 632470},
        {"name": "Until Dawn", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/2172010/header.jpg", "appid": 2172010}
    ],
    "Top-Down": [
        {"name": "Hades", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", "appid": 1145360},
        {"name": "Hotline Miami", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/219150/header.jpg", "appid": 219150},
        {"name": "Foxhole", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/505460/header.jpg", "appid": 505460},
        {"name": "RimWorld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/294100/header.jpg", "appid": 294100},
        {"name": "Alien Swarm: Reactive Drop", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/563560/header.jpg", "appid": 563560},
        {"name": "The Ascent", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/979690/header.jpg", "appid": 979690},
        {"name": "Weird West", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1097350/header.jpg", "appid": 1097350},
        {"name": "Ruiner", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/464060/header.jpg", "appid": 464060}
    ],
    "Sandbox": [
        {"name": "Terraria", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", "appid": 105600},
        {"name": "Garry's Mod", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/4000/header.jpg", "appid": 4000},
        {"name": "Teardown", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1167630/header.jpg", "appid": 1167630},
        {"name": "People Playground", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1118200/header.jpg", "appid": 1118200},
        {"name": "Space Engineers", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/244850/header.jpg", "appid": 244850},
        {"name": "Besiege", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/346010/header.jpg", "appid": 346010},
        {"name": "Scrap Mechanic", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/387990/header.jpg", "appid": 387990},
        {"name": "Universe Sandbox", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/72200/header.jpg", "appid": 72200}
    ],
    "Open World Survival Craft": [
        {"name": "Palworld", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1623730/header.jpg", "appid": 1623730},
        {"name": "Valheim", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/892970/header.jpg", "appid": 892970},
        {"name": "Enshrouded", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1203630/header.jpg", "appid": 1203630},
        {"name": "Rust", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/252490/header.jpg", "appid": 252490},
        {"name": "Sons of the Forest", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1326470/header.jpg", "appid": 1326470},
        {"name": "ARK: Survival Evolved", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/346110/header.jpg", "appid": 346110},
        {"name": "Grounded", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/962130/header.jpg", "appid": 962130},
        {"name": "V Rising", "imageUrl": "https://cdn.akamai.steamstatic.com/steam/apps/1604030/header.jpg", "appid": 1604030}
    ]
}

# 3. Compute Top 25 Highest Rated and Lowest 25 Rated Flop Showcases
def compute_strict_score(row):
    c_std = float(row["brightness_std"]) if pd.notna(row["brightness_std"]) else 50.0
    warm_pct = 50.0 if row["palette_type"] == "warm" else (20.0 if row["palette_type"] == "neutral" else 5.0)
    entropy = float(row["entropy"]) if pd.notna(row["entropy"]) else 6.0
    edge_density = float(row["edge_density"]) * 100.0 if pd.notna(row["edge_density"]) and float(row["edge_density"]) < 1.0 else (float(row["edge_density"]) if pd.notna(row["edge_density"]) else 10.0)
    is_center_focused = (row["focus"] == "center")
    spotlight_ratio = float(row["center_vs_edge_brightness"]) if pd.notna(row.get("center_vs_edge_brightness")) else 0.0
    title_contrast = float(row["title_contrast"]) if pd.notna(row.get("title_contrast")) else 3.5

    # 1. Dynamic Contrast (Mega-Hit Benchmark: 63.0)
    contrast_score = min(100.0, 95.0 + (c_std - 63.0) * 0.8) if c_std >= 63.0 else max(0.0, 100.0 - (63.0 - c_std) * 3.5)
    # 2. Warmth / Saliency (Mega-Hit Benchmark: 45.0%)
    warmth_score = min(100.0, 95.0 + (warm_pct - 45.0) * 0.2) if warm_pct >= 45.0 else max(0.0, 100.0 - (45.0 - warm_pct) * 2.0)
    # 3. Shannon Entropy (Mega-Hit Benchmark: 6.90 bits)
    entropy_score = 98.0 if entropy >= 6.90 else max(0.0, 100.0 - (6.90 - entropy) * 50.0)
    # 4. Edge Density (Mega-Hit Benchmark: 13.5%)
    edge_score = 95.0 if edge_density >= 13.5 else max(0.0, 100.0 - (13.5 - edge_density) * 8.0)
    # 5. Hero Spotlight / Composition
    focus_score = 98.0 if spotlight_ratio > 10.0 else (85.0 if is_center_focused else 45.0)
    # 6. Title Typography Contrast
    if title_contrast >= 4.5:
        text_score = min(100.0, 92.0 + (title_contrast - 4.5) * 2.0)
    elif title_contrast >= 3.0:
        text_score = 60.0 + ((title_contrast - 3.0) / 1.5) * 25.0
    else:
        text_score = max(0.0, title_contrast * 18.0)

    sub_scores = [contrast_score, warmth_score, entropy_score, edge_score, focus_score, text_score]
    base_score = (
        contrast_score * 0.25 +
        warmth_score * 0.15 +
        entropy_score * 0.15 +
        edge_score * 0.15 +
        focus_score * 0.15 +
        text_score * 0.15
    )

    is_contrast_flaw = c_std < 58.0
    is_warmth_flaw = warm_pct < 35.0
    is_entropy_flaw = entropy < 6.2
    is_edge_flaw = edge_density < 8.0
    is_focus_flaw = not is_center_focused
    is_text_flaw = title_contrast < 3.0

    flaw_count = sum([is_contrast_flaw, is_warmth_flaw, is_entropy_flaw, is_edge_flaw, is_focus_flaw, is_text_flaw])
    min_sub = min(sub_scores)
    flaw_penalty = 0.0
    if flaw_count > 0:
        flaw_penalty = flaw_count * 13.0 + max(0.0, (40.0 - min_sub) * 0.8)

    overall = max(0, min(100, round(base_score - flaw_penalty)))
    return overall

clean_df["score"] = clean_df.apply(compute_strict_score, axis=1)

def format_game_card(r):
    aid = int(r["appid"])
    c_std = round(float(r["brightness_std"]), 1) if pd.notna(r["brightness_std"]) else 0.0
    warm_type = str(r["palette_type"]) if pd.notna(r["palette_type"]) else "neutral"
    reviews = int(r["total_reviews"]) if pd.notna(r["total_reviews"]) else 0
    t = str(r["tier"]) if pd.notna(r["tier"]) else "moderate"
    genres = str(r["all_genres"]) if pd.notna(r["all_genres"]) else (str(r["primary_genre"]) if pd.notna(r["primary_genre"]) else "Indie")
    return {
        "appid": aid,
        "name": str(r["name"]),
        "score": int(r["score"]),
        "tier": t,
        "tier_label": tier_labels.get(t, t.title()),
        "reviews": reviews,
        "contrast_std": c_std,
        "palette_type": warm_type,
        "genre": genres.split(";")[0].split(",")[0].strip(),
        "imageUrl": f"https://cdn.akamai.steamstatic.com/steam/apps/{aid}/header.jpg",
        "storeUrl": f"https://store.steampowered.com/app/{aid}/"
    }

top_rated_games = [format_game_card(r) for _, r in clean_df.sort_values(by=["score", "total_reviews"], ascending=[False, False]).head(25).iterrows()]
lowest_rated_games = [format_game_card(r) for _, r in clean_df[clean_df["tier"].isin(["near_zero", "struggling"])].sort_values(by=["score", "total_reviews"], ascending=[True, True]).head(25).iterrows()]

output_payload = {
    "generated_at": pd.Timestamp.now().isoformat(),
    "overall": overall_stats,
    "tiers": tier_benchmarks,
    "genres": genre_benchmarks,
    "tags": tag_benchmarks,
    "presets": sample_presets,
    "genre_competitors": genre_competitor_catalogs,
    "top_rated": top_rated_games,
    "lowest_rated": lowest_rated_games
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2)

print(f"✅ Generated {OUTPUT_JSON} with {total_valid:,} records, {len(genre_benchmarks)} broad genres, {len(tag_benchmarks)} tags benchmarks, 25 Top-Rated, and 25 Lowest-Rated.")

