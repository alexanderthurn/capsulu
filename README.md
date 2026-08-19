# Capsulu – The Steam Capsule Rater

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Analyzed Games](https://img.shields.io/badge/benchmark-28%2C754%20Steam%20Games-orange.svg)](output/report.md)

> [!NOTE]
> **Legal Notice**: This project is an independent open-source research and developer tool. It is **not affiliated with, endorsed by, or sponsored by Valve Corporation**. Steam and the Steam logo are trademarks or registered trademarks of Valve Corporation in the U.S. and/or other countries.

**Capsulu** is an open-source Computer Vision engine and storefront competition simulator for evaluating Steam capsule artwork. It benchmarks any game's capsule art against an empirical dataset of **28,754 real Steam games across 5 commercial sales tiers**.

---

## 🌟 Key Features

- **⚡ Instant In-Browser Computer Vision**: Pure client-side pixel analysis calculating Dynamic Contrast (Luminance Standard Deviation), Shannon Entropy (tonal depth), Sobel Edge Density, Warm Accent Share, and Central Spotlight Lighting.
- **🏪 Storefront Competition Simulator (Visual Check)**:
  - **120px Discovery Matrix**: 3×3 gapless micro-thumbnail glance test with your capsule positioned in the exact center against competing Steam hits.
  - **Large Browse Matrix**: Full-scale 3×3 storefront grid view to assess art scale and composition.
- **🎨 Interactive Dominant Color Breakdown**: Integrated **D3.js donut/cake diagram** with bidirectional swatch hover highlighting and exact color percentage shares.
- **📊 28,754 Games Empirical Dataset**: Scientific benchmark comparing top-tier Mega-Hits (>50,000 reviews) directly against Near-Zero Flops (<10 reviews).
- **🔗 Deep Linking**: Shareable direct analysis URLs (`/?app=4429000` or `/?app=https://store.steampowered.com/app/...`).
- **🛠️ Tailored Developer Checklist**: Actionable recommendations on lighting, vignettes, silhouettes, and color temperature.

---

## 📈 Empirical Research Insights (28,754 Games Analyzed)

Our computer vision pipeline analyzed 28,754 Steam capsules to discover what visually distinguishes commercial mega-hits from games with near-zero downloads:

| Visual Dimension | 🏆 Mega-Hits (>50k Reviews) | 🌟 High (10k–50k) | 📊 Moderate (1k–10k) | 📉 Low (100–1k) | 🕳️ Flops (<10 Reviews) |
|---|---|---|---|---|---|
| **Dynamic Contrast (Std Dev)** | **63.0** | 61.8 | 59.7 | 58.1 | **56.9** |
| **Warm Accent Saliency %** | **49.9%** | 47.5% | 44.2% | 41.8% | **39.0%** |
| **Shannon Entropy (Bits)** | **6.99** | 6.85 | 6.62 | 6.41 | **6.18** |
| **Edge Density (Sharpness)** | **14.2%** | 13.8% | 12.9% | 12.1% | **11.2%** |
| **Center Spotlight Vignette %** | **71.9%** | 68.4% | 63.1% | 58.5% | **52.4%** |

### The "Winning Capsule" Visual Formula:
1. **Dynamic Lighting vs. Flat Midtones**: Mega-hits maintain a contrast score of **63.0** (vs 56.9 for flops). Highlights and shadows are sharply separated.
2. **Warm Saliency Advantage**: **49.9%** of top games utilize warm accents (gold, amber, crimson) that trigger immediate chromatic pop against Steam's dark navy client theme.
3. **Hero Spotlight Composition**: **71.9%** of top games use center-focused lighting with subtle perimeter vignetting to lock viewer gaze within the 1-second Steam browsing glance.

---

## 🚀 Quickstart & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/alexanderthurn/steam-capsulu.git
cd steam-capsulu
```

### 2. Install Python Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
python3 server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

## 📁 Repository Structure

```
steam-capsulu/
├── web/                           # Client-side web application
│   ├── index.html                 # Main interface & dashboard
│   ├── style.css                  # Steam dark theme & responsive styles
│   ├── app.js                     # Pure JS computer vision & scoring engine
│   └── benchmarks.json            # Curated statistical benchmark dataset
├── output/
│   └── report.md                  # Comprehensive empirical research report
├── 1_collect_appids.py            # Scrapes Steam App IDs across sales tiers
├── 2_download_capsules.py         # Batch downloads 460x215 capsule images
├── 3_fetch_metrics.py             # Enriches dataset with Steam store metadata
├── 4_mosaic.py                    # Generates comparative visual mosaics
├── 5_analyze_images.py            # Python OpenCV batch image analysis pipeline
├── 6_generate_report.py           # Statistical report generator & chart plotter
├── export_benchmarks.py           # Exports clean benchmarks.json for the web app
├── server.py                      # Local development server & Steam API proxy
├── requirements.txt               # Python package requirements
├── LICENSE                        # MIT License
└── README.md                      # Documentation
```

---

## 🔬 Computer Vision Methodology

Capsulu processes artwork in real time using HTML5 Canvas pixel manipulation:

- **Luminance Std Dev (Dynamic Contrast)**: $\sigma = \sqrt{\frac{1}{N}\sum (L_i - \bar{L})^2}$ where $L = 0.2126R + 0.7152G + 0.0722B$.
- **Shannon Entropy (Tonal Richness)**: $H = -\sum p(i) \log_2 p(i)$ across the 256-bin luminance histogram.
- **Sobel Operator (Edge Density)**: Convolves $3\times3$ horizontal and vertical Sobel gradient kernels across pixels to calculate structural sharpness.
- **Chromatic Warmth Ratio**: Measures red/amber dominance against Steam's `#1b2838` background.
- **Spatial Spotlight Quotient**: Compares center rectangle luminance against outer border luminance.

---

## ⚖️ Legal Disclaimer

This project is an independent open-source research and developer tool. It is not affiliated with, endorsed by, or sponsored by Valve Corporation. Steam and the Steam logo are trademarks or registered trademarks of Valve Corporation in the U.S. and/or other countries.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
