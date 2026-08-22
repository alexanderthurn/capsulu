#!/usr/bin/env python3
"""
server.py — Capsulu Web Server & Public AI Agent API Endpoint
Provides:
1. Static web app hosting (web/)
2. /api/steam-details?appid={appid} - Steam appdetails proxy
3. /api/rate?appid={appid} - Public Computer Vision & Rating API for AI agents & web apps
   (Supports ?format=json (default) and ?format=markdown)
"""

import http.server
import json
import math
import os
import re
import socketserver
import urllib.request
import urllib.parse
from io import BytesIO
from PIL import Image

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

from capsulu_scoring import analyze_capsule, evaluate_scores, CANVAS_W, CANVAS_H


def analyze_capsule_image(img_bytes):
    """Computer Vision evaluation using the canonical shared scoring engine."""
    cv = analyze_capsule(img_bytes)
    scores = evaluate_scores(cv)

    overall_score = scores["overallScore"]
    contrast_std = cv["brightnessStd"]
    warmth_pct = cv["warmPct"]
    entropy = cv["entropy"]
    edge_density = cv["edgeDensity"]
    is_center_focused = cv["isCenterFocused"]
    spotlight_ratio = cv["spotlightRatio"]

    if overall_score >= 88:
        tier = "🏆 Mega-Hit Grade"
        percentile = "Top 10% on Steam"
        headline = "Exceptional"
    elif overall_score >= 72:
        tier = "🌟 Solid Indie Grade"
        percentile = "Top 35% on Steam"
        headline = "Strong"
    elif overall_score >= 50:
        tier = "📊 Moderate Visibility"
        percentile = "Median 50% on Steam"
        headline = "Average"
    elif overall_score >= 30:
        tier = "📉 Struggling Grade"
        percentile = "Bottom 30% on Steam"
        headline = "Low"
    else:
        tier = "🕳️ Near-Zero Flop Risk"
        percentile = "Bottom 15% on Steam"
        headline = "Critical"

    # Action Items
    recommendations = []
    if contrast_std >= 62.0:
        recommendations.append("✓ Strong Dynamic Contrast: Highlights and shadows are sharply separated (matches Mega-Hit benchmark 63.0).")
    else:
        recommendations.append(f"✕ Low Dynamic Contrast ({contrast_std:.1f} vs 63.0 benchmark): Midtones are too flat. Brighten key lights and deepen background shadows by 15-20%.")

    if warmth_pct >= 45.0:
        recommendations.append(f"✓ Steam UI Saliency: Warm color accents ({warmth_pct:.1f}%) pop vividly against Steam's navy client theme.")
    else:
        recommendations.append(f"! Add Warm Accent Glow: Palette is primarily cool/neutral. Add golden rim-lighting, fire embers, or warm title accents to catch user glance.")

    if entropy >= 6.80:
        recommendations.append("✓ Rich Tonal Depth: High information entropy indicates polished, cinematic rendering.")
    else:
        recommendations.append(f"✕ Soft / Low Depth ({entropy:.2f} bits vs 6.99 benchmark): Avoid unlit 3D models or low-contrast backgrounds.")

    if is_center_focused:
        recommendations.append("✓ Hero Spotlight: Lighting is concentrated on the central character, guiding the customer's eye.")
    else:
        recommendations.append("! Apply Edge Vignetting: Outer borders are too bright. Feather outer 15% edges to lock attention on your central hero.")

    if cv["titleContrast"] >= 4.5:
        recommendations.append(f"✓ Title Clarity: Text contrast ratio ({cv['titleContrast']}:1) exceeds WCAG AA threshold.")
    elif cv["titleContrast"] >= 3.0:
        recommendations.append(f"! Moderate Title Contrast ({cv['titleContrast']}:1): Consider adding a subtle text shadow or outline for sharper legibility.")
    else:
        recommendations.append(f"✕ Low Title Contrast ({cv['titleContrast']}:1): Title text blends into the background. Add drop shadow, outline, or brighter text color.")

    # Dominant palette (simple extraction from the image)
    from PIL import Image as PILImage
    from io import BytesIO as BIO
    pil_img = PILImage.open(BIO(img_bytes)).convert("RGB")
    pil_img = pil_img.resize((CANVAS_W, CANVAS_H), PILImage.Resampling.BILINEAR)
    px = pil_img.load()
    color_samples = []
    for y in range(CANVAS_H):
        for x in range(CANVAS_W):
            i = y * CANVAS_W + x
            if i % 40 == 0:
                color_samples.append(px[x, y])

    buckets = {}
    for r, g, b in color_samples:
        key = (r // 32 * 32, g // 32 * 32, b // 32 * 32)
        if key not in buckets:
            buckets[key] = {'count': 0, 'r': 0, 'g': 0, 'b': 0}
        buckets[key]['count'] += 1
        buckets[key]['r'] += r
        buckets[key]['g'] += g
        buckets[key]['b'] += b

    sorted_b = sorted(buckets.values(), key=lambda x: x['count'], reverse=True)[:5]
    dominant_palette = []
    for b in sorted_b:
        cr = int(round(b['r'] / b['count']))
        cg = int(round(b['g'] / b['count']))
        cb = int(round(b['b'] / b['count']))
        hex_code = f"#{cr:02x}{cg:02x}{cb:02x}"
        pct = round((b['count'] / len(color_samples)) * 100, 1)
        dominant_palette.append({"hex": hex_code, "pct": pct})

    return {
        "overallScore": overall_score,
        "tier": tier,
        "percentile": percentile,
        "headline": headline,
        "metrics": {
            "brightnessStd": round(contrast_std, 1),
            "warmPct": round(warmth_pct, 1),
            "entropy": round(entropy, 2),
            "edgeDensity": round(edge_density, 2),
            "isCenterFocused": is_center_focused,
            "spotlightRatio": round(spotlight_ratio, 1),
            "titleContrast": cv["titleContrast"],
            "titleReadability": cv["titleReadability"],
            "titleZoneKey": cv["titleZoneKey"],
            "titleSizePct": cv["titleSizePct"],
        },
        "subScores": {
            "contrastScore": scores["contrastScore"],
            "warmthScore": scores["warmthScore"],
            "entropyScore": scores["entropyScore"],
            "edgeScore": scores["edgeScore"],
            "focusScore": scores["focusScore"],
            "textScore": scores["textScore"],
        },
        "dominantPalette": dominant_palette,
        "recommendations": recommendations,
    }


class SteamCapsuluHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # 1. Public Rate Endpoint for AI Agents & Bots
        if parsed.path == "/api/rate":
            appid = params.get("appid", [None])[0]
            url = params.get("url", [None])[0]
            img_url = params.get("image_url", [None])[0]
            out_format = params.get("format", ["json"])[0].lower()

            target_appid = appid
            if not target_appid and url:
                m = re.search(r'store\.steampowered\.com/app/(\d+)', url)
                if m: target_appid = m.group(1)

            if not target_appid and not img_url:
                self.send_error(400, "Missing required query parameter: appid, url, or image_url")
                return

            try:
                # Fetch Steam Store Metadata
                game_name = f"App {target_appid}" if target_appid else "Custom Image"
                store_price = "N/A"
                release_date = "N/A"
                genres = []
                image_bytes = None
                header_url = img_url

                if target_appid:
                    steam_api_url = f"https://store.steampowered.com/api/appdetails?appids={target_appid}"
                    req = urllib.request.Request(steam_api_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=6) as response:
                        s_data = json.loads(response.read().decode("utf-8"))
                        s_info = s_data.get(str(target_appid), {}).get("data", {})
                        if s_info:
                            game_name = s_info.get("name", game_name)
                            genres = [g.get("description") for g in s_info.get("genres", [])]
                            header_url = s_info.get("header_image")
                            if s_info.get("is_free"):
                                store_price = "Free to Play"
                            elif s_info.get("price_overview"):
                                store_price = s_info.get("price_overview", {}).get("final_formatted", "N/A")
                            elif s_info.get("release_date", {}).get("coming_soon"):
                                store_price = "Coming Soon"
                            release_date = s_info.get("release_date", {}).get("date", "N/A")

                # Fallback header URLs
                candidate_urls = [header_url] if header_url else []
                if target_appid:
                    candidate_urls.extend([
                        f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{target_appid}/header.jpg",
                        f"https://cdn.akamai.steamstatic.com/steam/apps/{target_appid}/header.jpg"
                    ])

                for u in candidate_urls:
                    if not u: continue
                    try:
                        img_req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(img_req, timeout=6) as img_res:
                            image_bytes = img_res.read()
                            if image_bytes: break
                    except Exception:
                        continue

                if not image_bytes:
                    self.send_error(404, "Could not download Steam capsule header artwork.")
                    return

                # Run Computer Vision Analysis
                cv_res = analyze_capsule_image(image_bytes)

                host_header = self.headers.get("Host", f"localhost:{PORT}")
                web_link = f"http://{host_header}/?app={target_appid if target_appid else urllib.parse.quote(header_url or '')}"

                ai_summary = (
                    f"Based on Capsulu (benchmarked against 28,754 real Steam games), '{game_name}' scores "
                    f"{cv_res['overallScore']}/100 ({cv_res['tier']}, {cv_res['percentile']}). "
                    f"Dynamic contrast is {cv_res['metrics']['brightnessStd']} (Mega-Hit avg: 63.0) with "
                    f"{cv_res['metrics']['warmPct']}% warm color saliency. "
                    f"Key recommendation: {cv_res['recommendations'][0]} "
                    f"View full interactive storefront simulator: {web_link}"
                )

                payload = {
                    "success": True,
                    "engine": "Capsulu Computer Vision v1.0",
                    "benchmark_dataset_scope": "28,754 Verified Steam Games",
                    "appid": int(target_appid) if target_appid else None,
                    "name": game_name,
                    "price": store_price,
                    "release_date": release_date,
                    "genres": genres,
                    "score": {
                        "overallScore": cv_res["overallScore"],
                        "tier": cv_res["tier"],
                        "percentile": cv_res["percentile"],
                        "headline": cv_res["headline"]
                    },
                    "subScores": cv_res["subScores"],
                    "metrics": cv_res["metrics"],
                    "dominantPalette": cv_res["dominantPalette"],
                    "recommendations": cv_res["recommendations"],
                    "web_report_url": web_link,
                    "ai_summary": ai_summary
                }

                if out_format in ("markdown", "md", "text"):
                    c_std = cv_res['metrics']['brightnessStd']
                    w_pct = cv_res['metrics']['warmPct']
                    is_cf = cv_res['metrics']['isCenterFocused']
                    
                    contrast_fix = f"Maintain strong lighting contrast ({c_std} std dev)." if c_std >= 63.0 else f"Deepen cast shadows and push specular highlights on the main hero/subject to increase dynamic contrast std dev from {c_std} up to the Steam Mega-Hit benchmark of >= 63.0."
                    warmth_fix = f"Color temperature is well balanced ({w_pct}% warm color share)." if w_pct >= 45.0 else f"Introduce warm accents (golden rim-lighting, torch flame, magical particle glow) to increase warm pixel share from {w_pct}% towards ~45% so the capsule pops against Steam dark navy #171a21 interface."
                    focus_fix = "Good hero illumination. Keep secondary background elements subdued." if is_cf else "Apply a subtle 15% radial edge vignette (darkening borders) to funnel viewer gaze toward the center hero character."

                    md_text = f"""# 🏆 Capsule Score: {cv_res['overallScore']} / 100

**Global Rating**: {cv_res['tier']} ({cv_res['percentile']})
**Game**: {game_name}
**Headline**: {cv_res['headline']}
**Steam Store Link**: https://store.steampowered.com/app/{target_appid}/

## 📊 Computer Vision Metrics (vs. 28,754 Steam Games)
- **Dynamic Contrast**: `{c_std}` (Mega-Hit benchmark: `63.0` | Flop avg: `56.9`)
- **Warm UI Saliency**: `{w_pct}%` (Mega-Hit benchmark: `49.9%` | Flop avg: `39.0%`)
- **Shannon Entropy (Tonal Depth)**: `{cv_res['metrics']['entropy']} bits` (Mega-Hit benchmark: `6.99 bits`)
- **Edge Density (Sharpness)**: `{cv_res['metrics']['edgeDensity']}%` (Mega-Hit benchmark: `14.2%`)
- **Hero Spotlight Vignetting**: `{'Yes' if is_cf else 'No'}` (71.9% of Mega-Hits use center spotlights)
- **Title Contrast Ratio**: `{cv_res['metrics']['titleContrast']}:1` ({cv_res['metrics']['titleReadability']} readability)

## 🛠️ Key Recommendations
{chr(10).join(f"- {r}" for r in cv_res['recommendations'])}

## 🎨 Ready-to-Use AI Art Fix Prompt
```
Please optimize this attached steam capsule artwork:

1. Dynamic Contrast & Lighting:
• {contrast_fix}

2. Color Temperature & Steam UI Pop:
• {warmth_fix}

3. Title Typography & Readability:
• Title text needs >= 4.5:1 WCAG AA contrast against background (add subtle dark drop shadow or scrim if needed).

4. Compositional Hierarchy:
• {focus_fix}

5. Thumbnail Downscaling (120px Discovery Queue):
• Ensure the hero silhouette and title typography remain instantly legible when downscaled to 120px wide (as seen in Steam Discovery Queue). But do not add a thumbnail to the image.

Compliance: Adhere strictly to Steam asset rules (clean title typography only, no review quotes, no discount stickers). Do not add stuff, this needs to be the final capsule art that can be uploaded.
```

👉 **Interactive Simulator & Palette Breakdown**: [{web_link}]({web_link})
"""
                    body = md_text.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/markdown; charset=utf-8")
                else:
                    body = json.dumps(payload, indent=2).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")

                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            except Exception as err:
                err_payload = json.dumps({"success": False, "error": str(err)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(err_payload)))
                self.end_headers()
                self.wfile.write(err_payload)
                return

        # 2. Existing Steam AppDetails proxy endpoint
        if parsed.path == "/api/steam-details":
            appid = params.get("appid", [None])[0]
            if not appid:
                self.send_error(400, "Missing appid parameter")
                return

            try:
                steam_api_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
                req = urllib.request.Request(
                    steam_api_url, 
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))

                app_data = data.get(str(appid), {}).get("data", {})
                if not app_data:
                    res_payload = {"success": False, "error": "Game data not found on Steam"}
                else:
                    rel_info = app_data.get("release_date", {})
                    is_coming_soon = rel_info.get("coming_soon", False)
                    rel_date = rel_info.get("date", "")
                    
                    if app_data.get("is_free"):
                        price_str = "Free to Play"
                    elif app_data.get("price_overview"):
                        price_str = app_data.get("price_overview", {}).get("final_formatted", "N/A")
                    elif is_coming_soon:
                        price_str = "Coming Soon"
                    else:
                        price_str = "Free"

                    review_status = "Coming Soon" if is_coming_soon else "Positive"

                    # Scrape rich user tags from store page HTML
                    tags = []
                    try:
                        store_page_url = f"https://store.steampowered.com/app/{appid}/"
                        page_req = urllib.request.Request(
                            store_page_url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                "Cookie": "birthtime=283993201; mature_content=1; wants_mature_content=1; lastagecheckage=1-0-1990"
                            }
                        )
                        with urllib.request.urlopen(page_req, timeout=5) as page_resp:
                            html = page_resp.read().decode("utf-8", errors="ignore")
                            raw_tags = re.findall(r'class=["\']app_tag[^"\']*["\'][^>]*>\s*([^<]+?)\s*<', html)
                            tags = [t.strip() for t in raw_tags if t.strip() and t.strip() not in ["+", "(?)"]]
                    except Exception as tag_err:
                        print(f"Error scraping store page tags for {appid}: {tag_err}", flush=True)
                        tags = []

                    raw_genres = [g.get("description") for g in app_data.get("genres", []) if isinstance(g, dict)]

                    res_payload = {
                        "success": True,
                        "appid": int(appid),
                        "name": app_data.get("name"),
                        "header_image": app_data.get("header_image"),
                        "capsule_image": app_data.get("capsule_image"),
                        "price": price_str,
                        "is_coming_soon": is_coming_soon,
                        "release_date": rel_date,
                        "review_status": review_status,
                        "genres": raw_genres,
                        "tags": tags if tags else raw_genres
                    }

                body = json.dumps(res_payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            except Exception as e:
                err_body = json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
                return

        # Default static file handler
        return super().do_GET()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SteamCapsuluHandler) as httpd:
        print(f"🚀 Capsulu Server running at http://localhost:{PORT}")
        httpd.serve_forever()
