/**
 * ai_forecast.js — Pure In-Browser Deep Learning & Commercial Sales Forecast Engine
 * Part of Capsulu — Steam Capsule Rater
 */

// Global ONNX Runtime Web State
let onnxGlobalSession = null;
let onnxGlobalClasses = null;

/**
 * Initializes the PyTorch ONNX Vision Model in the browser via WebAssembly
 */
async function initOnnxModel() {
    if (typeof ort === 'undefined') {
        console.log('ONNX Runtime Web script not loaded yet; using empirical fallback');
        return;
    }
    try {
        if (ort.env && ort.env.wasm) {
            ort.env.wasm.numThreads = 1;
        }
        onnxGlobalSession = await ort.InferenceSession.create('models/capsulu_global_model.onnx', {
            executionProviders: ['wasm']
        });
        const metaResp = await fetch('models/capsulu_global_classes.json');
        onnxGlobalClasses = await metaResp.json();
        console.log('🤖 Capsulu PyTorch Global Vision Network loaded in browser:', onnxGlobalClasses?.classes);
    } catch (e) {
        console.log('Note: Global ONNX Model deferred or fallback active:', e.message);
    }
}

/**
 * Executes neural network inference or fallback curve to compute expected reviews and sales
 */
async function updateCommercialForecast(scores, cv, knownReviews = null, appid = null, img = null) {
    const s = scores.overallScore;

    let expReviews = 0;
    let p10 = Math.min(99, Math.max(4, Math.round(s * 1.15 - 8)));
    let p50 = Math.min(95, Math.max(2, Math.round(s * 0.95 - 18)));

    // 1. Try running pure PyTorch neural network via ONNX Runtime Web
    if (onnxGlobalSession && img) {
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 224;
            canvas.height = 224;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, 224, 224);
            const imgData = ctx.getImageData(0, 0, 224, 224).data;

            const floatArr = new Float32Array(3 * 224 * 224);
            const mean = [0.485, 0.456, 0.406];
            const std = [0.229, 0.224, 0.225];

            for (let i = 0; i < 224 * 224; i++) {
                const r = imgData[i * 4] / 255.0;
                const g = imgData[i * 4 + 1] / 255.0;
                const b = imgData[i * 4 + 2] / 255.0;

                floatArr[0 * 224 * 224 + i] = (r - mean[0]) / std[0];
                floatArr[1 * 224 * 224 + i] = (g - mean[1]) / std[1];
                floatArr[2 * 224 * 224 + i] = (b - mean[2]) / std[2];
            }

            const inputTensor = new ort.Tensor('float32', floatArr, [1, 3, 224, 224]);
            const results = await onnxGlobalSession.run({ input: inputTensor });
            const rawProbs = results.probabilities.data;

            // Softmax
            let maxLogit = -Infinity;
            for (let i = 0; i < rawProbs.length; i++) if (rawProbs[i] > maxLogit) maxLogit = rawProbs[i];
            let sumExp = 0;
            const probs = [];
            for (let i = 0; i < rawProbs.length; i++) {
                const ep = Math.exp(rawProbs[i] - maxLogit);
                probs.push(ep);
                sumExp += ep;
            }
            for (let i = 0; i < probs.length; i++) probs[i] /= sumExp;

            const classMap = {};
            if (onnxGlobalClasses && onnxGlobalClasses.classes) {
                onnxGlobalClasses.classes.forEach((c, idx) => { classMap[c] = probs[idx]; });
            }

            const pFlops = classMap['1_flops'] || 0.05;
            const pLow = classMap['2_low_visibility'] || 0.15;
            const pMod = classMap['3_moderate'] || 0.30;
            const pSolid = classMap['4_solid_indies'] || 0.35;
            const pMega = classMap['5_megahits'] || 0.15;

            // Weighted review estimate across full Steam commercial tiers:
            // 1_flops: ~3 reviews | 2_low: ~45 reviews | 3_mod: ~250 reviews | 4_solid: ~2,400 reviews | 5_mega: ~95,000 reviews
            const nnExpReviews = Math.round(
                pFlops * 3 +
                pLow * 45 +
                pMod * 250 +
                pSolid * 2400 +
                pMega * 95000
            );

            if (nnExpReviews > 0) {
                expReviews = nnExpReviews;
                p10 = Math.min(99, Math.max(5, Math.round((pMod + pSolid + pMega) * 100)));
                p50 = Math.min(98, Math.max(2, Math.round((pSolid * 0.7 + pMega) * 100)));
            }
        } catch (err) {
            console.log('Neural inference fallback:', err.message);
        }
    }

    // 2. If Neural Model could not execute (unsupported browser or missing WebAssembly)
    if (expReviews === 0) {
        const heroElem = document.getElementById('forecastHeroNum');
        if (heroElem) heroElem.textContent = "AI Offline";

        const heroCopiesElem = document.getElementById('forecastHeroCopies');
        if (heroCopiesElem) heroCopiesElem.textContent = "--";

        const rangeElem = document.getElementById('forecastRange');
        if (rangeElem) rangeElem.textContent = "Modern Browser with WebAssembly Required";

        const salesTopElem = document.getElementById('salesHeroTop');
        if (salesTopElem) salesTopElem.textContent = "N/A";

        const sentElem = document.getElementById('forecastSentence');
        if (sentElem) {
            sentElem.innerHTML = `<span style="color:#ff8585; font-weight:600;">⚠️ The PyTorch Vision Neural Network requires a modern browser (Chrome, Edge, Safari 16+, Firefox) with WebAssembly enabled to run commercial sales forecasting.</span>`;
        }
        return;
    }

    const minRange = Math.max(0, Math.round(expReviews * 0.65));
    const maxRange = Math.round(expReviews * 1.55);
    const estCopies = Math.round(expReviews * 30);
    const minCopies = Math.round(minRange * 30);
    const maxCopies = Math.round(maxRange * 30);

    const fmtFull = (n) => Math.round(Number(n) || 0).toLocaleString('en-US');

    const heroElem = document.getElementById('forecastHeroNum');
    if (heroElem) {
        heroElem.textContent = `~${fmtFull(expReviews)}`;
    }

    const heroCopiesElem = document.getElementById('forecastHeroCopies');
    if (heroCopiesElem) {
        heroCopiesElem.textContent = `~${fmtFull(estCopies)}`;
    }

    const rangeElem = document.getElementById('forecastRange');
    if (rangeElem) {
        rangeElem.textContent = `Expected: ${fmtFull(minCopies)} – ${fmtFull(maxCopies)} sales (${fmtFull(minRange)} – ${fmtFull(maxRange)} reviews)`;
    }

    const salesTopElem = document.getElementById('salesHeroTop');
    if (salesTopElem) {
        salesTopElem.textContent = `~${fmtFull(estCopies)}`;
    }

    const sentElem = document.getElementById('forecastSentence');
    if (sentElem) {
        if (s >= 80) {
            sentElem.innerHTML = `This capsule has a <strong class="hl-green">${p10}% chance</strong> to unlock the Steam algorithm (10+ reviews), with an <strong class="hl-blue">${p50}% probability</strong> of reaching community traction (50+ reviews).`;
        } else if (s >= 60) {
            sentElem.innerHTML = `This capsule has a <strong class="hl-gold">${p10}% chance</strong> to cross the 10-review Steam threshold. Pushing contrast and typography sharpness can boost traction odds above 75%.`;
        } else {
            sentElem.innerHTML = `This capsule is at risk of remaining under the 10-review visibility barrier (<strong class="hl-red">${p10}% odds</strong>). Key fixes needed on lighting hierarchy and text readability.`;
        }
    }

    // 3. Known Reality Reviews Indicator (if game has known Steam reviews)
    const realityRow = document.getElementById('forecastRealityRow');
    const realityText = document.getElementById('forecastRealityText');

    if (knownReviews !== null && knownReviews !== undefined && !isNaN(knownReviews) && Number(knownReviews) > 0) {
        const revCount = Number(knownReviews);
        const now = new Date();
        const d = String(now.getDate()).padStart(2, '0');
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const y = now.getFullYear();
        const dateFormatted = `${d}.${m}.${y}`;

        if (realityRow) realityRow.style.display = 'flex';
        if (realityText) realityText.textContent = `Reality: ${revCount.toLocaleString()} reviews (${dateFormatted})`;
    } else {
        if (realityRow) realityRow.style.display = 'none';
    }
}

/**
 * Smoothly switches to the AI Tab & scrolls to the AI Methodology Section
 */
window.scrollToAiMethodology = function () {
    if (typeof window.setActiveTab === 'function') {
        window.setActiveTab('ai');
    } else if (typeof setActiveTab === 'function') {
        setActiveTab('ai');
    }

    const executeScroll = () => {
        const methodSection = document.getElementById('aiMethodologySection');
        if (methodSection) {
            const rect = methodSection.getBoundingClientRect();
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
            const targetY = Math.max(0, rect.top + scrollTop - 70);

            try {
                window.scrollTo({ top: targetY, behavior: 'smooth' });
            } catch (e) {
                window.scrollTo(0, targetY);
            }

            methodSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            methodSection.classList.remove('pulse-highlight');
            void methodSection.offsetWidth;
            methodSection.classList.add('pulse-highlight');
            setTimeout(() => methodSection.classList.remove('pulse-highlight'), 2500);
        }
    };

    setTimeout(executeScroll, 60);
    setTimeout(executeScroll, 250);
};
