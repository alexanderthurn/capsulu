#!/usr/bin/env python3
"""
5_analyze_images.py — Extract visual features from header capsule images.

Analyzes each downloaded header image and saves a full feature set per image
as a JSON file in data/raw_analysis/{appid}.json. Fully resumable.

Features extracted:
  - Color: dominant colors, palette type, brightness, contrast, saturation
  - Text: OCR detection, position, size, color, readability/contrast
  - Detail: sharpness, edge density, entropy, texture complexity
  - Composition: visual weight distribution, brightness zones

Usage:
    python 5_analyze_images.py [--limit 10] [--workers 4] [--tier all]

Output:
    data/raw_analysis/{appid}.json  (one per image)
"""

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

# Try to import pytesseract
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    print("⚠️  pytesseract not installed — text analysis will be skipped")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
ANALYSIS_DIR = os.path.join(DATA_DIR, "raw_analysis")
APPS_FILE = os.path.join(DATA_DIR, "apps_all.json")

# Image zones for position classification (3x3 grid)
ZONES = {
    "top_left":     (0.0, 0.0, 0.33, 0.33),
    "top_center":   (0.33, 0.0, 0.67, 0.33),
    "top_right":    (0.67, 0.0, 1.0, 0.33),
    "mid_left":     (0.0, 0.33, 0.33, 0.67),
    "mid_center":   (0.33, 0.33, 0.67, 0.67),
    "mid_right":    (0.67, 0.33, 1.0, 0.67),
    "bot_left":     (0.0, 0.67, 0.33, 1.0),
    "bot_center":   (0.33, 0.67, 0.67, 1.0),
    "bot_right":    (0.67, 0.67, 1.0, 1.0),
}


def rgb_to_hex(r, g, b):
    """Convert RGB to hex string."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def classify_color_temp(r, g, b):
    """Classify a color as warm, cool, or neutral."""
    warmth = (r * 1.0 + g * 0.5) - (b * 1.0 + g * 0.2)
    if warmth > 30:
        return "warm"
    elif warmth < -30:
        return "cool"
    return "neutral"


def luminance(r, g, b):
    """Calculate relative luminance (WCAG formula)."""
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(l1, l2):
    """WCAG contrast ratio between two luminance values."""
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def classify_zone(cx, cy, img_w, img_h):
    """Classify a point into one of 9 zones."""
    rx = cx / img_w
    ry = cy / img_h
    for zone_name, (x1, y1, x2, y2) in ZONES.items():
        if x1 <= rx < x2 and y1 <= ry < y2:
            return zone_name
    return "mid_center"


def analyze_colors(img_rgb, img_hsv):
    """Extract color features from the image."""
    pixels = img_rgb.reshape(-1, 3).astype(float)
    hsv_pixels = img_hsv.reshape(-1, 3).astype(float)

    # K-means for dominant colors (5 clusters)
    n_colors = 5
    sample_size = min(5000, len(pixels))
    indices = np.random.choice(len(pixels), sample_size, replace=False)
    sample = pixels[indices]

    kmeans = KMeans(n_clusters=n_colors, n_init=3, max_iter=100, random_state=42)
    kmeans.fit(sample)

    colors = kmeans.cluster_centers_
    labels = kmeans.predict(sample)
    counts = np.bincount(labels, minlength=n_colors)
    percentages = counts / counts.sum()

    # Sort by percentage (descending)
    order = np.argsort(-percentages)
    dominant_colors = []
    for i in order:
        r, g, b = colors[i]
        dominant_colors.append({
            "rgb": [int(r), int(g), int(b)],
            "hex": rgb_to_hex(r, g, b),
            "percentage": round(float(percentages[i]), 3),
            "temperature": classify_color_temp(r, g, b),
        })

    # Overall temperature
    temp_counts = {"warm": 0, "cool": 0, "neutral": 0}
    for dc in dominant_colors:
        temp_counts[dc["temperature"]] += dc["percentage"]
    palette_type = max(temp_counts, key=temp_counts.get)

    # Brightness (luminance)
    gray = 0.299 * pixels[:, 0] + 0.587 * pixels[:, 1] + 0.114 * pixels[:, 2]
    avg_brightness = float(np.mean(gray))
    brightness_std = float(np.std(gray))

    # Saturation
    avg_saturation = float(np.mean(hsv_pixels[:, 1]))
    saturation_std = float(np.std(hsv_pixels[:, 1]))

    # Dark vs light ratio
    dark_ratio = float(np.mean(gray < 80))
    light_ratio = float(np.mean(gray > 180))

    # Hue diversity (number of distinct hue bins)
    hue_bins = np.histogram(hsv_pixels[:, 0], bins=18, range=(0, 180))[0]
    active_hues = int(np.sum(hue_bins > (len(hsv_pixels) * 0.01)))

    return {
        "dominant_colors": dominant_colors,
        "palette_type": palette_type,
        "avg_brightness": round(avg_brightness, 1),
        "brightness_std": round(brightness_std, 1),
        "contrast_level": "high" if brightness_std > 60 else "medium" if brightness_std > 35 else "low",
        "avg_saturation": round(avg_saturation, 1),
        "saturation_std": round(saturation_std, 1),
        "dark_ratio": round(dark_ratio, 3),
        "light_ratio": round(light_ratio, 3),
        "hue_diversity": active_hues,
    }


def analyze_detail(img_gray):
    """Extract detail/complexity features."""
    # Laplacian variance (sharpness/detail)
    laplacian = cv2.Laplacian(img_gray, cv2.CV_64F)
    laplacian_var = float(np.var(laplacian))
    laplacian_mean = float(np.mean(np.abs(laplacian)))

    # Edge density (Canny)
    edges = cv2.Canny(img_gray, 50, 150)
    edge_density = float(np.mean(edges > 0))

    # Entropy (information density)
    hist = cv2.calcHist([img_gray], [0], None, [256], [0, 256]).flatten()
    hist = hist / hist.sum()
    hist = hist[hist > 0]
    entropy = float(-np.sum(hist * np.log2(hist)))

    # Texture complexity via Gabor filter responses
    gabor_responses = []
    for theta in [0, np.pi/4, np.pi/2, 3*np.pi/4]:
        kernel = cv2.getGaborKernel((15, 15), 3.0, theta, 8.0, 0.5, 0)
        filtered = cv2.filter2D(img_gray, cv2.CV_64F, kernel)
        gabor_responses.append(float(np.std(filtered)))
    texture_complexity = float(np.mean(gabor_responses))

    # Classify detail level
    if laplacian_var > 1500:
        detail_level = "very_high"
    elif laplacian_var > 500:
        detail_level = "high"
    elif laplacian_var > 150:
        detail_level = "medium"
    else:
        detail_level = "low"

    return {
        "sharpness": round(laplacian_var, 1),
        "sharpness_mean": round(laplacian_mean, 1),
        "edge_density": round(edge_density, 4),
        "entropy": round(entropy, 2),
        "texture_complexity": round(texture_complexity, 1),
        "detail_level": detail_level,
    }


def analyze_composition(img_gray, img_rgb):
    """Analyze visual composition and weight distribution."""
    h, w = img_gray.shape

    # Brightness per zone
    zone_brightness = {}
    for zone_name, (x1, y1, x2, y2) in ZONES.items():
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)
        region = img_gray[py1:py2, px1:px2]
        zone_brightness[zone_name] = round(float(np.mean(region)), 1)

    # Visual weight (darker = heavier) — find where the "weight" is
    # Use inverted brightness as weight
    weight = 255.0 - img_gray.astype(float)
    total_weight = weight.sum()

    if total_weight > 0:
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        center_x = float(np.sum(x_coords * weight) / total_weight) / w
        center_y = float(np.sum(y_coords * weight) / total_weight) / h
    else:
        center_x, center_y = 0.5, 0.5

    # Is the image center-focused or edge-focused?
    center_region = img_gray[h//4:3*h//4, w//4:3*w//4]
    edge_brightness = (np.sum(img_gray.astype(float)) - np.sum(center_region.astype(float))) / \
                      (img_gray.size - center_region.size + 1)
    center_brightness = float(np.mean(center_region))

    return {
        "zone_brightness": zone_brightness,
        "visual_weight_center": {
            "x": round(center_x, 3),
            "y": round(center_y, 3),
        },
        "center_vs_edge_brightness": round(center_brightness - edge_brightness, 1),
        "focus": "center" if center_brightness > edge_brightness else "edges",
    }


def analyze_text(img_path, img_rgb, img_gray):
    """Detect and analyze text in the image using OCR."""
    if not HAS_TESSERACT:
        return {"has_text": None, "note": "tesseract not available"}

    h, w = img_gray.shape

    try:
        # Run OCR with bounding box data
        # Use PSM 11 (sparse text) since game headers have varied layouts
        data = pytesseract.image_to_data(
            Image.fromarray(img_rgb),
            output_type=pytesseract.Output.DICT,
            config="--psm 11"
        )

        # Filter for text with reasonable confidence
        text_elements = []
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = int(data["conf"][i]) if data["conf"][i] != "-1" else -1

            if text and conf > 30 and len(text) >= 2:
                bx = data["left"][i]
                by = data["top"][i]
                bw = data["width"][i]
                bh = data["height"][i]

                # Center of text bounding box
                cx = bx + bw / 2
                cy = by + bh / 2

                # Zone classification
                zone = classify_zone(cx, cy, w, h)

                # Text size relative to image
                text_area = bw * bh
                image_area = w * h
                relative_size = text_area / image_area

                # Size classification
                if relative_size > 0.1:
                    size_class = "large"
                elif relative_size > 0.03:
                    size_class = "medium"
                else:
                    size_class = "small"

                # Sample text color (median of pixels in bounding box)
                text_region = img_rgb[
                    max(0, by):min(h, by + bh),
                    max(0, bx):min(w, bx + bw)
                ]

                if text_region.size > 0:
                    # Text pixels are typically the brightest or darkest in the region
                    region_gray = cv2.cvtColor(text_region, cv2.COLOR_RGB2GRAY)
                    region_mean = np.mean(region_gray)

                    # If region is mostly dark, text is likely bright (and vice versa)
                    if region_mean < 128:
                        # Dark background — find bright pixels (text)
                        bright_mask = region_gray > region_mean + 20
                    else:
                        # Bright background — find dark pixels (text)
                        bright_mask = region_gray < region_mean - 20

                    if bright_mask.any():
                        text_pixels = text_region[bright_mask]
                        if len(text_pixels) > 0:
                            text_color = np.median(text_pixels, axis=0).astype(int)
                        else:
                            text_color = np.median(text_region.reshape(-1, 3), axis=0).astype(int)
                    else:
                        text_color = np.median(text_region.reshape(-1, 3), axis=0).astype(int)

                    tr, tg, tb = int(text_color[0]), int(text_color[1]), int(text_color[2])

                    # Background color (surrounding area)
                    pad = 5
                    bg_region = img_rgb[
                        max(0, by - pad):min(h, by + bh + pad),
                        max(0, bx - pad):min(w, bx + bw + pad)
                    ]
                    bg_color = np.median(bg_region.reshape(-1, 3), axis=0).astype(int)
                    br, bg_val, bb = int(bg_color[0]), int(bg_color[1]), int(bg_color[2])

                    # WCAG contrast ratio
                    text_lum = luminance(tr, tg, tb)
                    bg_lum = luminance(br, bg_val, bb)
                    cr = contrast_ratio(text_lum, bg_lum)

                    readability = "good" if cr >= 4.5 else "fair" if cr >= 3.0 else "poor"
                else:
                    tr, tg, tb = 0, 0, 0
                    br, bg_val, bb = 0, 0, 0
                    cr = 1.0
                    readability = "unknown"

                text_elements.append({
                    "text": text,
                    "confidence": conf,
                    "bbox": {"x": bx, "y": by, "w": bw, "h": bh},
                    "zone": zone,
                    "relative_size": round(relative_size, 4),
                    "size_class": size_class,
                    "text_color": {
                        "rgb": [tr, tg, tb],
                        "hex": rgb_to_hex(tr, tg, tb),
                    },
                    "background_color": {
                        "rgb": [br, bg_val, bb],
                        "hex": rgb_to_hex(br, bg_val, bb),
                    },
                    "contrast_ratio": round(cr, 2),
                    "readability": readability,
                })

        # Aggregate text analysis
        has_text = len(text_elements) > 0
        full_text = " ".join([t["text"] for t in text_elements])

        # Find the primary title (largest text element)
        primary_title = None
        if text_elements:
            largest = max(text_elements, key=lambda t: t["relative_size"])
            primary_title = {
                "text": largest["text"],
                "zone": largest["zone"],
                "size_class": largest["size_class"],
                "text_color": largest["text_color"],
                "readability": largest["readability"],
                "contrast_ratio": largest["contrast_ratio"],
            }

        # Text position summary
        zones_used = list(set(t["zone"] for t in text_elements)) if text_elements else []

        # Dominant text color across all elements
        if text_elements:
            all_text_colors = [t["text_color"]["rgb"] for t in text_elements]
            avg_text_color = np.mean(all_text_colors, axis=0).astype(int)
            dominant_text_color = {
                "rgb": [int(avg_text_color[0]), int(avg_text_color[1]), int(avg_text_color[2])],
                "hex": rgb_to_hex(*avg_text_color),
            }
            # Is it white-ish?
            is_white_text = all(c > 180 for c in avg_text_color)
        else:
            dominant_text_color = None
            is_white_text = None

        return {
            "has_text": has_text,
            "text_count": len(text_elements),
            "full_text_detected": full_text if full_text else None,
            "primary_title": primary_title,
            "text_zones": zones_used,
            "dominant_text_color": dominant_text_color,
            "is_white_text": is_white_text,
            "text_elements": text_elements,
        }

    except Exception as e:
        return {
            "has_text": None,
            "error": str(e),
        }


def analyze_single_image(appid: int) -> dict:
    """Run full analysis on a single image. Returns the result dict."""
    img_path = os.path.join(IMAGES_DIR, f"{appid}.jpg")
    output_path = os.path.join(ANALYSIS_DIR, f"{appid}.json")

    # Skip if already analyzed
    if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
        return {"appid": appid, "status": "skipped"}

    if not os.path.exists(img_path):
        return {"appid": appid, "status": "no_image"}

    try:
        # Load image in different color spaces
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            return {"appid": appid, "status": "corrupt_image"}

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        h, w = img_gray.shape

        # Run all analyses
        color_data = analyze_colors(img_rgb, img_hsv)
        detail_data = analyze_detail(img_gray)
        composition_data = analyze_composition(img_gray, img_rgb)
        text_data = analyze_text(img_path, img_rgb, img_gray)

        result = {
            "appid": appid,
            "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "image_size": {"width": w, "height": h},
            "color": color_data,
            "detail": detail_data,
            "composition": composition_data,
            "text": text_data,
        }

        # Save to file
        os.makedirs(ANALYSIS_DIR, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return {"appid": appid, "status": "success"}

    except Exception as e:
        return {"appid": appid, "status": "error", "error": str(e)}


def load_apps(tier: str) -> list:
    """Load app list, optionally filtered by tier."""
    if not os.path.exists(APPS_FILE):
        print(f"❌ {APPS_FILE} not found.")
        sys.exit(1)
    with open(APPS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    apps = data["apps"]
    if tier != "all":
        apps = [a for a in apps if a.get("tier") == tier]
    return apps


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Steam header capsule images"
    )
    parser.add_argument("--limit", type=int, default=0,
                        help="Max images to analyze. 0 = all.")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel workers. Default: 4")
    parser.add_argument("--tier", choices=["all", "top", "mid", "low"],
                        default="all", help="Tier filter. Default: all")
    args = parser.parse_args()

    os.makedirs(ANALYSIS_DIR, exist_ok=True)

    apps = load_apps(args.tier)
    if args.limit > 0:
        apps = apps[:args.limit]

    # Check which are already done
    total_before = len(apps)
    apps_todo = [a for a in apps if not (
        os.path.exists(os.path.join(ANALYSIS_DIR, f"{a['appid']}.json"))
        and os.path.getsize(os.path.join(ANALYSIS_DIR, f"{a['appid']}.json")) > 100
    )]
    already_done = total_before - len(apps_todo)

    print("🔬 Steam Capsulu — Image Analyzer")
    print(f"   Total in scope:   {total_before:,}")
    print(f"   Already analyzed: {already_done:,}")
    print(f"   Remaining:        {len(apps_todo):,}")
    print(f"   Workers:          {args.workers}")
    print(f"   Tier filter:      {args.tier}")
    print(f"   Tesseract OCR:    {'✅ available' if HAS_TESSERACT else '❌ not available'}")
    print(f"   Output:           {ANALYSIS_DIR}/{{appid}}.json")
    print()

    if not apps_todo:
        print("✅ All images already analyzed!")
        return

    stats = {"success": 0, "skipped": 0, "errors": 0, "no_image": 0}
    completed = 0
    start_time = time.time()

    # Use ProcessPoolExecutor for CPU-bound work
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(analyze_single_image, app["appid"]): app
            for app in apps_todo
        }

        for future in as_completed(futures):
            completed += 1
            try:
                result = future.result()
                status = result["status"]
                if status == "success":
                    stats["success"] += 1
                elif status == "skipped":
                    stats["skipped"] += 1
                elif status == "no_image":
                    stats["no_image"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                stats["errors"] += 1

            if completed % 100 == 0 or completed == len(apps_todo):
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(apps_todo) - completed) / rate if rate > 0 else 0
                print(
                    f"  [{completed:,}/{len(apps_todo):,}] "
                    f"✅ {stats['success']} "
                    f"❌ {stats['errors']} "
                    f"📭 {stats['no_image']} — "
                    f"ETA: {eta:.0f}s"
                )

    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"📊 Analysis Summary")
    print(f"{'='*60}")
    print(f"  Analyzed:       {stats['success']:,}")
    print(f"  Already done:   {already_done:,}")
    print(f"  No image:       {stats['no_image']:,}")
    print(f"  Errors:         {stats['errors']:,}")
    print(f"  Time:           {elapsed:.1f}s")
    print(f"  Saved to:       {ANALYSIS_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
