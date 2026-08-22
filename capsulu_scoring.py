#!/usr/bin/env python3
"""
capsulu_scoring.py — Canonical Capsulu Computer Vision & Scoring Engine (Python)

Faithful port of the client-side engine in web/app.js:
  - runComputerVision()  → analyze_capsule()
  - analyzeTitleText()   → _analyze_title_text()
  - evaluateScores()     → evaluate_scores()

Usage:
    from capsulu_scoring import score_image
    result = score_image("data/images/730.jpg")
    print(result["overall_score"])  # 0-100
"""

import math
from io import BytesIO
from PIL import Image

# Canonical capsule analysis resolution (matches app.js CANVAS_WIDTH/HEIGHT)
CANVAS_W = 460
CANVAS_H = 215


# ---------------------------------------------------------------------------
# Core CV Pipeline  (mirrors runComputerVision in app.js)
# ---------------------------------------------------------------------------

def analyze_capsule(img_input):
    """
    Run full Computer Vision analysis on a capsule image.

    Args:
        img_input: file path (str) or raw bytes

    Returns:
        dict with all CV metrics matching app.js runComputerVision() output
    """
    if isinstance(img_input, (str,)):
        img = Image.open(img_input).convert("RGB")
    elif isinstance(img_input, bytes):
        img = Image.open(BytesIO(img_input)).convert("RGB")
    else:
        img = img_input.convert("RGB")

    img = img.resize((CANVAS_W, CANVAS_H), Image.Resampling.BILINEAR)
    pixels = img.load()
    w, h = CANVAS_W, CANVAS_H
    total_pixels = w * h

    # Pre-allocate luminance array
    lum_array = [0.0] * total_pixels
    lum_hist = [0] * 256

    sum_lum = 0.0
    sum_lum_sq = 0.0
    sum_sat = 0.0
    warm_count = 0
    cool_count = 0
    neutral_count = 0
    dark_count = 0
    light_count = 0

    color_samples = []

    for y in range(h):
        for x in range(w):
            i = y * w + x
            r, g, b = pixels[x, y]

            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            lum_array[i] = lum
            sum_lum += lum
            sum_lum_sq += lum * lum

            lum_byte = min(255, int(lum))
            lum_hist[lum_byte] += 1

            if lum < 80:
                dark_count += 1
            if lum > 180:
                light_count += 1

            warmth = (r * 1.0 + g * 0.5) - (b * 1.0 + g * 0.2)
            if warmth > 25:
                warm_count += 1
            elif warmth < -25:
                cool_count += 1
            else:
                neutral_count += 1

            max_c = max(r, g, b)
            min_c = min(r, g, b)
            delta = max_c - min_c
            sat = 0 if max_c == 0 else (delta / max_c) * 255
            sum_sat += sat

            if i % 40 == 0:
                color_samples.append((r, g, b))

    avg_brightness = sum_lum / total_pixels
    variance = (sum_lum_sq / total_pixels) - (avg_brightness * avg_brightness)
    brightness_std = math.sqrt(max(0, variance))
    avg_saturation = sum_sat / total_pixels

    # Shannon Entropy
    entropy = 0.0
    for count in lum_hist:
        if count > 0:
            p = count / total_pixels
            entropy -= p * math.log2(p)

    # Sobel Edge Density (step 2)
    edge_count = 0
    for y in range(1, h - 1, 2):
        for x in range(1, w - 1, 2):
            gx = (
                -1 * lum_array[(y - 1) * w + (x - 1)] + 1 * lum_array[(y - 1) * w + (x + 1)] +
                -2 * lum_array[y * w + (x - 1)]       + 2 * lum_array[y * w + (x + 1)] +
                -1 * lum_array[(y + 1) * w + (x - 1)] + 1 * lum_array[(y + 1) * w + (x + 1)]
            )
            gy = (
                -1 * lum_array[(y - 1) * w + (x - 1)] + -2 * lum_array[(y - 1) * w + x] + -1 * lum_array[(y - 1) * w + (x + 1)] +
                 1 * lum_array[(y + 1) * w + (x - 1)] +  2 * lum_array[(y + 1) * w + x] +  1 * lum_array[(y + 1) * w + (x + 1)]
            )
            magnitude = math.sqrt(gx * gx + gy * gy)
            if magnitude > 45:
                edge_count += 1
    edge_density = (edge_count / (total_pixels / 4)) * 100

    # Center vs Border Spotlight Ratio
    cx_start = int(w * 0.25)
    cx_end = int(w * 0.75)
    cy_start = int(h * 0.2)
    cy_end = int(h * 0.8)
    c_sum, c_cnt, b_sum, b_cnt = 0.0, 0, 0.0, 0

    for y in range(0, h, 3):
        for x in range(0, w, 3):
            val = lum_array[y * w + x]
            if cx_start <= x <= cx_end and cy_start <= y <= cy_end:
                c_sum += val
                c_cnt += 1
            else:
                b_sum += val
                b_cnt += 1

    center_brightness = c_sum / max(1, c_cnt)
    border_brightness = b_sum / max(1, b_cnt)
    spotlight_ratio = center_brightness - border_brightness
    is_center_focused = spotlight_ratio > 0

    # Title Text Analysis
    text_analysis = _analyze_title_text(lum_array, w, h)

    return {
        "avgBrightness": round(avg_brightness, 1),
        "brightnessStd": round(brightness_std, 1),
        "avgSaturation": round(avg_saturation, 1),
        "entropy": round(entropy, 2),
        "edgeDensity": round(edge_density, 2),
        "warmPct": round((warm_count / total_pixels) * 100, 1),
        "coolPct": round((cool_count / total_pixels) * 100, 1),
        "neutralPct": round((neutral_count / total_pixels) * 100, 1),
        "darkRatio": round((dark_count / total_pixels) * 100, 1),
        "lightRatio": round((light_count / total_pixels) * 100, 1),
        "isCenterFocused": is_center_focused,
        "spotlightRatio": round(spotlight_ratio, 1),
        "titleContrast": text_analysis["contrastRatio"],
        "titleZoneKey": text_analysis["zoneKey"],
        "titleSizePct": text_analysis["sizePct"],
        "titleSizeClass": text_analysis["sizeClass"],
        "titleReadability": text_analysis["readability"],
    }


# ---------------------------------------------------------------------------
# Title Text Glyph Detector  (mirrors analyzeTitleText in app.js)
# ---------------------------------------------------------------------------

def _analyze_title_text(lum_array, w, h):
    """
    Detect game title typography position, relative size %, and contrast clarity.

    Faithful port of analyzeTitleText() from app.js:
    1. Horizontal gradient steps (letter glyph edges, diff > 36)
    2. Vertical stroke run-length filter (stems >= 10px)
    3. Block-level stem density (10x10 blocks)
    4. Dominant horizontal text band (sliding window 3-6 rows)
    5. Contrast ratio in detected title region
    """
    total_pixels = w * h

    # 1. Horizontal gradient steps
    diff_x = [0] * total_pixels
    for y in range(h):
        row_offset = y * w
        for x in range(w - 1):
            idx = row_offset + x
            diff = abs(lum_array[idx + 1] - lum_array[idx])
            if diff > 36:
                diff_x[idx] = 1

    # 2. Vertical stroke run-length filter
    vert_run = [0] * total_pixels
    for x in range(w - 1):
        run = 0
        for y in range(h):
            idx = y * w + x
            if diff_x[idx]:
                run += 1
                vert_run[idx] = run
            else:
                if run > 0:
                    for k in range(1, run + 1):
                        vert_run[(y - k) * w + x] = run
                    run = 0
        if run > 0:
            for k in range(1, run + 1):
                vert_run[(h - k) * w + x] = run

    # 3. Block-level letter stem density (10x10 blocks)
    block_size = 10
    grid_cols = w // block_size
    grid_rows = h // block_size
    stem_blocks = [0.0] * (grid_cols * grid_rows)
    block_min_l = [0.0] * (grid_cols * grid_rows)
    block_max_l = [0.0] * (grid_cols * grid_rows)
    block_lums = [0.0] * (grid_cols * grid_rows)

    for by in range(grid_rows):
        y1 = by * block_size
        y2 = min(h, (by + 1) * block_size)
        for bx in range(grid_cols):
            x1 = bx * block_size
            x2 = min(w, (bx + 1) * block_size)

            stem_count = 0
            min_l = 255.0
            max_l = 0.0
            sum_l = 0.0
            count = 0

            for y in range(y1, y2):
                row_offset = y * w
                for x in range(x1, x2):
                    idx = row_offset + x
                    l = lum_array[idx]
                    if l < min_l:
                        min_l = l
                    if l > max_l:
                        max_l = l
                    sum_l += l
                    count += 1
                    if vert_run[idx] >= 10:
                        stem_count += 1

            b_range = max_l - min_l
            b_idx = by * grid_cols + bx
            block_lums[b_idx] = sum_l / max(count, 1)
            block_min_l[b_idx] = min_l
            block_max_l[b_idx] = max_l

            if stem_count >= 2 and b_range > 42:
                cr = (max_l + 5.0) / (min_l + 5.0)
                stem_blocks[b_idx] = stem_count * (b_range / 255.0) * min(10.0, cr)

    # 4. Find dominant horizontal text line band (sliding window 3-6 rows)
    best_band_score = -1.0
    best_r_start = 0
    best_r_end = grid_rows
    best_c_start = 0
    best_c_end = grid_cols

    for band_h in (3, 4, 5, 6):
        for r0 in range(grid_rows - band_h + 1):
            r1 = r0 + band_h
            col_sums = [0.0] * grid_cols

            for r in range(r0, r1):
                for c in range(grid_cols):
                    col_sums[c] += stem_blocks[r * grid_cols + c]

            active_cols = [c for c in range(grid_cols) if col_sums[c] > 1.0]

            if len(active_cols) >= 3:
                c_min = active_cols[0]
                c_max = active_cols[-1]
                span_len = c_max - c_min + 1

                energy = sum(col_sums[c] for c in range(c_min, c_max + 1))
                density = energy / max(span_len, 1)
                score = energy * math.sqrt(density)

                if score > best_band_score:
                    best_band_score = score
                    best_r_start = r0
                    best_r_end = r1
                    best_c_start = c_min
                    best_c_end = c_max

    # Calculate centroid of detected title band
    cy = 0.5
    cx = 0.5
    min_x_norm = 0.3
    max_x_norm = 0.7

    title_weight = 0.0
    sum_r = 0.0
    sum_c = 0.0

    for r in range(best_r_start, min(best_r_end, grid_rows)):
        for c in range(best_c_start, min(best_c_end + 1, grid_cols)):
            s = stem_blocks[r * grid_cols + c]
            if s > 0:
                title_weight += s
                sum_r += (r - best_r_start) * s
                sum_c += (c - best_c_start) * s

    if title_weight > 0:
        cy_local = sum_r / title_weight
        cx_local = sum_c / title_weight
        cy = (best_r_start + cy_local + 0.5) / grid_rows
        cx = (best_c_start + cx_local + 0.5) / grid_cols
        min_x_norm = best_c_start / grid_cols
        max_x_norm = (best_c_end + 1) / grid_cols

    # Classify Y axis
    if cy < 0.38:
        y_key, y_label = "top", "Top"
    elif cy > 0.62:
        y_key, y_label = "bot", "Bottom"
    else:
        y_key, y_label = "mid", "Middle"

    # Classify X axis
    if min_x_norm < 0.12 and cx < 0.44:
        x_key, x_label = "left", "Left"
    elif max_x_norm > 0.88 and cx > 0.56:
        x_key, x_label = "right", "Right"
    elif cx < 0.38:
        x_key, x_label = "left", "Left"
    elif cx > 0.62:
        x_key, x_label = "right", "Right"
    else:
        x_key, x_label = "center", "Center"

    zone_key = f"{y_key}_{x_key}"

    span_w = (best_c_end - best_c_start + 1) * block_size
    span_h = (best_r_end - best_r_start) * block_size
    size_pct = min(45, max(8, round((span_w * span_h / total_pixels) * 100, 1)))

    # Size classification
    if size_pct > 28:
        size_class = "large"
    elif size_pct < 14:
        size_class = "small"
    else:
        size_class = "medium"

    # Contrast ratio in detected title text region
    darkest = 255.0
    brightest = 0.0
    bg_samples = []

    for r in range(best_r_start, min(best_r_end, grid_rows)):
        for c in range(best_c_start, min(best_c_end + 1, grid_cols)):
            idx = r * grid_cols + c
            if stem_blocks[idx] > 0:
                if block_min_l[idx] < darkest:
                    darkest = block_min_l[idx]
                if block_max_l[idx] > brightest:
                    brightest = block_max_l[idx]
                bg_samples.append(block_lums[idx])

    contrast_ratio = 3.5
    if brightest > darkest and len(bg_samples) > 0:
        bg_samples.sort()
        bg_est = bg_samples[int(len(bg_samples) * 0.3)]
        l1 = brightest / 255.0
        l2 = max(0, (darkest + bg_est) / (2 * 255.0))
        contrast_ratio = round(
            (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05), 1
        )
        if contrast_ratio < 1.1:
            contrast_ratio = 1.2
        if contrast_ratio > 21.0:
            contrast_ratio = 21.0

    # Readability classification
    if contrast_ratio >= 4.5:
        readability = "good"
    elif contrast_ratio >= 3.0:
        readability = "fair"
    else:
        readability = "poor"

    return {
        "zoneKey": zone_key,
        "sizePct": size_pct,
        "sizeClass": size_class,
        "contrastRatio": contrast_ratio,
        "readability": readability,
    }


# ---------------------------------------------------------------------------
# Score Evaluation Engine  (mirrors evaluateScores in app.js)
# ---------------------------------------------------------------------------

def evaluate_scores(cv):
    """
    Compute the 0-100 overall Capsulu score from CV metrics.
    Exact port of evaluateScores() from app.js with all 6 sub-scores,
    6 flaw checks, and identical weights.

    Args:
        cv: dict from analyze_capsule()

    Returns:
        dict with overallScore, all 6 sub-scores, tier info
    """
    # 1. Dynamic Contrast (Mega-Hit Benchmark: 63.0)
    if cv["brightnessStd"] >= 63.0:
        contrast_score = min(100.0, 95.0 + (cv["brightnessStd"] - 63.0) * 0.8)
    else:
        contrast_score = max(0.0, 100.0 - (63.0 - cv["brightnessStd"]) * 3.5)

    # 2. Warmth / Saliency (Mega-Hit Benchmark: 45.0%)
    if cv["warmPct"] >= 45.0:
        warmth_score = min(100.0, 95.0 + (cv["warmPct"] - 45.0) * 0.2)
    else:
        warmth_score = max(0.0, 100.0 - (45.0 - cv["warmPct"]) * 2.0)

    # 3. Shannon Entropy (Mega-Hit Benchmark: 6.90 bits)
    if cv["entropy"] >= 6.90:
        entropy_score = 98.0
    else:
        entropy_score = max(0.0, 100.0 - (6.90 - cv["entropy"]) * 50.0)

    # 4. Edge Density (Mega-Hit Benchmark: 13.5%)
    if cv["edgeDensity"] >= 13.5:
        edge_score = 95.0
    else:
        edge_score = max(0.0, 100.0 - (13.5 - cv["edgeDensity"]) * 8.0)

    # 5. Hero Spotlight / Composition
    if cv["isCenterFocused"]:
        focus_score = 98.0 if cv["spotlightRatio"] > 10.0 else 85.0
    else:
        focus_score = 45.0

    # 6. Title Typography Contrast (Benchmark: 4.5:1)
    if cv["titleContrast"] >= 4.5:
        text_score = min(100.0, round(92.0 + (cv["titleContrast"] - 4.5) * 2.0))
    elif cv["titleContrast"] >= 3.0:
        text_score = round(60.0 + ((cv["titleContrast"] - 3.0) / 1.5) * 25.0)
    else:
        text_score = max(0.0, round(cv["titleContrast"] * 18.0))

    sub_scores = [contrast_score, warmth_score, entropy_score, edge_score, focus_score, text_score]

    base_score = (
        contrast_score * 0.25 +
        warmth_score  * 0.15 +
        entropy_score * 0.15 +
        edge_score    * 0.15 +
        focus_score   * 0.15 +
        text_score    * 0.15
    )

    # Strict Flaw Penalty (6 checks, matching app.js)
    is_contrast_flaw = cv["brightnessStd"] < 58.0
    is_warmth_flaw   = cv["warmPct"] < 35.0
    is_entropy_flaw  = cv["entropy"] < 6.2
    is_edge_flaw     = cv["edgeDensity"] < 8.0
    is_focus_flaw    = not cv["isCenterFocused"]
    is_text_flaw     = cv["titleContrast"] < 3.0

    flaw_count = sum([
        is_contrast_flaw, is_warmth_flaw, is_entropy_flaw,
        is_edge_flaw, is_focus_flaw, is_text_flaw
    ])
    min_sub = min(sub_scores)

    flaw_penalty = 0.0
    if flaw_count > 0:
        flaw_penalty = flaw_count * 13.0 + max(0.0, (40.0 - min_sub) * 0.8)

    overall_score = max(0, min(100, round(base_score - flaw_penalty)))

    # Tier classification
    if overall_score >= 88:
        tier = "Mega-Hit"
        percentile = "Top 10%"
    elif overall_score >= 72:
        tier = "Solid Indie"
        percentile = "Top 35%"
    elif overall_score >= 50:
        tier = "Moderate"
        percentile = "Median 50%"
    elif overall_score >= 30:
        tier = "Struggling"
        percentile = "Bottom 30%"
    else:
        tier = "Critical"
        percentile = "Bottom 15%"

    return {
        "overallScore": overall_score,
        "contrastScore": round(contrast_score),
        "warmthScore": round(warmth_score),
        "entropyScore": round(entropy_score),
        "edgeScore": round(edge_score),
        "focusScore": round(focus_score),
        "textScore": round(text_score),
        "baseScore": round(base_score),
        "flawPenalty": round(flaw_penalty),
        "tier": tier,
        "percentile": percentile,
    }


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------

def score_image(img_input):
    """
    One-shot: analyze an image and return the full score breakdown.
    All keys use camelCase matching app.js naming convention.

    Args:
        img_input: file path (str) or raw bytes

    Returns:
        dict with overallScore, tier, all sub-scores, and raw CV metrics
    """
    cv = analyze_capsule(img_input)
    scores = evaluate_scores(cv)
    return {
        "overallScore": scores["overallScore"],
        "contrastScore": scores["contrastScore"],
        "warmthScore": scores["warmthScore"],
        "entropyScore": scores["entropyScore"],
        "edgeScore": scores["edgeScore"],
        "focusScore": scores["focusScore"],
        "textScore": scores["textScore"],
        "baseScore": scores["baseScore"],
        "flawPenalty": scores["flawPenalty"],
        "tier": scores["tier"],
        "percentile": scores["percentile"],
        "metrics": cv,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python capsulu_scoring.py <image_path>")
        sys.exit(1)
    result = score_image(sys.argv[1])
    print(f"Overall: {result['overallScore']}/100  ({result['tier']}, {result['percentile']})")
    print(f"  Contrast: {result['contrastScore']}  Warmth: {result['warmthScore']}  "
          f"Entropy: {result['entropyScore']}  Edge: {result['edgeScore']}  "
          f"Focus: {result['focusScore']}  Text: {result['textScore']}")
    m = result['metrics']
    print(f"  CV: brightnessStd={m['brightnessStd']}, warmPct={m['warmPct']}, "
          f"entropy={m['entropy']}, edgeDensity={m['edgeDensity']}, "
          f"spotlightRatio={m['spotlightRatio']}, titleContrast={m['titleContrast']}")

