/**
 * ai_forecast.js — Pure In-Browser Deep Learning & Commercial Sales Forecast Engine
 * Part of Capsulu — Steam Capsule Rater
 */

// Global ONNX Runtime Web State
let onnxIndieSession = null;
let onnxIndieClasses = null;

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
        onnxIndieSession = await ort.InferenceSession.create('models/capsulu_indie_model.onnx', {
            executionProviders: ['wasm']
        });
        const metaResp = await fetch('models/capsulu_indie_classes.json');
        onnxIndieClasses = await metaResp.json();
        console.log('🤖 Capsulu PyTorch Neural Network loaded in browser:', onnxIndieClasses?.classes);
    } catch (e) {
        console.log('Note: ONNX Model deferred or fallback active:', e.message);
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
    if (onnxIndieSession && img) {
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
            const results = await onnxIndieSession.run({ input: inputTensor });
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
            if (onnxIndieClasses && onnxIndieClasses.classes) {
                onnxIndieClasses.classes.forEach((c, idx) => { classMap[c] = probs[idx]; });
            }

            const pZero = classMap['indie_0_zero'] || 0.1;
            const p1_5 = classMap['indie_1_to_5'] || 0.2;
            const p6_10 = classMap['indie_6_to_10'] || 0.2;
            const p11_100 = classMap['indie_11_to_100'] || 0.3;
            const p100_500 = classMap['indie_100_to_500'] || 0.2;

            const nnExpReviews = Math.round(pZero * 0 + p1_5 * 3 + p6_10 * 8 + p11_100 * 45 + p100_500 * 260);
            if (nnExpReviews > 0) {
                expReviews = nnExpReviews;
                p10 = Math.min(99, Math.max(5, Math.round((p6_10 * 0.5 + p11_100 + p100_500) * 100)));
                p50 = Math.min(95, Math.max(2, Math.round((p100_500 + p11_100 * 0.45) * 100)));
            }
        } catch (err) {
            console.log('Neural inference fallback:', err.message);
        }
    }

    // 2. If Neural Model could not execute (unsupported browser or missing WebAssembly)
    if (expReviews === 0) {
        const heroElem = document.getElementById('forecastHeroNum');
        if (heroElem) heroElem.textContent = "AI Offline";

        const rangeElem = document.getElementById('forecastRange');
        if (rangeElem) rangeElem.textContent = "WebAssembly Acceleration Unavailable";

        const copiesElem = document.getElementById('forecastCopies');
        if (copiesElem) copiesElem.textContent = "Modern Browser Required";

        const salesTopElem = document.getElementById('salesHeroTop');
        if (salesTopElem) salesTopElem.textContent = "N/A";

        const sentElem = document.getElementById('forecastSentence');
        if (sentElem) {
            sentElem.innerHTML = `<span style="color:#ff8585; font-weight:600;">⚠️ The PyTorch Vision Neural Network requires a modern browser (Chrome, Edge, Safari 16+, Firefox) with WebAssembly enabled. Please update your browser to unlock AI commercial sales forecasting.</span>`;
        }
        return;
    }

    const minRange = Math.max(0, Math.round(expReviews * 0.65));
    const maxRange = Math.round(expReviews * 1.55);
    const estCopies = Math.round(expReviews * 30);

    const fmtNum = (n) => n >= 10000 ? `${(n / 1000).toFixed(1)}k` : n.toLocaleString();

    const heroElem = document.getElementById('forecastHeroNum');
    if (heroElem) {
        heroElem.textContent = `~${fmtNum(expReviews)}`;
    }

    const rangeElem = document.getElementById('forecastRange');
    if (rangeElem) {
        rangeElem.textContent = `Expected: ${fmtNum(minRange)} – ${fmtNum(maxRange)} reviews`;
    }

    const copiesElem = document.getElementById('forecastCopies');
    if (copiesElem) {
        copiesElem.textContent = `~${fmtNum(estCopies)} copies sold`;
    }

    const salesTopElem = document.getElementById('salesHeroTop');
    if (salesTopElem) {
        salesTopElem.textContent = `~${fmtNum(estCopies)}`;
    }

    const sentElem = document.getElementById('forecastSentence');
    if (sentElem) {
        if (s >= 80) {
            sentElem.innerHTML = `Your capsule has a <strong class="hl-green">${p10}% chance</strong> to unlock the Steam algorithm (10+ reviews), with an <strong class="hl-blue">${p50}% probability</strong> of reaching community traction (50+ reviews).`;
        } else if (s >= 60) {
            sentElem.innerHTML = `Your capsule has a <strong class="hl-gold">${p10}% chance</strong> to cross the 10-review Steam threshold. Pushing contrast and typography sharpness can boost traction odds above 75%.`;
        } else {
            sentElem.innerHTML = `Your capsule is at risk of remaining under the 10-review visibility barrier (<strong class="hl-red">${p10}% odds</strong>). Key fixes needed on lighting hierarchy and text readability.`;
        }
    }
}

/**
 * Smoothly scrolls to the AI Methodology & Deep Analysis Section
 */
window.scrollToAiMethodology = function() {
    if (typeof currentTab !== 'undefined' && currentTab !== 'home') {
        if (typeof setActiveTab === 'function') setActiveTab('home');
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

    setTimeout(executeScroll, 50);
    setTimeout(executeScroll, 250);
};
