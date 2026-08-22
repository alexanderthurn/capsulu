/**
 * cv_engine.js — Pure Client-Side Computer Vision & Heuristic Scoring Engine
 * Part of Capsulu — Steam Capsule Rater
 * Matches capsulu_scoring.py canonical implementation
 */

var CANVAS_WIDTH = 460;
var CANVAS_HEIGHT = 215;

function round(val, dec) {
    return Number(val.toFixed(dec));
}

function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

/**
 * Pure JavaScript Computer Vision Engine
 */
function runComputerVision(img) {
    const cvCanvas = document.getElementById('cvCanvas') || document.createElement('canvas');
    cvCanvas.width = CANVAS_WIDTH;
    cvCanvas.height = CANVAS_HEIGHT;
    const ctx = cvCanvas.getContext('2d');
    
    ctx.drawImage(img, 0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    const imgData = ctx.getImageData(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    const data = imgData.data;
    const totalPixels = CANVAS_WIDTH * CANVAS_HEIGHT;

    const lumArray = new Float32Array(totalPixels);
    const lumHist = new Uint32Array(256);

    let sumLum = 0;
    let sumLumSq = 0;
    let sumSat = 0;
    let warmCount = 0;
    let coolCount = 0;
    let neutralCount = 0;
    let darkCount = 0;
    let lightCount = 0;

    const colorSamples = [];

    for (let i = 0; i < totalPixels; i++) {
        const r = data[i * 4];
        const g = data[i * 4 + 1];
        const b = data[i * 4 + 2];

        const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        lumArray[i] = lum;
        sumLum += lum;
        sumLumSq += lum * lum;

        const lumByte = Math.min(255, Math.floor(lum));
        lumHist[lumByte]++;

        if (lum < 80) darkCount++;
        if (lum > 180) lightCount++;

        const warmth = (r * 1.0 + g * 0.5) - (b * 1.0 + g * 0.2);
        if (warmth > 25) warmCount++;
        else if (warmth < -25) coolCount++;
        else neutralCount++;

        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const delta = max - min;
        const sat = max === 0 ? 0 : (delta / max) * 255;
        sumSat += sat;

        if (i % 40 === 0) {
            colorSamples.push([r, g, b]);
        }
    }

    const avgBrightness = sumLum / totalPixels;
    const variance = (sumLumSq / totalPixels) - (avgBrightness * avgBrightness);
    const brightnessStd = Math.sqrt(Math.max(0, variance));
    const avgSaturation = sumSat / totalPixels;

    let entropy = 0;
    for (let i = 0; i < 256; i++) {
        if (lumHist[i] > 0) {
            const p = lumHist[i] / totalPixels;
            entropy -= p * Math.log2(p);
        }
    }

    let edgeCount = 0;
    const w = CANVAS_WIDTH;
    const h = CANVAS_HEIGHT;

    for (let y = 1; y < h - 1; y += 2) {
        for (let x = 1; x < w - 1; x += 2) {
            const gx =
                -1 * lumArray[(y - 1) * w + (x - 1)] + 1 * lumArray[(y - 1) * w + (x + 1)] +
                -2 * lumArray[y * w + (x - 1)] + 2 * lumArray[y * w + (x + 1)] +
                -1 * lumArray[(y + 1) * w + (x - 1)] + 1 * lumArray[(y + 1) * w + (x + 1)];

            const gy =
                -1 * lumArray[(y - 1) * w + (x - 1)] + -2 * lumArray[(y - 1) * w + x] + -1 * lumArray[(y - 1) * w + (x + 1)] +
                1 * lumArray[(y + 1) * w + (x - 1)] + 2 * lumArray[(y + 1) * w + x] + 1 * lumArray[(y + 1) * w + (x + 1)];

            const magnitude = Math.sqrt(gx * gx + gy * gy);
            if (magnitude > 45) edgeCount++;
        }
    }
    const edgeDensity = (edgeCount / (totalPixels / 4)) * 100;

    const centerStartX = Math.floor(w * 0.25);
    const centerEndX = Math.floor(w * 0.75);
    const centerStartY = Math.floor(h * 0.2);
    const centerEndY = Math.floor(h * 0.8);

    let centerSum = 0;
    let centerCount = 0;
    let borderSum = 0;
    let borderCount = 0;

    for (let y = 0; y < h; y += 3) {
        for (let x = 0; x < w; x += 3) {
            const val = lumArray[y * w + x];
            if (x >= centerStartX && x <= centerEndX && y >= centerStartY && y <= centerEndY) {
                centerSum += val;
                centerCount++;
            } else {
                borderSum += val;
                borderCount++;
            }
        }
    }

    const centerBrightness = centerSum / (centerCount || 1);
    const borderBrightness = borderSum / (borderCount || 1);
    const spotlightRatio = centerBrightness - borderBrightness;
    const isCenterFocused = spotlightRatio > 0;

    const dominantColors = extractDominantColors(colorSamples);
    const textAnalysis = analyzeTitleText(data, lumArray, w, h);

    return {
        avgBrightness: round(avgBrightness, 1),
        brightnessStd: round(brightnessStd, 1),
        avgSaturation: round(avgSaturation, 1),
        entropy: round(entropy, 2),
        edgeDensity: round(edgeDensity, 2),
        warmPct: round((warmCount / totalPixels) * 100, 1),
        coolPct: round((coolCount / totalPixels) * 100, 1),
        neutralPct: round((neutralCount / totalPixels) * 100, 1),
        darkRatio: round((darkCount / totalPixels) * 100, 1),
        lightRatio: round((lightCount / totalPixels) * 100, 1),
        isCenterFocused: isCenterFocused,
        spotlightRatio: round(spotlightRatio, 1),
        dominantColors: dominantColors,
        textAnalysis: textAnalysis,
        titleZone: textAnalysis.zoneLabel,
        titleZoneKey: textAnalysis.zoneKey,
        titleSizePct: textAnalysis.sizePct,
        titleSizeClass: textAnalysis.sizeClass,
        titleSizeLabel: textAnalysis.sizeLabel,
        titleContrast: textAnalysis.contrastRatio,
        titleReadability: textAnalysis.readability,
        titleReadabilityLabel: textAnalysis.readabilityLabel
    };
}

/**
 * Detect Game Title Typography Position, Relative Size %, and Contrast Clarity
 */
function analyzeTitleText(rgbaData, lumArray, w, h) {
    const totalPixels = w * h;

    const diffX = new Uint8Array(totalPixels);
    for (let y = 0; y < h; y++) {
        const rowOffset = y * w;
        for (let x = 0; x < w - 1; x++) {
            const idx = rowOffset + x;
            const diff = Math.abs(lumArray[idx + 1] - lumArray[idx]);
            if (diff > 36) diffX[idx] = 1;
        }
    }

    const vertRun = new Int16Array(totalPixels);
    for (let x = 0; x < w - 1; x++) {
        let run = 0;
        for (let y = 0; y < h; y++) {
            const idx = y * w + x;
            if (diffX[idx]) {
                run++;
                vertRun[idx] = run;
            } else {
                if (run > 0) {
                    for (let k = 1; k <= run; k++) {
                        vertRun[(y - k) * w + x] = run;
                    }
                    run = 0;
                }
            }
        }
        if (run > 0) {
            for (let k = 1; k <= run; k++) {
                vertRun[(h - k) * w + x] = run;
            }
        }
    }

    const blockSize = 10;
    const gridCols = Math.floor(w / blockSize);
    const gridRows = Math.floor(h / blockSize);
    const stemBlocks = new Float32Array(gridCols * gridRows);
    const blockMinL = new Float32Array(gridCols * gridRows);
    const blockMaxL = new Float32Array(gridCols * gridRows);
    const blockLums = new Float32Array(gridCols * gridRows);

    for (let by = 0; by < gridRows; by++) {
        const y1 = by * blockSize;
        const y2 = Math.min(h, (by + 1) * blockSize);
        for (let bx = 0; bx < gridCols; bx++) {
            const x1 = bx * blockSize;
            const x2 = Math.min(w, (bx + 1) * blockSize);

            let stemCount = 0;
            let minL = 255;
            let maxL = 0;
            let sumL = 0;
            let count = 0;

            for (let y = y1; y < y2; y++) {
                const rowOffset = y * w;
                for (let x = x1; x < x2; x++) {
                    const idx = rowOffset + x;
                    const l = lumArray[idx];
                    if (l < minL) minL = l;
                    if (l > maxL) maxL = l;
                    sumL += l;
                    count++;

                    if (vertRun[idx] >= 10) {
                        stemCount++;
                    }
                }
            }

            const bRange = maxL - minL;
            const bIdx = by * gridCols + bx;
            blockLums[bIdx] = sumL / (count || 1);
            blockMinL[bIdx] = minL;
            blockMaxL[bIdx] = maxL;

            if (stemCount >= 2 && bRange > 42) {
                const cr = (maxL + 5.0) / (minL + 5.0);
                stemBlocks[bIdx] = stemCount * (bRange / 255.0) * Math.min(10.0, cr);
            }
        }
    }

    let bestBandScore = -1;
    let bestRStart = 0, bestREnd = gridRows;
    let bestCStart = 0, bestCEnd = gridCols;

    for (const bandH of [3, 4, 5, 6]) {
        for (let r0 = 0; r0 <= gridRows - bandH; r0++) {
            const r1 = r0 + bandH;
            const colSums = new Float32Array(gridCols);

            for (let r = r0; r < r1; r++) {
                for (let c = 0; c < gridCols; c++) {
                    colSums[c] += stemBlocks[r * gridCols + c];
                }
            }

            let activeCols = [];
            for (let c = 0; c < gridCols; c++) {
                if (colSums[c] > 1.0) activeCols.push(c);
            }

            if (activeCols.length >= 3) {
                const cMin = activeCols[0];
                const cMax = activeCols[activeCols.length - 1];
                const spanLen = cMax - cMin + 1;

                let energy = 0;
                for (let c = cMin; c <= cMax; c++) {
                    energy += colSums[c];
                }
                const density = energy / Math.max(spanLen, 1);
                const score = energy * Math.sqrt(density);

                if (score > bestBandScore) {
                    bestBandScore = score;
                    bestRStart = r0;
                    bestREnd = r1;
                    bestCStart = cMin;
                    bestCEnd = cMax;
                }
            }
        }
    }

    let cy = 0.5;
    let cx = 0.5;
    let minXNorm = 0.3;
    let maxXNorm = 0.7;

    let titleWeight = 0;
    let sumR = 0;
    let sumC = 0;

    for (let r = bestRStart; r < bestREnd && r < gridRows; r++) {
        for (let c = bestCStart; c <= bestCEnd && c < gridCols; c++) {
            const score = stemBlocks[r * gridCols + c];
            if (score > 0) {
                titleWeight += score;
                sumR += (r - bestRStart) * score;
                sumC += (c - bestCStart) * score;
            }
        }
    }

    if (titleWeight > 0) {
        const cyLocal = sumR / titleWeight;
        const cxLocal = sumC / titleWeight;
        cy = (bestRStart + cyLocal + 0.5) / gridRows;
        cx = (bestCStart + cxLocal + 0.5) / gridCols;
        minXNorm = bestCStart / gridCols;
        maxXNorm = (bestCEnd + 1) / gridCols;
    }

    let yKey = 'mid';
    let yLabel = 'Middle';
    if (cy < 0.38) {
        yKey = 'top';
        yLabel = 'Top';
    } else if (cy > 0.62) {
        yKey = 'bot';
        yLabel = 'Bottom';
    }

    let xKey = 'center';
    let xLabel = 'Center';
    if (minXNorm < 0.12 && cx < 0.44) {
        xKey = 'left';
        xLabel = 'Left';
    } else if (maxXNorm > 0.88 && cx > 0.56) {
        xKey = 'right';
        xLabel = 'Right';
    } else if (cx < 0.38) {
        xKey = 'left';
        xLabel = 'Left';
    } else if (cx > 0.62) {
        xKey = 'right';
        xLabel = 'Right';
    }

    const zoneKey = `${yKey}_${xKey}`;
    const zoneLabel = `${yLabel} ${xLabel}`;

    const spanW = (bestCEnd - bestCStart + 1) * blockSize;
    const spanH = (bestREnd - bestRStart) * blockSize;
    const sizePct = Math.min(45, Math.max(8, round((spanW * spanH / totalPixels) * 100, 1)));

    let sizeClass = "medium";
    let sizeLabel = "Optimal (14-28%)";
    if (sizePct > 28) {
        sizeClass = "large";
        sizeLabel = "Dominant (>28%)";
    } else if (sizePct < 14) {
        sizeClass = "small";
        sizeLabel = "Compact (<14%)";
    }

    let darkest = 255;
    let brightest = 0;
    let bgSamples = [];

    for (let r = bestRStart; r < bestREnd && r < gridRows; r++) {
        for (let c = bestCStart; c <= bestCEnd && c < gridCols; c++) {
            const idx = r * gridCols + c;
            if (stemBlocks[idx] > 0) {
                if (blockMinL[idx] < darkest) darkest = blockMinL[idx];
                if (blockMaxL[idx] > brightest) brightest = blockMaxL[idx];
                bgSamples.push(blockLums[idx]);
            }
        }
    }

    let contrastRatio = 3.5;
    if (brightest > darkest && bgSamples.length > 0) {
        bgSamples.sort((a, b) => a - b);
        const bgEst = bgSamples[Math.floor(bgSamples.length * 0.3)];
        const l1 = brightest / 255.0;
        const l2 = Math.max(0, (darkest + bgEst) / (2 * 255.0));
        contrastRatio = round((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05), 1);
        if (contrastRatio < 1.1) contrastRatio = 1.2;
        if (contrastRatio > 21.0) contrastRatio = 21.0;
    }

    let readability = "good";
    let readabilityLabel = "High Clarity (≥4.5:1)";
    if (contrastRatio >= 4.5) {
        readability = "good";
        readabilityLabel = "High Clarity (≥4.5:1)";
    } else if (contrastRatio >= 3.0) {
        readability = "fair";
        readabilityLabel = "Moderate (3.0–4.5:1)";
    } else {
        readability = "poor";
        readabilityLabel = "Low Contrast (<3.0:1)";
    }

    return {
        zoneKey: zoneKey,
        zoneLabel: zoneLabel,
        sizePct: sizePct,
        sizeClass: sizeClass,
        sizeLabel: sizeLabel,
        contrastRatio: contrastRatio,
        readability: readability,
        readabilityLabel: readabilityLabel
    };
}

function extractDominantColors(samples) {
    if (!samples || !samples.length) return [];

    const buckets = {};
    samples.forEach(s => {
        const r = Array.isArray(s) ? s[0] : (s.r || 0);
        const g = Array.isArray(s) ? s[1] : (s.g || 0);
        const b = Array.isArray(s) ? s[2] : (s.b || 0);
        const qr = Math.floor(r / 32) * 32;
        const qg = Math.floor(g / 32) * 32;
        const qb = Math.floor(b / 32) * 32;
        const key = `${qr},${qg},${qb}`;
        if (!buckets[key]) buckets[key] = { count: 0, r: 0, g: 0, b: 0 };
        buckets[key].count++;
        buckets[key].r += r;
        buckets[key].g += g;
        buckets[key].b += b;
    });

    const sorted = Object.values(buckets).sort((a, b) => b.count - a.count).slice(0, 5);
    const total = samples.length;

    return sorted.map(b => {
        const r = Math.round(b.r / b.count);
        const g = Math.round(b.g / b.count);
        const blue = Math.round(b.b / b.count);
        return {
            hex: rgbToHex(r, g, blue),
            pct: round((b.count / total) * 100, 1)
        };
    });
}

/**
 * Score Evaluation Engine (Strict Multi-Flaw Penalty & Full 0-100 Dynamic Range)
 */
function evaluateScores(cv) {
    let contrastScore = 100;
    if (cv.brightnessStd >= 63.0) {
        contrastScore = Math.min(100, 95 + (cv.brightnessStd - 63.0) * 0.8);
    } else {
        contrastScore = Math.max(0, 100 - (63.0 - cv.brightnessStd) * 3.5);
    }

    let warmthScore = 100;
    if (cv.warmPct >= 45.0) {
        warmthScore = Math.min(100, 95 + (cv.warmPct - 45.0) * 0.25);
    } else {
        warmthScore = Math.max(0, 100 - (45.0 - cv.warmPct) * 2.8);
    }

    let entropyScore = 100;
    if (cv.entropy >= 6.80) {
        entropyScore = Math.min(100, 95 + (cv.entropy - 6.80) * 8.0);
    } else {
        entropyScore = Math.max(0, 100 - (6.80 - cv.entropy) * 35.0);
    }

    let edgeScore = 100;
    if (cv.edgeDensity >= 25.0) {
        edgeScore = Math.min(100, 95 + (cv.edgeDensity - 25.0) * 0.3);
    } else {
        edgeScore = Math.max(0, 100 - (25.0 - cv.edgeDensity) * 3.8);
    }

    let focusScore = 100;
    if (cv.spotlightRatio >= 8.0) {
        focusScore = Math.min(100, 95 + (cv.spotlightRatio - 8.0) * 0.5);
    } else if (cv.spotlightRatio >= 0.0) {
        focusScore = 80 + (cv.spotlightRatio / 8.0) * 15;
    } else {
        focusScore = Math.max(0, 80 + (cv.spotlightRatio) * 3.5);
    }

    let textScore = 100;
    if (cv.titleContrast >= 4.5) {
        textScore = Math.min(100, 95 + (cv.titleContrast - 4.5) * 1.5);
    } else if (cv.titleContrast >= 3.0) {
        textScore = 75 + ((cv.titleContrast - 3.0) / 1.5) * 20;
    } else {
        textScore = Math.max(0, 75 - (3.0 - cv.titleContrast) * 35.0);
    }

    const baseScore =
        contrastScore * 0.22 +
        warmthScore * 0.18 +
        entropyScore * 0.16 +
        edgeScore * 0.14 +
        focusScore * 0.14 +
        textScore * 0.16;

    let flawPenalty = 0;
    if (cv.brightnessStd < 50) flawPenalty += (50 - cv.brightnessStd) * 0.8;
    if (cv.warmPct < 25) flawPenalty += (25 - cv.warmPct) * 0.6;
    if (cv.entropy < 6.2) flawPenalty += (6.2 - cv.entropy) * 12.0;
    if (cv.edgeDensity < 15) flawPenalty += (15 - cv.edgeDensity) * 0.8;
    if (cv.spotlightRatio < -5) flawPenalty += (-5 - cv.spotlightRatio) * 0.7;
    if (cv.titleContrast < 2.5) flawPenalty += (2.5 - cv.titleContrast) * 8.0;

    let overallScore = Math.round(Math.max(1, Math.min(99, baseScore - flawPenalty)));

    let tierName = "Top Commercial Tier";
    let tierBadgeClass = "tier-top";
    let percentile = "Top 5% of Steam Capsules";
    let headline = "Exceptional";
    let summary = "Your capsule has strong visual saliency with punchy contrast and intentional lighting that will stand out on Steam's dark store theme.";

    if (overallScore >= 90) {
        tierName = "Top Commercial Tier";
        tierBadgeClass = "tier-top";
        percentile = "Top 5% of Steam Capsules";
        headline = "Exceptional";
        summary = "Your capsule has strong visual saliency with punchy contrast and intentional lighting that will stand out on Steam's dark store theme.";
    } else if (overallScore >= 75) {
        tierName = "Solid Indie Performer";
        tierBadgeClass = "tier-mid";
        percentile = "Top 25% of Steam Capsules";
        headline = "Strong Visibility";
        summary = "Good overall composition and clarity. Minor tuning to contrast or typography will push it into the top commercial bracket.";
    } else if (overallScore >= 55) {
        tierName = "Moderate Visibility";
        tierBadgeClass = "tier-moderate";
        percentile = "Mid-range Steam Capsule";
        headline = "Needs Contrast Boost";
        summary = "The capsule risks blending into Steam's dark client. Increasing dynamic contrast or boosting warm focal accents is recommended.";
    } else {
        tierName = "Low Visibility Risk";
        tierBadgeClass = "tier-low";
        percentile = "Bottom 20% of Steam Capsules";
        headline = "High Visibility Risk";
        summary = "Artwork lacks necessary contrast, focal separation, or title clarity. High probability of low click-through rates in crowded queues.";
    }

    return {
        overallScore,
        baseScore: Math.round(baseScore),
        flawPenalty: Math.round(flawPenalty),
        contrastScore: Math.round(contrastScore),
        warmthScore: Math.round(warmthScore),
        entropyScore: Math.round(entropyScore),
        edgeScore: Math.round(edgeScore),
        focusScore: Math.round(focusScore),
        textScore: Math.round(textScore),
        tierName,
        tierBadgeClass,
        percentile,
        headline,
        summary
    };
}
