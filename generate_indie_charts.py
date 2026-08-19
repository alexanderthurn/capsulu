#!/usr/bin/env python3
"""
generate_indie_charts.py — Generates empirical comparison charts specifically for
the indie zero-to-100 funnel:
  1. 0 Reviews (Ghost Zone / Unbought)
  2. 1-5 Reviews (Friend Reviews Only)
  3. 6-10 Reviews (Milestone Threshold)
  4. 11-100 Reviews (Algorithm Ignition)
  5. 100+ Reviews (Breakout Hits)

Saves charts to:
  - output/charts/indie_*.png
  - web/benchmark/indie_*.png
"""

import os
import shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "aggregated_dataset.csv")
OUTPUT_CHARTS_DIR = os.path.join(PROJECT_DIR, "output", "charts")
WEB_BENCHMARK_DIR = os.path.join(PROJECT_DIR, "web", "benchmark")

os.makedirs(OUTPUT_CHARTS_DIR, exist_ok=True)
os.makedirs(WEB_BENCHMARK_DIR, exist_ok=True)

# Aesthetic theme
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "figure.titlesize": 15,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight"
})

INDIE_TIER_ORDER = ["0_reviews", "1_5_reviews", "6_10_reviews", "11_100_reviews", "100_plus"]

INDIE_TIER_LABELS = {
    "0_reviews": "0 Reviews (Ghost Zone)",
    "1_5_reviews": "1-5 Reviews (Friend Zone)",
    "6_10_reviews": "6-10 Reviews (Threshold)",
    "11_100_reviews": "11-100 Reviews (Ignition)",
    "100_plus": "100+ Reviews (Breakout)"
}

INDIE_SHORT_LABELS = {
    "0_reviews": "0 Revs\n(Ghost)",
    "1_5_reviews": "1-5 Revs\n(Friend)",
    "6_10_reviews": "6-10 Revs\n(Threshold)",
    "11_100_reviews": "11-100 Revs\n(Ignition)",
    "100_plus": "100+ Revs\n(Breakout)"
}

INDIE_COLORS = {
    "0_reviews": "#c0392b",    # Dark Crimson
    "1_5_reviews": "#e74c3c",  # Red
    "6_10_reviews": "#f39c12", # Gold/Orange
    "11_100_reviews": "#3498db", # Cyan/Blue
    "100_plus": "#2ecc71"      # Emerald Green
}

def classify_indie_tier(reviews):
    if pd.isna(reviews) or reviews == 0:
        return "0_reviews"
    elif 1 <= reviews <= 5:
        return "1_5_reviews"
    elif 6 <= reviews <= 10:
        return "6_10_reviews"
    elif 11 <= reviews <= 100:
        return "11_100_reviews"
    else:
        return "100_plus"

def load_clean_data():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Missing {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    clean_df = df[
        (df["brightness_std"] > 1.0) &
        (df["avg_brightness"] > 5.0) &
        (df["avg_brightness"] < 250.0)
    ].copy()
    clean_df["indie_tier"] = clean_df["total_reviews"].apply(classify_indie_tier)
    print(f"📊 Loaded {len(clean_df):,} cleaned games.")
    print(clean_df["indie_tier"].value_counts())
    return clean_df

def generate_indie_chart_1_brightness_contrast(df):
    print("📈 Generating Indie Chart 1: Brightness & Contrast...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

    # Brightness
    sns.boxplot(
        data=df,
        x="indie_tier",
        y="avg_brightness",
        order=INDIE_TIER_ORDER,
        hue="indie_tier",
        palette=INDIE_COLORS,
        legend=False,
        ax=ax1,
        boxprops=dict(alpha=0.8),
        showmeans=True,
        meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black", "markersize":"7"}
    )
    ax1.set_title("Average Brightness (0-255) in Indie Funnel\n(White dot = mean • 0-5 revs are muddier)")
    ax1.set_xlabel("")
    ax1.set_ylabel("Mean Pixel Luminance")
    ax1.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax1.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])

    # Contrast (Std Dev)
    sns.boxplot(
        data=df,
        x="indie_tier",
        y="brightness_std",
        order=INDIE_TIER_ORDER,
        hue="indie_tier",
        palette=INDIE_COLORS,
        legend=False,
        ax=ax2,
        boxprops=dict(alpha=0.8),
        showmeans=True,
        meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black", "markersize":"7"}
    )
    ax2.set_title("Dynamic Contrast (Std Dev) in Indie Funnel\n(Sharp leap: 57.0 in Friend Zone → 61.5+ in Breakouts)")
    ax2.set_xlabel("")
    ax2.set_ylabel("Luminance Std Dev (Dynamic Range)")
    ax2.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax2.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])

    plt.tight_layout()
    path = os.path.join(OUTPUT_CHARTS_DIR, "indie_1_brightness_contrast.png")
    plt.savefig(path)
    plt.close()
    return path

def generate_indie_chart_2_palette_and_saturation(df):
    print("📈 Generating Indie Chart 2: Color Temperature & Saturation...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

    palette_df = df.groupby(["indie_tier", "palette_type"]).size().unstack(fill_value=0)
    palette_df = palette_df.div(palette_df.sum(axis=1), axis=0) * 100
    palette_df = palette_df.reindex(INDIE_TIER_ORDER)

    temp_colors = {"warm": "#e67e22", "cool": "#3498db", "neutral": "#95a5a6"}
    palette_df[["warm", "cool", "neutral"]].plot(
        kind="bar",
        stacked=True,
        color=[temp_colors[c] for c in ["warm", "cool", "neutral"]],
        ax=ax1,
        alpha=0.85,
        rot=0
    )
    ax1.set_title("Color Temperature Breakdown (%)\n(61% of 0-5 review games blend into dark Steam UI)")
    ax1.set_xlabel("")
    ax1.set_ylabel("Percentage (%)")
    ax1.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax1.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])
    ax1.legend(title="Palette Type", loc="upper right")

    # Saturation KDE
    sns.kdeplot(
        data=df[df["indie_tier"] == "100_plus"]["avg_saturation"],
        label="100+ Revs (Breakout)",
        color=INDIE_COLORS["100_plus"],
        linewidth=2.8,
        fill=True,
        alpha=0.2,
        ax=ax2
    )
    sns.kdeplot(
        data=df[df["indie_tier"] == "11_100_reviews"]["avg_saturation"],
        label="11-100 Revs (Ignition)",
        color=INDIE_COLORS["11_100_reviews"],
        linewidth=2.0,
        linestyle="--",
        ax=ax2
    )
    sns.kdeplot(
        data=df[df["indie_tier"] == "1_5_reviews"]["avg_saturation"],
        label="1-5 Revs (Friend Zone)",
        color=INDIE_COLORS["1_5_reviews"],
        linewidth=2.8,
        fill=True,
        alpha=0.15,
        ax=ax2
    )
    ax2.set_title("Color Saturation Density (HSV Saturation)")
    ax2.set_xlabel("Average Saturation (0-255)")
    ax2.set_ylabel("Density")
    ax2.legend(loc="upper right")

    plt.tight_layout()
    path = os.path.join(OUTPUT_CHARTS_DIR, "indie_2_palette_and_saturation.png")
    plt.savefig(path)
    plt.close()
    return path

def generate_indie_chart_3_detail_and_complexity(df):
    print("📈 Generating Indie Chart 3: Sharpness & Edge Density...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

    # Edge density
    sns.barplot(
        data=df,
        x="indie_tier",
        y="edge_density",
        order=INDIE_TIER_ORDER,
        hue="indie_tier",
        palette=INDIE_COLORS,
        legend=False,
        ax=ax1,
        capsize=0.1,
        alpha=0.85
    )
    ax1.set_title("Edge Density % (Silhouette Definition at 120px)\n(0-5 rev games suffer from blurry outlines)")
    ax1.set_xlabel("")
    ax1.set_ylabel("Edge Pixel Fraction (%)")
    ax1.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax1.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])

    # Shannon Entropy
    sns.boxplot(
        data=df,
        x="indie_tier",
        y="entropy",
        order=INDIE_TIER_ORDER,
        hue="indie_tier",
        palette=INDIE_COLORS,
        legend=False,
        ax=ax2,
        boxprops=dict(alpha=0.8)
    )
    ax2.set_title("Shannon Entropy (Visual Information Depth)\n(Rich texture detail rises steadily with reviews)")
    ax2.set_xlabel("")
    ax2.set_ylabel("Entropy (bits)")
    ax2.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax2.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])

    plt.tight_layout()
    path = os.path.join(OUTPUT_CHARTS_DIR, "indie_3_detail_complexity.png")
    plt.savefig(path)
    plt.close()
    return path

def generate_indie_chart_4_text_typography(df):
    print("📈 Generating Indie Chart 4: Typography & Readability...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

    df_text = df[df["has_text"] == True].copy()
    readability_df = df_text.groupby(["indie_tier", "title_readability"]).size().unstack(fill_value=0)
    for col in ["good", "fair", "poor"]:
        if col not in readability_df.columns:
            readability_df[col] = 0
    readability_df = readability_df[["good", "fair", "poor"]]
    readability_pct = readability_df.div(readability_df.sum(axis=1), axis=0) * 100
    readability_pct = readability_pct.reindex(INDIE_TIER_ORDER)

    read_colors = {"good": "#27ae60", "fair": "#f39c12", "poor": "#c0392b"}
    readability_pct.plot(
        kind="bar",
        stacked=True,
        color=[read_colors[c] for c in ["good", "fair", "poor"]],
        ax=ax1,
        alpha=0.85,
        rot=0
    )
    ax1.set_title("Text Readability (WCAG Contrast Standards)\n(Good ≥ 4.5:1, Fair ≥ 3:1, Poor < 3:1)")
    ax1.set_xlabel("")
    ax1.set_ylabel("Percentage (%)")
    ax1.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax1.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])
    ax1.legend(title="Readability", loc="upper right")

    # Text Contrast Ratio
    sns.boxplot(
        data=df_text,
        x="indie_tier",
        y="title_contrast",
        order=INDIE_TIER_ORDER,
        hue="indie_tier",
        palette=INDIE_COLORS,
        legend=False,
        ax=ax2,
        showfliers=False,
        boxprops=dict(alpha=0.8)
    )
    ax2.set_title("Title-to-Background Contrast Ratio in Indie Tiers")
    ax2.set_xlabel("")
    ax2.set_ylabel("Contrast Ratio (:1)")
    ax2.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax2.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])
    ax2.axhline(4.5, color="green", linestyle=":", label="WCAG AA (4.5:1)")
    ax2.legend(loc="upper right")

    plt.tight_layout()
    path = os.path.join(OUTPUT_CHARTS_DIR, "indie_4_text_readability.png")
    plt.savefig(path)
    plt.close()
    return path

def generate_indie_chart_5_title_positioning_heatmap(df):
    print("📈 Generating Indie Chart 5: Title Positioning Comparison...")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)

    grid_order = [
        ["top_left", "top_center", "top_right"],
        ["mid_left", "mid_center", "mid_right"],
        ["bot_left", "bot_center", "bot_right"]
    ]

    df_text = df[df["has_text"] == True]
    compare_tiers = ["1_5_reviews", "11_100_reviews", "100_plus"]

    for idx, tier in enumerate(compare_tiers):
        sub_df = df_text[df_text["indie_tier"] == tier]
        total = len(sub_df)
        counts = sub_df["title_zone"].value_counts()

        matrix = np.zeros((3, 3))
        for r in range(3):
            for c in range(3):
                zone_name = grid_order[r][c]
                matrix[r, c] = (counts.get(zone_name, 0) / total * 100) if total > 0 else 0

        sns.heatmap(
            matrix,
            annot=True,
            fmt=".1f",
            cmap="YlGnBu",
            cbar=False,
            xticklabels=["Left", "Center", "Right"],
            yticklabels=["Top", "Middle", "Bottom"] if idx == 0 else False,
            ax=axes[idx],
            annot_kws={"size": 11, "weight": "bold"}
        )
        axes[idx].set_title(f"{INDIE_TIER_LABELS[tier]}\n(Title Location %)")

    plt.suptitle("Where Indie Developers Place the Title Logo (3x3 Grid %)", fontsize=14, y=1.03)
    plt.tight_layout()
    path = os.path.join(OUTPUT_CHARTS_DIR, "indie_5_title_positioning_heatmap.png")
    plt.savefig(path)
    plt.close()
    return path

def generate_indie_chart_6_composition_focus(df):
    print("📈 Generating Indie Chart 6: Visual Focus & Lighting Distribution...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

    focus_df = df.groupby(["indie_tier", "focus"]).size().unstack(fill_value=0)
    focus_pct = focus_df.div(focus_df.sum(axis=1), axis=0) * 100
    focus_pct = focus_pct.reindex(INDIE_TIER_ORDER)

    focus_colors = {"center": "#9b59b6", "edges": "#34495e"}
    focus_pct[["center", "edges"]].plot(
        kind="bar",
        stacked=True,
        color=[focus_colors[c] for c in ["center", "edges"]],
        ax=ax1,
        alpha=0.85,
        rot=0
    )
    ax1.set_title("Focal Lighting Focus (% of Tier)\n(Center Spotlight vs Edge Vignette)")
    ax1.set_xlabel("")
    ax1.set_ylabel("Percentage (%)")
    ax1.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax1.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])
    ax1.legend(title="Focal Lighting", loc="upper right")

    # Dark ratio vs Light ratio
    tier_ratios = df.groupby("indie_tier")[["dark_ratio", "light_ratio"]].mean().reindex(INDIE_TIER_ORDER) * 100
    tier_ratios.plot(
        kind="bar",
        color=["#2c3e50", "#f1c40f"],
        ax=ax2,
        alpha=0.85,
        rot=0
    )
    ax2.set_title("Shadow vs Highlight Composition (%)\n(0-5 revs have 10% lower specular highlight ratios)")
    ax2.set_xlabel("")
    ax2.set_ylabel("Average Area (%)")
    ax2.set_xticks(range(len(INDIE_TIER_ORDER)))
    ax2.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])
    ax2.legend(["Shadow Ratio (<80)", "Highlight Ratio (>180)"], loc="upper right")

    plt.tight_layout()
    path = os.path.join(OUTPUT_CHARTS_DIR, "indie_6_composition_lighting.png")
    plt.savefig(path)
    plt.close()
    return path

def generate_indie_chart_7_indie_milestones(df):
    print("📈 Generating Indie Chart 7: Zero-to-100 Breakthrough Milestones...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Top Indie Genres distribution across 0-10 vs 11-100 vs 100+
    indie_genres = ["Indie", "Action", "Adventure", "RPG", "Strategy", "Simulation", "Casual"]
    genre_df = df[df["primary_genre"].isin(indie_genres)].copy()

    g_pivot = pd.crosstab(genre_df["primary_genre"], genre_df["indie_tier"], normalize="index") * 100
    g_pivot = g_pivot.reindex(columns=INDIE_TIER_ORDER)

    g_pivot.plot(
        kind="barh",
        stacked=True,
        color=[INDIE_COLORS[c] for c in INDIE_TIER_ORDER],
        ax=ax1,
        alpha=0.85
    )
    ax1.set_title("Review Tier Distribution Across Popular Indie Genres")
    ax1.set_xlabel("Share of Genre (%)")
    ax1.set_ylabel("Primary Genre")
    ax1.legend([INDIE_SHORT_LABELS[t].replace("\n", " ") for t in INDIE_TIER_ORDER], loc="lower right", fontsize=8.5)

    # Metric progression radar / line
    metrics_summary = df.groupby("indie_tier", observed=False).agg({
        "brightness_std": "mean",
        "avg_brightness": "mean",
        "entropy": "mean",
        "edge_density": lambda x: x.mean() * 100
    }).reindex(INDIE_TIER_ORDER)

    # Normalize metrics to 0-100 for easy visual comparison
    norm_summary = (metrics_summary - metrics_summary.min()) / (metrics_summary.max() - metrics_summary.min()) * 100
    
    x_indices = np.arange(len(INDIE_TIER_ORDER))
    ax2.plot(x_indices, norm_summary["brightness_std"], marker="o", linewidth=2.5, label="Dynamic Contrast", color="#f1c40f")
    ax2.plot(x_indices, norm_summary["entropy"], marker="s", linewidth=2.5, label="Shannon Entropy", color="#9b59b6")
    ax2.plot(x_indices, norm_summary["edge_density"], marker="^", linewidth=2.5, label="Edge Density (120px)", color="#3498db")
    ax2.plot(x_indices, norm_summary["avg_brightness"], marker="d", linewidth=2.5, label="Avg Brightness", color="#2ecc71")

    ax2.set_title("Visual Quality Metric Progression (0 → 100+ Reviews)")
    ax2.set_xlabel("Indie Review Milestone")
    ax2.set_ylabel("Relative Quality Index (0-100)")
    ax2.set_xticks(x_indices)
    ax2.set_xticklabels([INDIE_SHORT_LABELS[t] for t in INDIE_TIER_ORDER])
    ax2.legend(loc="upper left")

    plt.tight_layout()
    path = os.path.join(OUTPUT_CHARTS_DIR, "indie_7_genre_visual_profiles.png")
    plt.savefig(path)
    plt.close()
    return path

def main():
    print("🎨 Starting Indie Zero-to-100 Funnel Chart Generation...")
    df = load_clean_data()

    chart_funcs = [
        generate_indie_chart_1_brightness_contrast,
        generate_indie_chart_2_palette_and_saturation,
        generate_indie_chart_3_detail_and_complexity,
        generate_indie_chart_4_text_typography,
        generate_indie_chart_5_title_positioning_heatmap,
        generate_indie_chart_6_composition_focus,
        generate_indie_chart_7_indie_milestones
    ]

    for fn in chart_funcs:
        p = fn(df)
        if p and os.path.exists(p):
            fname = os.path.basename(p)
            dest = os.path.join(WEB_BENCHMARK_DIR, fname)
            shutil.copyfile(p, dest)
            print(f"  ✓ Saved to {dest}")

    print("🎉 All 7 Indie Funnel Charts generated successfully!")

if __name__ == "__main__":
    main()
