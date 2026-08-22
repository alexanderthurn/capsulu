/**
 * Render D3 Cake / Donut Diagram for Dominant Colors
 */
function renderPalettePieChart(dominantColors) {
    const svgEl = document.getElementById('palettePieChart');
    const centerLabel = document.getElementById('pieCenterPct');
    if (!svgEl || !dominantColors || !dominantColors.length) return;

    if (centerLabel) centerLabel.textContent = '100%';

    // Use D3 if available
    if (typeof d3 !== 'undefined') {
        const svg = d3.select(svgEl);
        svg.selectAll('*').remove();

        const width = 130;
        const height = 130;
        const radius = Math.min(width, height) / 2;
        const innerRadius = 36;
        const outerRadius = 60;

        const g = svg.append('g')
            .attr('transform', `translate(${width / 2}, ${height / 2})`);

        const pie = d3.pie()
            .value(d => d.pct)
            .sort(null);

        const arc = d3.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius)
            .padAngle(0.03);

        const arcHover = d3.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius + 4)
            .padAngle(0.03);

        const arcs = g.selectAll('.pie-slice')
            .data(pie(dominantColors))
            .enter()
            .append('g')
            .attr('class', 'pie-slice');

        arcs.append('path')
            .attr('d', arc)
            .attr('fill', d => d.data.hex)
            .attr('stroke', '#0e141b')
            .attr('stroke-width', '1.5px')
            .on('mouseenter', function (event, d) {
                d3.select(this).transition().duration(150).attr('d', arcHover);
                if (centerLabel) centerLabel.textContent = d.data.pct + "%";

                // Highlight matching swatch
                const swatches = document.querySelectorAll('.palette-dedicated-panel .swatch-item');
                if (swatches[d.index]) swatches[d.index].classList.add('highlighted');
            })
            .on('mouseleave', function (event, d) {
                d3.select(this).transition().duration(150).attr('d', arc);
                if (centerLabel) centerLabel.textContent = '100%';

                const swatches = document.querySelectorAll('.palette-dedicated-panel .swatch-item');
                if (swatches[d.index]) swatches[d.index].classList.remove('highlighted');
            });
    } else {
        // SVG Pure Math Fallback
        svgEl.innerHTML = '';
        let startAngle = 0;
        dominantColors.forEach(c => {
            const angle = (c.pct / 100) * 360;
            // Draw slice
        });
    }
}

/**
 * Visual Check View Switcher (Small: 1 Column in Left Column | Large: Full Width spanning 2 Columns)
 */
window.switchSimView = function (mode) {
    const simToggleSmall = document.getElementById('simToggleSmall');
    const simToggleLarge = document.getElementById('simToggleLarge');
    const panel = document.getElementById('visualCheckPanel');
    const leftCol = document.querySelector('.top-left-col');
    const genreBenchmarkCard = document.getElementById('genreBenchmarkCard');
    const fullWidthSlot = document.getElementById('visualCheckFullWidthSlot');

    if (!panel) return;

    if (mode === 'small') {
        if (simToggleSmall) simToggleSmall.classList.add('active');
        if (simToggleLarge) simToggleLarge.classList.remove('active');
        panel.classList.remove('sim-panel-fullwidth');

        if (leftCol) {
            if (genreBenchmarkCard && genreBenchmarkCard.parentNode === leftCol) {
                leftCol.insertBefore(panel, genreBenchmarkCard);
            } else {
                leftCol.appendChild(panel);
            }
        }
    } else if (mode === 'large') {
        if (simToggleLarge) simToggleLarge.classList.add('active');
        if (simToggleSmall) simToggleSmall.classList.remove('active');
        panel.classList.add('sim-panel-fullwidth');

        if (fullWidthSlot) {
            fullWidthSlot.appendChild(panel);
            panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
};

/**
 * Capsulu - Computer Vision & Scoring Engine
 * Supports Deep Linking (?app=...), 3x3 Large Grid & Seamless 3x3 Micro Matrix (User in Center).
 */

let benchmarksData = null;
const RECENT_STORAGE_KEY = 'steam_capsulu_recents_v4';

// Active analysis evaluation state
let currentGenreLens = 'all';
let currentCvResult = null;
let currentScores = null;
let currentLoadedImgSrc = null;
let currentLoadedGameName = null;
let currentLoadedAppId = null;
let currentLoadedTags = [];
let currentLoadedGenres = [];

// DOM Elements
const dropZoneArea = document.getElementById('dropZoneArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const steamUrlInput = document.getElementById('steamUrlInput');
const fetchUrlBtn = document.getElementById('fetchUrlBtn');
const genreSelectDropdown = document.getElementById('genreSelectDropdown');
const recentListContainer = document.getElementById('recentListContainer');
const loadingBar = document.getElementById('loadingBar');
const resultsDashboard = document.getElementById('resultsDashboard');
const benchmarkCountBadge = document.getElementById('benchmarkCountBadge');
const cvCanvas = document.getElementById('cvCanvas');
const ctx = cvCanvas.getContext('2d', { willReadFrequently: true });

// Catalog of Top Verified Steam Games for Surrounding Lineups (12+ titles)
const STORE_CATALOG = [
    { name: "ELDEN RING", appid: 1245620, url: "https://store.steampowered.com/app/1245620/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", price: "$59.99" },
    { name: "Hades", appid: 1145360, url: "https://store.steampowered.com/app/1145360/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg", price: "$24.99" },
    { name: "Balatro", appid: 2379780, url: "https://store.steampowered.com/app/2379780/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg", price: "$14.99" },
    { name: "Cyberpunk 2077", appid: 1091500, url: "https://store.steampowered.com/app/1091500/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg", price: "$59.99" },
    { name: "Stardew Valley", appid: 413150, url: "https://store.steampowered.com/app/413150/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg", price: "$14.99" },
    { name: "Hollow Knight", appid: 367520, url: "https://store.steampowered.com/app/367520/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg", price: "$14.99" },
    { name: "Baldur's Gate 3", appid: 1086940, url: "https://store.steampowered.com/app/1086940/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg", price: "$59.99" },
    { name: "Terraria", appid: 105600, url: "https://store.steampowered.com/app/105600/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg", price: "$9.99" },
    { name: "Slay the Spire", appid: 646570, url: "https://store.steampowered.com/app/646570/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/646570/header.jpg", price: "$24.99" },
    { name: "Vampire Survivors", appid: 1794680, url: "https://store.steampowered.com/app/1794680/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1794680/header.jpg", price: "$4.99" },
    { name: "Deep Rock Galactic", appid: 548430, url: "https://store.steampowered.com/app/548430/", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/548430/header.jpg", price: "$29.99" },
    { name: "DICEPTION", appid: 4429000, url: "https://store.steampowered.com/app/4429000/DICEPTION/", imageUrl: "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4429000/56bd8aa0cf2d865acbae5501824e33c4dd8c2269/header.jpg?t=1785770104", price: "4,99€" },
    { name: "Melodan", appid: 4987230, url: "https://store.steampowered.com/app/4987230/Melodan/", imageUrl: "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4987230/833a1d7f3a40629d6c8edd334ad871425ccd644b/header.jpg?t=1786736037", price: "Coming Soon" }
];

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
    cvCanvas.width = CANVAS_WIDTH;
    cvCanvas.height = CANVAS_HEIGHT;
    setupEventListeners();
    await loadBenchmarks();
    initOnnxModel();
    initRecentList();
    checkDeepLink();
    checkInitialTab();
});

/**
 * Check and restore active tab & chart mode from URL query param or hash on initial load
 */
function checkInitialTab() {
    const params = new URLSearchParams(window.location.search);
    const tabFromUrl = params.get('tab') || (window.location.hash ? window.location.hash.replace('#', '') : null);
    if (tabFromUrl && (tabFromUrl === 'benchmark' || tabFromUrl === 'ai')) {
        if (typeof window.setActiveTab === 'function') {
            window.setActiveTab(tabFromUrl, false);
        }
    }
    const chartMode = params.get('chart_mode') || params.get('charts');
    if (chartMode && (chartMode === 'all' || chartMode === 'indie')) {
        if (typeof switchChartMode === 'function') {
            switchChartMode(chartMode, false);
        }
    }
    const showcaseFromUrl = params.get('showcase') || params.get('showcase_tab');
    if (showcaseFromUrl && typeof switchShowcaseTab === 'function') {
        currentShowcaseTab = showcaseFromUrl;
    }
}

/**
 * Check and execute URL deep link on initial load
 */
function checkDeepLink() {
    const params = new URLSearchParams(window.location.search);
    const query = params.get('app') || params.get('url') || params.get('appid');
    if (query && query.trim()) {
        steamUrlInput.value = query.trim();
        handleUrlInput(false);
    }
}

/**
 * Load pre-compiled clean benchmark dataset
 */
async function loadBenchmarks() {
    try {
        const res = await fetch('benchmarks.json?v=' + Date.now(), { cache: 'no-store' });
        if (res.ok) {
            benchmarksData = await res.json();
            if (benchmarksData.overall && benchmarksData.overall.total_games_analyzed) {
                if (benchmarkCountBadge) {
                    benchmarkCountBadge.textContent = `${benchmarksData.overall.total_games_analyzed.toLocaleString()} Games Analyzed`;
                }
                populateGenreDropdowns(currentLoadedGenres || [], currentLoadedTags || []);
            }
            if (benchmarksData.showcases || benchmarksData.top_rated) {
                switchShowcaseTab(currentShowcaseTab, false);
            }
        }
    } catch (e) {
        console.warn('Error loading benchmarks.json:', e);
    }
}

/**
 * Setup Event Listeners
 */
function setupEventListeners() {
    const navHomeBtn = document.getElementById('navHomeBtn');
    const navBenchmarkBtn = document.getElementById('navBenchmarkBtn');
    const navAiBtn = document.getElementById('navAiBtn');
    const homeView = document.getElementById('homeView');
    const benchmarkView = document.getElementById('benchmarkView');
    const aiView = document.getElementById('aiView');
    const brandHomeLink = document.getElementById('brandHomeLink');

    function setActiveTab(tab, updateUrl = true) {
        if (navHomeBtn) navHomeBtn.classList.toggle('active', tab === 'home');
        if (navBenchmarkBtn) navBenchmarkBtn.classList.toggle('active', tab === 'benchmark');
        if (navAiBtn) navAiBtn.classList.toggle('active', tab === 'ai');

        if (homeView) homeView.style.display = tab === 'home' ? 'block' : 'none';
        if (benchmarkView) benchmarkView.style.display = tab === 'benchmark' ? 'block' : 'none';
        if (aiView) aiView.style.display = tab === 'ai' ? 'block' : 'none';

        if (tab === 'benchmark') {
            if (typeof switchShowcaseTab === 'function') {
                switchShowcaseTab(currentShowcaseTab || 'top_rated', false);
            }
        }

        if (tab === 'ai') {
            const origin = window.location.origin;
            const sysElem = document.getElementById('aiSystemPromptText');
            if (sysElem) sysElem.textContent = sysElem.textContent.replace(/http:\/\/localhost:8000/g, origin);
            const curlElem = document.getElementById('aiCurlSnippet');
            if (curlElem) curlElem.textContent = curlElem.textContent.replace(/http:\/\/localhost:8000/g, origin);
        }

        if (updateUrl) {
            const url = new URL(window.location);
            if (tab === 'home') {
                url.searchParams.delete('tab');
            } else {
                url.searchParams.set('tab', tab);
            }
            window.history.replaceState({}, '', url.toString());
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Expose globally for deep links and tab switching
    window.setActiveTab = setActiveTab;

    if (brandHomeLink) {
        brandHomeLink.addEventListener('click', (e) => {
            e.preventDefault();
            setActiveTab('home');
        });
    }

    if (navHomeBtn) navHomeBtn.addEventListener('click', () => setActiveTab('home'));
    if (navBenchmarkBtn) navBenchmarkBtn.addEventListener('click', () => setActiveTab('benchmark'));
    if (navAiBtn) navAiBtn.addEventListener('click', () => setActiveTab('ai'));

    // Global helper to smoothly scroll to AI Methodology & Analysis Section on the AI Tab
    window.scrollToAiMethodology = function () {
        if (typeof currentTab !== 'undefined' && currentTab !== 'ai') {
            if (typeof setActiveTab === 'function') setActiveTab('ai');
        }

        const executeScroll = () => {
            const methodSection = document.getElementById('aiMethodologySection');
            if (methodSection) {
                // Compute exact absolute page top offset
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
                void methodSection.offsetWidth; // trigger reflow
                methodSection.classList.add('pulse-highlight');
                setTimeout(() => methodSection.classList.remove('pulse-highlight'), 2500);
            }
        };

        setTimeout(executeScroll, 50);
        setTimeout(executeScroll, 250);
    };

    const aiForecastCard = document.getElementById('aiForecastCard');
    if (aiForecastCard) {
        aiForecastCard.style.cursor = 'pointer';
        aiForecastCard.title = 'Click to learn how Capsulu analyzes artwork & forecasts sales';
        aiForecastCard.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollToAiMethodology();
        });
    }

    window.addEventListener('popstate', () => {
        const p = new URLSearchParams(window.location.search);
        const t = p.get('tab') || 'home';
        setActiveTab(t, false);
        checkDeepLink();
    });

    // Visual Check Small / Large View Toggle
    const simToggleSmall = document.getElementById('simToggleSmall');
    const simToggleLarge = document.getElementById('simToggleLarge');
    const simViewSmall = document.getElementById('simViewSmall');
    const simViewLarge = document.getElementById('simViewLarge');

    if (simToggleSmall && simToggleLarge && simViewSmall && simViewLarge) {
        simToggleSmall.addEventListener('click', () => {
            simToggleSmall.classList.add('active');
            simToggleLarge.classList.remove('active');
            simViewSmall.style.display = 'block';
            simViewLarge.style.display = 'none';
        });

        simToggleLarge.addEventListener('click', () => {
            simToggleLarge.classList.add('active');
            simToggleSmall.classList.remove('active');
            simViewSmall.style.display = 'none';
            simViewLarge.style.display = 'block';
        });
    }

    // Chart Lightbox Modal Logic
    const chartLightboxModal = document.getElementById('chartLightboxModal');
    const lightboxBackdrop = document.getElementById('lightboxBackdrop');
    const lightboxCloseBtn = document.getElementById('lightboxCloseBtn');
    const lightboxImg = document.getElementById('lightboxImg');
    const lightboxTitle = document.getElementById('lightboxTitle');

    function openLightbox(src, title) {
        if (!chartLightboxModal || !lightboxImg) return;
        lightboxImg.src = src;
        if (lightboxTitle) lightboxTitle.textContent = title || 'Benchmark Chart';
        chartLightboxModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        if (!chartLightboxModal) return;
        chartLightboxModal.style.display = 'none';
        document.body.style.overflow = '';
        if (lightboxImg) lightboxImg.src = '';
    }

    if (lightboxBackdrop) lightboxBackdrop.addEventListener('click', closeLightbox);
    if (lightboxCloseBtn) lightboxCloseBtn.addEventListener('click', closeLightbox);
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && chartLightboxModal && chartLightboxModal.style.display === 'flex') {
            closeLightbox();
        }
    });

    document.querySelectorAll('.chart-img-wrapper').forEach(wrapper => {
        wrapper.addEventListener('click', () => {
            const src = wrapper.getAttribute('data-chart-src');
            const title = wrapper.getAttribute('data-chart-title');
            if (src) openLightbox(src, title);
        });
    });

    // Empirical Research Charts Gallery Toggle (All vs Indie Funnel)
    const btnChartsAll = document.getElementById('btnChartsAll');
    const btnChartsIndie = document.getElementById('btnChartsIndie');
    if (btnChartsAll) btnChartsAll.addEventListener('click', () => switchChartMode('all', true));
    if (btnChartsIndie) btnChartsIndie.addEventListener('click', () => switchChartMode('indie', true));

    // Benchmark 5x5 Showcase Category Tabs
    document.querySelectorAll('.showcase-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const showcaseKey = btn.getAttribute('data-showcase');
            if (showcaseKey) switchShowcaseTab(showcaseKey, true);
        });
    });

    // Genre Comparison Lens Switcher Listeners
    document.querySelectorAll('.genre-pill-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const selectedGenre = btn.getAttribute('data-genre') || 'all';
            switchGenreLens(selectedGenre);
        });
    });

    // Synchronized Genre/Tag Dropdowns Listeners across all panels
    document.addEventListener('change', (e) => {
        if (e.target && e.target.classList.contains('genre-sync-dropdown')) {
            const val = e.target.value;
            switchGenreLens(val);
        }
    });

    // Clickable Visual Check Competitor Capsule Lineup
    document.addEventListener('click', (e) => {
        const item = e.target.closest('.clickable-sim-item');
        if (item) {
            const appid = item.getAttribute('data-appid');
            const imageUrl = item.getAttribute('data-image-url');
            const name = item.getAttribute('data-name');
            const isUser = item.getAttribute('data-is-user') === 'true';
            openSimulatorGame(appid, imageUrl, name, isUser);
        }
    });

    // AI Tab & Hub Copy Listeners
    const btnQuickCopyAgentPrompt = document.getElementById('btnQuickCopyAgentPrompt');
    const btnToggleAiAdvanced = document.getElementById('btnToggleAiAdvanced');
    const aiAdvancedBody = document.getElementById('aiAdvancedBody');
    const advancedToggleArrow = document.getElementById('advancedToggleArrow');
    const btnCopySystemPrompt = document.getElementById('btnCopySystemPrompt');
    const btnCopyGenPrompt = document.getElementById('btnCopyGenPrompt');
    const btnCopyCurlSnippet = document.getElementById('btnCopyCurlSnippet');
    const btnCopyAiPrompt = document.getElementById('btnCopyAiPrompt');

    if (btnQuickCopyAgentPrompt) {
        btnQuickCopyAgentPrompt.addEventListener('click', () => {
            const text = document.getElementById('aiSystemPromptText')?.textContent || '';
            navigator.clipboard.writeText(text).then(() => {
                const icon = document.getElementById('quickCopyIcon');
                const label = document.getElementById('quickCopyText');
                const step2Box = document.getElementById('aiStep2Box');
                const step2Tag = document.getElementById('aiStep2Tag');

                if (icon) icon.textContent = '✓';
                if (label) label.textContent = 'Copied to Clipboard!';
                btnQuickCopyAgentPrompt.classList.add('copied');

                // Unlock Step 2 with animation
                if (step2Box) {
                    step2Box.classList.remove('ai-step-locked');
                    step2Box.classList.add('ai-step-unlocked');
                }
                if (step2Tag) {
                    step2Tag.textContent = 'Step 2: Ready to Paste!';
                }

                setTimeout(() => {
                    if (icon) icon.textContent = '📋';
                    if (label) label.textContent = 'Copy Agent Prompt';
                    btnQuickCopyAgentPrompt.classList.remove('copied');
                }, 2500);
            });
        });
    }

    if (btnToggleAiAdvanced && aiAdvancedBody) {
        btnToggleAiAdvanced.addEventListener('click', () => {
            const isHidden = aiAdvancedBody.style.display === 'none' || aiAdvancedBody.style.display === '';
            aiAdvancedBody.style.display = isHidden ? 'block' : 'none';
            btnToggleAiAdvanced.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
            if (advancedToggleArrow) {
                advancedToggleArrow.textContent = isHidden ? '▲' : '▼';
            }
        });
    }

    if (btnCopySystemPrompt) {
        btnCopySystemPrompt.addEventListener('click', () => {
            const text = document.getElementById('aiSystemPromptText')?.textContent || '';
            navigator.clipboard.writeText(text).then(() => {
                btnCopySystemPrompt.textContent = '✓ Copied!';
                btnCopySystemPrompt.classList.add('copied');
                setTimeout(() => {
                    btnCopySystemPrompt.textContent = '📋 Copy Agent Prompt';
                    btnCopySystemPrompt.classList.remove('copied');
                }, 2000);
            });
        });
    }

    if (btnCopyGenPrompt) {
        btnCopyGenPrompt.addEventListener('click', () => {
            const text = document.getElementById('aiGenArtPromptExample')?.textContent || '';
            navigator.clipboard.writeText(text).then(() => {
                btnCopyGenPrompt.textContent = '✓ Copied!';
                btnCopyGenPrompt.classList.add('copied');
                setTimeout(() => {
                    btnCopyGenPrompt.textContent = '📋 Copy Template';
                    btnCopyGenPrompt.classList.remove('copied');
                }, 2000);
            });
        });
    }

    if (btnCopyCurlSnippet) {
        btnCopyCurlSnippet.addEventListener('click', () => {
            const text = document.getElementById('aiCurlSnippet')?.textContent || '';
            navigator.clipboard.writeText(text).then(() => {
                btnCopyCurlSnippet.textContent = '✓ Copied!';
                btnCopyCurlSnippet.classList.add('copied');
                setTimeout(() => {
                    btnCopyCurlSnippet.textContent = '📋 Copy cURL';
                    btnCopyCurlSnippet.classList.remove('copied');
                }, 2000);
            });
        });
    }

    const btnDownloadCapsule = document.getElementById('btnDownloadCapsule');
    const aiStep3Group = document.getElementById('aiStep3Group');

    if (btnDownloadCapsule) {
        btnDownloadCapsule.addEventListener('click', (e) => {
            e.preventDefault();
            downloadCurrentCapsule();
            if (btnCopyAiPrompt) {
                btnCopyAiPrompt.classList.add('step-suggested');
            }
        });
    }

    if (btnCopyAiPrompt) {
        btnCopyAiPrompt.addEventListener('click', () => {
            const text = document.getElementById('aiPromptTextarea')?.textContent || '';
            navigator.clipboard.writeText(text).then(() => {
                const icon = document.getElementById('copyPromptIcon');
                const label = document.getElementById('copyPromptText');
                if (icon) icon.textContent = '✓';
                if (label) label.textContent = '2. Copied!';
                btnCopyAiPrompt.classList.add('copied');
                btnCopyAiPrompt.classList.remove('step-suggested');

                if (aiStep3Group) {
                    aiStep3Group.classList.add('visible');
                    aiStep3Group.classList.add('step-suggested');
                }
                const inlineTargets = document.getElementById('aiChatTargetsInline');
                if (inlineTargets) {
                    inlineTargets.style.display = 'inline-flex';
                }

                setTimeout(() => {
                    if (icon) icon.textContent = '📋';
                    if (label) label.textContent = '2. Copy Prompt';
                    btnCopyAiPrompt.classList.remove('copied');
                }, 2500);
            });
        });
    }

    if (aiStep3Group) {
        aiStep3Group.addEventListener('click', () => {
            aiStep3Group.classList.remove('step-suggested');
        });
    }

    // 1-Click Autofix Download Button
    const btnDownloadAutofix = document.getElementById('btnDownloadAutofix');
    if (btnDownloadAutofix) {
        btnDownloadAutofix.addEventListener('click', (e) => {
            e.preventDefault();
            if (!currentAutofixCanvas) return;
            const filename = `${(currentLoadedGameName || 'steam_capsule').toLowerCase().replace(/[^a-z0-9]/g, '_')}_autofix.jpg`;
            currentAutofixCanvas.toBlob((blob) => {
                if (!blob) return;
                const blobUrl = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = blobUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(blobUrl), 3000);
            }, 'image/jpeg', 0.95);
        });
    }

    // Test in 3x3 Simulator Button
    const btnTestAutofixInSim = document.getElementById('btnTestAutofixInSim');
    if (btnTestAutofixInSim) {
        btnTestAutofixInSim.addEventListener('click', (e) => {
            e.preventDefault();
            if (!currentAutofixCanvas) {
                const heroImg = document.getElementById('resultHeroCapsuleImg') || document.getElementById('cvCanvas');
                if (window.CapsuluAutofix && heroImg) {
                    currentAutofixCanvas = window.CapsuluAutofix.applyCapsuluAutofix(heroImg);
                }
            }
            if (!currentAutofixCanvas) return;

            const userSimImgs = document.querySelectorAll('.user-capsule-item img, [data-is-user="true"] img');
            const testBtnText = document.getElementById('testSimText');
            const testBtnIcon = document.getElementById('testSimIcon');

            if (!isAutofixAppliedToSim) {
                // Apply autofixed image
                const enhancedDataUrl = currentAutofixCanvas.toDataURL('image/jpeg', 0.95);
                userSimImgs.forEach(img => {
                    img.src = enhancedDataUrl;
                });
                isAutofixAppliedToSim = true;
                if (testBtnText) testBtnText.textContent = '✓ Applied! (Click to Revert)';
                if (testBtnIcon) testBtnIcon.textContent = '↩️';
            } else {
                // Revert to original image
                userSimImgs.forEach(img => {
                    if (currentLoadedImgSrc) {
                        img.src = currentLoadedImgSrc;
                    }
                });
                isAutofixAppliedToSim = false;
                if (testBtnText) testBtnText.textContent = 'Test in 3×3 Simulator';
                if (testBtnIcon) testBtnIcon.textContent = '👁️';
            }

            // Scroll to visual check panel
            const visualPanel = document.getElementById('visualCheckPanel');
            if (visualPanel) {
                visualPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    }

    // In-Browser WebGPU Neural Diffusion Runner
    const btnRunWebGpu = document.getElementById('btnRunWebGpuDiffusion');
    const btnCancelWebGpu = document.getElementById('btnCancelWebGpu');
    const webgpuProgressCard = document.getElementById('webgpuProgressCard');
    const webgpuResultCard = document.getElementById('webgpuResultCard');
    const webgpuProgressFill = document.getElementById('webgpuProgressFill');
    const webgpuProgressPct = document.getElementById('webgpuProgressPct');
    const webgpuProgressLabel = document.getElementById('webgpuProgressLabel');
    const webgpuPhaseDesc = document.getElementById('webgpuPhaseDesc');
    const webgpuTelemetryBadge = document.getElementById('webgpuTelemetryBadge');

    if (btnRunWebGpu) {
        btnRunWebGpu.addEventListener('click', async (e) => {
            e.preventDefault();
            if (!window.CapsuluWebGpu) return;

            let sourceImg = (cvCanvas && cvCanvas.width > 0) ? cvCanvas : document.getElementById('resultHeroCapsuleImg');
            if (!sourceImg || (sourceImg.naturalWidth === 0 && sourceImg.width === 0)) {
                if (currentLoadedImgSrc) {
                    sourceImg = new Image();
                    sourceImg.crossOrigin = 'anonymous';
                    await new Promise((res) => {
                        sourceImg.onload = res;
                        sourceImg.onerror = res;
                        sourceImg.src = currentLoadedImgSrc;
                    });
                }
            }
            if (!sourceImg) return;

            if (webgpuResultCard) webgpuResultCard.style.display = 'none';
            if (webgpuProgressCard) webgpuProgressCard.style.display = 'block';
            btnRunWebGpu.disabled = true;

            try {
                const result = await window.CapsuluWebGpu.runInpaintingPipeline(
                    sourceImg,
                    { gameName: currentLoadedGameName, appid: currentLoadedAppId },
                    (prog) => {
                        if (webgpuProgressFill) webgpuProgressFill.style.width = `${prog.pct || 0}%`;
                        if (webgpuProgressPct) webgpuProgressPct.textContent = `${prog.pct || 0}%`;
                        if (webgpuProgressLabel && prog.message) webgpuProgressLabel.textContent = prog.message;
                        if (webgpuPhaseDesc) {
                            if (prog.speedMBs) {
                                webgpuPhaseDesc.textContent = `Bandwidth: ${prog.speedMBs} MB/s | Phase: ${prog.phase}`;
                            } else {
                                webgpuPhaseDesc.textContent = `Phase: ${prog.phase} (${prog.pct}%)`;
                            }
                        }
                    }
                );

                currentWebGpuCanvas = result.canvas;

                const nativeW = sourceImg.naturalWidth || sourceImg.videoWidth || sourceImg.width || 460;
                const nativeH = sourceImg.naturalHeight || sourceImg.videoHeight || sourceImg.height || 215;

                // Render Before Canvas
                const canvasBefore = document.getElementById('webgpuCanvasBefore');
                if (canvasBefore) {
                    canvasBefore.width = nativeW;
                    canvasBefore.height = nativeH;
                    const ctxB = canvasBefore.getContext('2d');
                    ctxB.imageSmoothingEnabled = true;
                    ctxB.imageSmoothingQuality = 'high';
                    ctxB.clearRect(0, 0, nativeW, nativeH);
                    ctxB.drawImage(sourceImg, 0, 0, nativeW, nativeH);
                }

                // Render After Canvas
                const canvasAfter = document.getElementById('webgpuCanvasAfter');
                if (canvasAfter && result.canvas) {
                    canvasAfter.width = nativeW;
                    canvasAfter.height = nativeH;
                    const ctxA = canvasAfter.getContext('2d');
                    ctxA.imageSmoothingEnabled = true;
                    ctxA.imageSmoothingQuality = 'high';
                    ctxA.clearRect(0, 0, nativeW, nativeH);
                    ctxA.drawImage(result.canvas, 0, 0, nativeW, nativeH);
                }

                // Initialize Before / After Slider for WebGPU
                if (window.CapsuluAutofix && window.CapsuluAutofix.initBeforeAfterSlider) {
                    window.CapsuluAutofix.initBeforeAfterSlider('webgpuBeforeAfterSlider');
                }

                if (webgpuTelemetryBadge) {
                    webgpuTelemetryBadge.textContent = `⚡ WebGPU Inpainted in ${(result.durationMs / 1000).toFixed(1)}s (${result.vramUsedMB} MB VRAM)`;
                }

                if (webgpuProgressCard) webgpuProgressCard.style.display = 'none';
                if (webgpuResultCard) {
                    webgpuResultCard.style.display = 'block';
                    webgpuResultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }

                const runText = document.getElementById('runWebGpuText');
                if (runText) runText.textContent = 'Re-Generate with WebGPU';
            } catch (err) {
                console.warn('WebGPU execution error or cancelled:', err);
                if (webgpuProgressCard) webgpuProgressCard.style.display = 'none';
            } finally {
                btnRunWebGpu.disabled = false;
            }
        });
    }

    if (btnCancelWebGpu) {
        btnCancelWebGpu.addEventListener('click', (e) => {
            e.preventDefault();
            if (window.CapsuluWebGpu) {
                window.CapsuluWebGpu.cancelInference();
            }
            if (webgpuProgressCard) webgpuProgressCard.style.display = 'none';
            if (btnRunWebGpu) btnRunWebGpu.disabled = false;
        });
    }

    // WebGPU Generated Art Download Button
    const btnDownloadWebGpuArt = document.getElementById('btnDownloadWebGpuArt');
    if (btnDownloadWebGpuArt) {
        btnDownloadWebGpuArt.addEventListener('click', (e) => {
            e.preventDefault();
            if (!currentWebGpuCanvas) return;
            const filename = `${(currentLoadedGameName || 'steam_capsule').toLowerCase().replace(/[^a-z0-9]/g, '_')}_neural_webgpu.jpg`;
            currentWebGpuCanvas.toBlob((blob) => {
                if (!blob) return;
                const blobUrl = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = blobUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => {
                    document.body.removeChild(a);
                    URL.revokeObjectURL(blobUrl);
                }, 1000);
            }, 'image/jpeg', 0.95);
        });
    }

    // WebGPU Test in 3x3 Simulator Button
    const btnTestWebGpuInSim = document.getElementById('btnTestWebGpuInSim');
    if (btnTestWebGpuInSim) {
        btnTestWebGpuInSim.addEventListener('click', (e) => {
            e.preventDefault();
            if (!currentWebGpuCanvas) return;

            const userSimImgs = document.querySelectorAll('.user-capsule-item img, [data-is-user="true"] img');
            const testBtnText = document.getElementById('testWebGpuSimText');
            const testBtnIcon = document.getElementById('testWebGpuSimIcon');

            if (!isWebGpuAppliedToSim) {
                // Apply WebGPU neural image
                const neuralDataUrl = currentWebGpuCanvas.toDataURL('image/jpeg', 0.95);
                userSimImgs.forEach(img => {
                    img.src = neuralDataUrl;
                });
                isWebGpuAppliedToSim = true;
                if (testBtnText) testBtnText.textContent = '✓ Applied! (Click to Revert)';
                if (testBtnIcon) testBtnIcon.textContent = '↩️';
            } else {
                // Revert to original image
                userSimImgs.forEach(img => {
                    if (currentLoadedImgSrc) {
                        img.src = currentLoadedImgSrc;
                    }
                });
                isWebGpuAppliedToSim = false;
                if (testBtnText) testBtnText.textContent = 'Test in 3×3 Simulator';
                if (testBtnIcon) testBtnIcon.textContent = '👁️';
            }

            // Scroll to visual check panel
            const visualPanel = document.getElementById('visualCheckPanel');
            if (visualPanel) {
                visualPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    }

    browseBtn.addEventListener('click', (e) => {
        e.preventDefault();
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    });

    fetchUrlBtn.addEventListener('click', () => handleUrlInput(true));
    steamUrlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleUrlInput(true);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZoneArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZoneArea.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZoneArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZoneArea.classList.remove('drag-over');
        });
    });

    dropZoneArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFile(files[0]);
        }
    });

    window.addEventListener('paste', (e) => {
        if (document.activeElement === steamUrlInput) return;

        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (let item of items) {
            if (item.type.indexOf('image') === 0) {
                const blob = item.getAsFile();
                handleFile(blob, 'Pasted Capsule Art');
                return;
            }
        }

        const text = (e.clipboardData || window.clipboardData).getData('text');
        if (text && (text.includes('steampowered.com') || text.includes('http') || /^\d+$/.test(text.trim()))) {
            steamUrlInput.value = text.trim();
            handleUrlInput(true);
        }
    });
}

/**
 * Default Seed Samples (Guaranteed 10+ games)
 */
function getDefaultSamples() {
    return [
        {
            name: "DICEPTION",
            appid: 4429000,
            url: "https://store.steampowered.com/app/4429000/DICEPTION/",
            imageUrl: "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4429000/56bd8aa0cf2d865acbae5501824e33c4dd8c2269/header.jpg?t=1785770104",
            price: "4,99€",
            tags: ["Indie", "Strategy"]
        },
        {
            name: "Melodan",
            appid: 4987230,
            url: "https://store.steampowered.com/app/4987230/Melodan/",
            imageUrl: "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4987230/833a1d7f3a40629d6c8edd334ad871425ccd644b/header.jpg?t=1786736037",
            price: "Coming Soon (Q1 2027)",
            tags: ["Action", "Indie", "Strategy"]
        },
        {
            name: "ELDEN RING",
            appid: 1245620,
            url: "https://store.steampowered.com/app/1245620/",
            imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg",
            price: "$59.99",
            tags: ["Souls-like", "RPG", "Dark Fantasy"]
        },
        {
            name: "Hades",
            appid: 1145360,
            url: "https://store.steampowered.com/app/1145360/",
            imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg",
            price: "$24.99",
            tags: ["Action Roguelike", "Indie", "Mythology"]
        },
        {
            name: "Balatro",
            appid: 2379780,
            url: "https://store.steampowered.com/app/2379780/",
            imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/2379780/header.jpg",
            price: "$14.99",
            tags: ["Roguelike Deckbuilder", "Indie"]
        },
        {
            name: "Cyberpunk 2077",
            appid: 1091500,
            url: "https://store.steampowered.com/app/1091500/",
            imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1091500/header.jpg",
            price: "$59.99",
            tags: ["Cyberpunk", "Open World", "RPG"]
        },
        {
            name: "Stardew Valley",
            appid: 413150,
            url: "https://store.steampowered.com/app/413150/",
            imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg",
            price: "$14.99",
            tags: ["Farming Sim", "Pixel Graphics", "Co-op"]
        },
        {
            name: "Hollow Knight",
            appid: 367520,
            url: "https://store.steampowered.com/app/367520/",
            imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/367520/header.jpg",
            price: "$14.99",
            tags: ["Metroidvania", "Souls-like", "2D"]
        },
        {
            name: "Baldur's Gate 3",
            appid: 1086940,
            url: "https://store.steampowered.com/app/1086940/",
            imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1086940/header.jpg",
            price: "$59.99",
            tags: ["CRPG", "Choices Matter", "Fantasy"]
        },
        {
            name: "Terraria",
            appid: 105600,
            url: "https://store.steampowered.com/app/105600/",
            imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/105600/header.jpg",
            price: "$9.99",
            tags: ["Sandbox", "Survival", "2D"]
        }
    ];
}

const PINNED_SAMPLES = [
    {
        name: "DICEPTION",
        appid: 4429000,
        url: "https://store.steampowered.com/app/4429000/DICEPTION/",
        imageUrl: "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4429000/56bd8aa0cf2d865acbae5501824e33c4dd8c2269/header.jpg?t=1785770104",
        price: "4,99€",
        tags: ["Indie", "Strategy"]
    },
    {
        name: "Melodan",
        appid: 4987230,
        url: "https://store.steampowered.com/app/4987230/Melodan/",
        imageUrl: "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/4987230/833a1d7f3a40629d6c8edd334ad871425ccd644b/header.jpg?t=1786736037",
        price: "Coming Soon (Q1 2027)",
        tags: ["Action", "Indie", "Strategy"]
    }
];

function ensurePinnedInList(items) {
    if (!Array.isArray(items)) items = [];

    for (const pinned of PINNED_SAMPLES) {
        const exists = items.some(x =>
            (x.appid && String(x.appid) === String(pinned.appid)) ||
            (x.name && x.name.toLowerCase() === pinned.name.toLowerCase())
        );
        if (!exists) {
            items.push(pinned);
        }
    }
    return items;
}

/**
 * Initialize / Render Merged Recent List (Guarantees DICEPTION and Melodan are always present)
 */
function initRecentList(forceReset = false) {
    let items = [];
    if (!forceReset) {
        try {
            items = JSON.parse(localStorage.getItem(RECENT_STORAGE_KEY) || '[]');
        } catch (e) {
            items = [];
        }
    }

    if (Array.isArray(items)) {
        // Clean out any legacy upload items
        items = items.filter(it => it && !it.isUpload && (it.appid || it.url));
    }

    if (!items || items.length < 9) {
        items = getDefaultSamples();
    }

    items = ensurePinnedInList(items);
    localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(items));
    renderRecentList(items);
}

function saveRecentItem(newItem) {
    if (!newItem || newItem.isUpload || (!newItem.appid && !newItem.url)) {
        return;
    }
    try {
        let items = JSON.parse(localStorage.getItem(RECENT_STORAGE_KEY) || '[]');
        if (!items || items.length === 0) items = getDefaultSamples();

        // Filter out uploads and clean items
        items = items.filter(it => it && !it.isUpload && (it.appid || it.url));

        // 1. Remove duplicate if already present
        items = items.filter(existing => {
            if (newItem.name && existing.name && existing.name.toLowerCase() === newItem.name.toLowerCase()) return false;
            if (newItem.appid && existing.appid && String(existing.appid) === String(newItem.appid)) return false;
            if (newItem.url && existing.url && existing.url === newItem.url) return false;
            return true;
        });

        // 2. Add newly tested item to front
        items.unshift(newItem);

        // 3. Separate non-pinned and pinned items so DICEPTION and Melodan NEVER get evicted
        const nonPinned = items.filter(item => {
            const isDiception = item.appid == 4429000 || (item.name && item.name.toLowerCase() === 'diception');
            const isMelodan = item.appid == 4987230 || (item.name && item.name.toLowerCase() === 'melodan');
            return !isDiception && !isMelodan;
        });

        // Keep up to 10 dynamic recent items
        const trimmedNonPinned = nonPinned.slice(0, 10);

        // 4. Assemble merged list preserving pinned games
        let merged = [newItem, ...trimmedNonPinned];
        merged = ensurePinnedInList(merged);

        // 5. Deduplicate preserving order
        const seen = new Set();
        const finalItems = merged.filter(it => {
            const key = it.appid ? String(it.appid) : (it.name || '').toLowerCase();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });

        localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(finalItems));
        renderRecentList(finalItems);
    } catch (e) {
        console.warn('Error updating recent items:', e);
    }
}

function renderRecentList(items) {
    recentListContainer.innerHTML = '';

    items.forEach((item, index) => {
        const link = document.createElement('a');
        link.className = 'sample-link';
        link.textContent = item.name;
        link.title = item.url ? `Analyze ${item.name} (${item.url})` : `Analyze ${item.name}`;

        link.addEventListener('click', (e) => {
            e.preventDefault();
            if (item.url) {
                steamUrlInput.value = item.url;
                handleUrlInput(true);
            } else if (item.imageUrl) {
                steamUrlInput.value = item.imageUrl;
                handleUrlInput(true);
            } else {
                alert(`"${item.name}" was an uploaded local file. Please click "Upload Image" to test again.`);
            }
        });

        recentListContainer.appendChild(link);

        if (index < items.length - 1) {
            const sep = document.createElement('span');
            sep.className = 'sample-separator';
            sep.textContent = ', ';
            recentListContainer.appendChild(sep);
        }
    });
}

/**
 * URL Parser & Steam Details Fetcher with Deep Link Support
 */
async function handleUrlInput(updateUrlBar = true) {
    const rawInput = steamUrlInput.value.trim();
    if (!rawInput) {
        alert('Please enter a Steam Store URL, an App ID, or an image URL.');
        return;
    }

    if (updateUrlBar) {
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('app', rawInput);
        window.history.pushState({ app: rawInput }, '', newUrl);
    }

    // 1. Direct Image URL
    if (
        rawInput.includes('.jpg') ||
        rawInput.includes('.png') ||
        rawInput.includes('.webp') ||
        rawInput.includes('store_item_assets')
    ) {
        const gameTitle = rawInput.split('/').pop().split('?')[0] || "Custom Image";
        saveRecentItem({
            name: gameTitle,
            url: rawInput,
            imageUrl: rawInput
        });
        loadImageWithFallbacks([rawInput, `https://images.weserv.nl/?url=${encodeURIComponent(rawInput)}`], gameTitle, null, null, null, rawInput);
        return;
    }

    // 2. Steam Store URL: store.steampowered.com/app/{appid}/...
    const storeMatch = rawInput.match(/store\.steampowered\.com\/app\/(\d+)(?:\/([^\/?#]+))?/i);
    let appid = null;
    let gameTitle = 'Steam Game';
    let storeUrl = null;

    if (storeMatch) {
        appid = storeMatch[1];
        const slug = storeMatch[2];
        gameTitle = slug ? decodeURIComponent(slug.replace(/_/g, ' ')) : `App ID ${appid}`;
        storeUrl = `https://store.steampowered.com/app/${appid}/`;
    } else if (/^\d+$/.test(rawInput)) {
        appid = rawInput;
        gameTitle = `App ID ${appid}`;
        storeUrl = `https://store.steampowered.com/app/${appid}/`;
    }

    if (appid) {
        showLoading(true);

        let detailsData = null;
        const endpointCandidates = [
            `api.php?appid=${appid}`,
            `/api/steam-details?appid=${appid}`,
            `https://corsproxy.io/?url=${encodeURIComponent('https://store.steampowered.com/api/appdetails?appids=' + appid)}`,
            `https://api.allorigins.win/raw?url=${encodeURIComponent('https://store.steampowered.com/api/appdetails?appids=' + appid)}`
        ];

        for (const ep of endpointCandidates) {
            try {
                const apiRes = await fetch(ep);
                if (apiRes.ok) {
                    const raw = await apiRes.json();
                    if (raw && raw.success && raw.header_image) {
                        detailsData = raw;
                        break;
                    } else if (raw && raw[appid] && raw[appid].data) {
                        const d = raw[appid].data;
                        const isComingSoon = d.release_date && d.release_date.coming_soon;
                        let priceStr = "Free";
                        if (d.is_free) priceStr = "Free to Play";
                        else if (d.price_overview) priceStr = d.price_overview.final_formatted || "Free";
                        else if (isComingSoon) priceStr = "Coming Soon";

                        detailsData = {
                            success: true,
                            appid: Number(appid),
                            name: d.name,
                            header_image: d.header_image,
                            price: priceStr,
                            is_coming_soon: isComingSoon,
                            release_date: d.release_date ? d.release_date.date : "",
                            genres: (d.genres || []).map(g => g.description)
                        };
                        break;
                    }
                }
            } catch (err) {
                // Continue to next endpoint candidate
            }
        }

        if (detailsData && detailsData.header_image) {
            const finalName = detailsData.name || gameTitle;
            let displayPrice = detailsData.price;
            if (detailsData.is_coming_soon && detailsData.release_date) {
                displayPrice = `Coming Soon (${detailsData.release_date})`;
            }

            const activeTags = (detailsData.tags && detailsData.tags.length > 0) ? detailsData.tags : (detailsData.genres || []);

            saveRecentItem({
                name: finalName,
                appid: appid,
                url: storeUrl,
                imageUrl: detailsData.header_image,
                price: displayPrice,
                tags: activeTags
            });

            const reviewsCount = (detailsData.total_reviews !== undefined && detailsData.total_reviews !== null) ? detailsData.total_reviews : ((detailsData.reviews !== undefined && detailsData.reviews !== null) ? detailsData.reviews : null);

            loadImageWithFallbacks(
                [
                    `https://images.weserv.nl/?url=${encodeURIComponent(detailsData.header_image)}`,
                    `https://wsrv.nl/?url=${encodeURIComponent(detailsData.header_image)}`,
                    detailsData.header_image
                ],
                finalName,
                displayPrice,
                activeTags,
                appid,
                storeUrl,
                detailsData.genres || [],
                reviewsCount
            );
            return;
        }

        // Fallback candidate URLs in priority order
        const candidates = [
            `https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/${appid}/header.jpg`,
            `https://cdn.akamai.steamstatic.com/steam/apps/${appid}/header.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/header.jpg`,
            `https://steamcdn-a.akamaihd.net/steam/apps/${appid}/header.jpg`,
            `https://images.weserv.nl/?url=https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/${appid}/header.jpg`
        ];

        saveRecentItem({
            name: gameTitle,
            appid: appid,
            url: storeUrl
        });

        loadImageWithFallbacks(candidates, gameTitle, null, null, appid, storeUrl, []);
        return;
    }

    // 3. Fallback for other HTTP URLs
    if (rawInput.startsWith('http://') || rawInput.startsWith('https://')) {
        const gameTitle = "Web Image";
        saveRecentItem({
            name: gameTitle,
            url: rawInput,
            imageUrl: rawInput
        });
        loadImageWithFallbacks([rawInput, `https://images.weserv.nl/?url=${encodeURIComponent(rawInput)}`], gameTitle, null, null, null, rawInput, []);
    } else {
        alert('Unrecognized format. Please paste a full Steam store URL (e.g. store.steampowered.com/app/4429000), an App ID, or an image URL.');
    }
}

/**
 * Sequential Candidate Loader
 */
function loadImageWithFallbacks(urls, gameTitle, price, tags, appid, storeUrl, genres = [], reviews = null) {
    showLoading(true);
    let currentIndex = 0;

    function tryNext() {
        if (currentIndex >= urls.length) {
            showLoading(false);
            const appMsg = appid ? ` (App ID ${appid})` : '';
            alert(
                `Could not automatically load the capsule image from Steam CDN${appMsg}.\n\n` +
                `💡 Tip: For newly released games with hashed assets, right-click the capsule image on your Steam store page, select "Copy Image Address", and paste the direct image link here, or click "Upload Image" to select your file directly!`
            );
            return;
        }

        const currentUrl = urls[currentIndex];
        currentIndex++;

        const img = new Image();
        img.crossOrigin = "anonymous";

        img.onload = () => {
            runVisualAiAnalysisFlow(img, currentUrl, (cv, scores) => {
                analyzeAndDisplay(img, currentUrl, gameTitle, price, tags, appid, storeUrl, genres, reviews, cv, scores);
            });
        };

        img.onerror = () => {
            tryNext();
        };

        img.src = currentUrl;
    }

    tryNext();
}

/**
 * File Upload Handler
 */
function handleFile(file, customName) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload a valid image file (PNG, JPG, WebP).');
        return;
    }

    const cleanUrl = new URL(window.location);
    cleanUrl.searchParams.delete('app');
    cleanUrl.searchParams.delete('url');
    cleanUrl.searchParams.delete('appid');
    window.history.pushState({}, '', cleanUrl.pathname);

    const reader = new FileReader();
    const gameName = customName || file.name.replace(/\.[^/.]+$/, "");

    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            runVisualAiAnalysisFlow(img, e.target.result, (cv, scores) => {
                analyzeAndDisplay(img, e.target.result, gameName, null, ["Custom Artwork"], null, null, [], null, cv, scores);
            });
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

let aiScanAnimInterval = null;
let currentAnalysisSessionId = 0;

function showLoading(show, message = null, previewSrc = null) {
    if (show) {
        loadingBar.style.display = 'block';
        resultsDashboard.style.display = 'none';

        // Immediately reset computational bars and states to 0%
        const cardCv = document.getElementById('engineCardCv');
        const barCv = document.getElementById('engineBarCv');
        const statusCv = document.getElementById('engineStatusCv');

        const cardNn = document.getElementById('engineCardNn');
        const barNn = document.getElementById('engineBarNn');
        const statusNn = document.getElementById('engineStatusNn');

        if (cardCv) cardCv.className = 'loading-engine-section';
        if (barCv) {
            barCv.style.transition = 'none';
            barCv.style.width = '0%';
            void barCv.offsetWidth;
            barCv.style.transition = '';
        }
        if (statusCv) statusCv.textContent = previewSrc ? 'Evaluating...' : 'Standby...';

        if (cardNn) cardNn.className = 'loading-engine-section loading-cnn-section';
        if (barNn) {
            barNn.style.transition = 'none';
            barNn.style.width = '0%';
            void barNn.offsetWidth;
            barNn.style.transition = '';
        }
        if (statusNn) statusNn.textContent = previewSrc ? 'Inferencing...' : 'Standby...';

        const previewImg = document.getElementById('aiScanPreviewImg');
        const kernelBox = document.getElementById('aiKernelBox');
        const laser = document.getElementById('aiScanLaser');
        const placeholder = document.getElementById('aiScanPlaceholder');

        if (previewSrc) {
            if (previewImg) {
                previewImg.src = previewSrc;
                previewImg.style.display = 'block';
            }
            if (kernelBox) kernelBox.style.display = 'block';
            if (laser) laser.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';
            startFeatureCanvasAnimation();
        } else {
            if (previewImg) previewImg.style.display = 'none';
            if (kernelBox) kernelBox.style.display = 'none';
            if (laser) laser.style.display = 'none';
            if (placeholder) {
                placeholder.style.display = 'flex';
                const span = placeholder.querySelector('span');
                if (span) span.textContent = message || "Fetching Steam Store details & capsule asset...";
            }
        }

        const textElem = document.getElementById('loadingDynamicText');
        if (textElem) textElem.textContent = message || "Executing parallel neural inference and pixel metrics...";
    } else {
        stopFeatureCanvasAnimation();
        loadingBar.style.display = 'none';
        resultsDashboard.style.display = 'block';
    }
}

function startFeatureCanvasAnimation() {
    const canvas = document.getElementById('aiScanFeatureCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    stopFeatureCanvasAnimation();

    const nodes = [];
    for (let i = 0; i < 20; i++) {
        nodes.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 1.4,
            vy: (Math.random() - 0.5) * 1.4,
            radius: Math.random() * 2.2 + 1.2
        });
    }

    aiScanAnimInterval = setInterval(() => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw connection lines
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.18)';
        ctx.lineWidth = 1;
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const dist = Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y);
                if (dist < 75) {
                    ctx.beginPath();
                    ctx.moveTo(nodes[i].x, nodes[i].y);
                    ctx.lineTo(nodes[j].x, nodes[j].y);
                    ctx.stroke();
                }
            }
        }

        // Draw glowing nodes
        for (const n of nodes) {
            ctx.fillStyle = '#00f2fe';
            ctx.shadowColor = '#00f2fe';
            ctx.shadowBlur = 8;
            ctx.beginPath();
            ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
            ctx.fill();

            n.x += n.vx;
            n.y += n.vy;
            if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
            if (n.y < 0 || n.y > canvas.height) n.y *= -1;
        }
        ctx.shadowBlur = 0;
    }, 40);
}

function stopFeatureCanvasAnimation() {
    if (aiScanAnimInterval) {
        clearInterval(aiScanAnimInterval);
        aiScanAnimInterval = null;
    }
}

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * True Dual-Engine Parallel AI Flow (Minimum ~2.2s Total Visual Experience):
 * Parallel Track A: Computer Vision Deterministic Engine (1.8s)
 * Parallel Track B: PyTorch Deep Learning CNN Model (2.2s)
 */
async function runVisualAiAnalysisFlow(img, imgSrc, onComplete) {
    const sessionId = ++currentAnalysisSessionId;
    showLoading(true, "Executing Parallel Neural & Vision Engines...", imgSrc);

    const cardCv = document.getElementById('engineCardCv');
    const barCv = document.getElementById('engineBarCv');
    const statusCv = document.getElementById('engineStatusCv');

    const cardNn = document.getElementById('engineCardNn');
    const barNn = document.getElementById('engineBarNn');
    const statusNn = document.getElementById('engineStatusNn');

    // Reset Engine Visual States & Start Fill
    if (cardCv) cardCv.className = 'loading-engine-section engine-active';
    if (barCv) barCv.style.width = '15%';
    if (statusCv) statusCv.textContent = 'Evaluating...';

    if (cardNn) cardNn.className = 'loading-engine-section loading-cnn-section engine-active';
    if (barNn) barNn.style.width = '10%';
    if (statusNn) statusNn.textContent = 'Inferencing...';

    // === PARALLEL TRACK A: Computer Vision Heuristics Engine (1.7s) ===
    const cvPromise = (async () => {
        setTimeout(() => { if (sessionId === currentAnalysisSessionId && barCv) barCv.style.width = '55%'; }, 500);
        setTimeout(() => { if (sessionId === currentAnalysisSessionId && barCv) barCv.style.width = '85%'; }, 1200);

        const cv = runComputerVision(img);
        const scores = evaluateScores(cv);

        await delay(1700);
        if (sessionId !== currentAnalysisSessionId) return null;

        if (barCv) barCv.style.width = '100%';
        if (statusCv) statusCv.textContent = '✓ 6 Metrics Done';
        if (cardCv) cardCv.className = 'loading-engine-section engine-done';

        return { cv, scores };
    })();

    // === PARALLEL TRACK B: PyTorch Deep Learning CNN Model (MobileNetV3) (2.2s) ===
    const nnPromise = (async () => {
        setTimeout(() => { if (sessionId === currentAnalysisSessionId && barNn) barNn.style.width = '40%'; }, 650);
        setTimeout(() => { if (sessionId === currentAnalysisSessionId && barNn) barNn.style.width = '75%'; }, 1500);

        const cvData = await cvPromise;
        if (!cvData || sessionId !== currentAnalysisSessionId) return false;
        await updateCommercialForecast(cvData.scores, cvData.cv, null, null, img);

        await delay(450);
        if (sessionId !== currentAnalysisSessionId) return false;

        if (barNn) barNn.style.width = '100%';
        if (statusNn) statusNn.textContent = '✓ Milestones Evaluated';
        if (cardNn) cardNn.className = 'loading-engine-section loading-cnn-section engine-done';

        return true;
    })();

    // Await both parallel engines
    const [cvResult] = await Promise.all([cvPromise, nnPromise]);
    if (sessionId !== currentAnalysisSessionId || !cvResult) return;

    await delay(200);

    // Complete & Reveal Dashboard
    if (typeof onComplete === 'function') {
        onComplete(cvResult.cv, cvResult.scores);
    }
    showLoading(false);
}

/**
 * Genre & Subcategory Detection Helper
 */
function detectGenreFromTags(tags) {
    if (!tags || tags.length === 0) return null;
    const tagStr = tags.join(" ").toLowerCase();

    // 1. High-Specificity Subcategories & Subgenres
    if (tagStr.includes("auto battler") || tagStr.includes("autobattler") || tagStr.includes("auto chess")) {
        return "Auto Battler";
    }
    if (tagStr.includes("deckbuilder") || tagStr.includes("card battler") || tagStr.includes("card game")) {
        return "Roguelike Deckbuilder";
    }
    if (tagStr.includes("action roguelike") || tagStr.includes("survivor") || tagStr.includes("bullet hell") || tagStr.includes("roguelite")) {
        return "Action Roguelike";
    }
    if (tagStr.includes("metroidvania") || tagStr.includes("precision platformer")) {
        return "Metroidvania";
    }
    if (tagStr.includes("souls-like") || tagStr.includes("soulslike") || tagStr.includes("dark fantasy")) {
        return "Souls-like";
    }
    if (tagStr.includes("survival horror") || tagStr.includes("psychological horror") || tagStr.includes("horror")) {
        return "Survival Horror";
    }
    if (tagStr.includes("cozy") || tagStr.includes("farming sim") || tagStr.includes("life sim")) {
        return "Cozy Sim";
    }
    if (tagStr.includes("turn-based tactics") || tagStr.includes("tactics") || tagStr.includes("tactical")) {
        return "Turn-Based Tactics";
    }
    if (tagStr.includes("city builder") || tagStr.includes("colony sim") || tagStr.includes("base building")) {
        return "City Builder";
    }
    if (tagStr.includes("boomer shooter") || tagStr.includes("retro fps") || tagStr.includes("arena shooter")) {
        return "Retro FPS";
    }

    // 2. Broad Top-Level Genres
    if (tagStr.includes("action") || tagStr.includes("shooter") || tagStr.includes("hack and slash") || tagStr.includes("fps") || tagStr.includes("fighting")) {
        return "Action";
    }
    if (tagStr.includes("rpg") || tagStr.includes("role-playing")) {
        return "RPG";
    }
    if (tagStr.includes("strategy") || tagStr.includes("rts") || tagStr.includes("turn-based") || tagStr.includes("grand strategy")) {
        return "Strategy";
    }
    if (tagStr.includes("adventure") || tagStr.includes("exploration") || tagStr.includes("narrative")) {
        return "Adventure";
    }
    if (tagStr.includes("simulation") || tagStr.includes("management") || tagStr.includes("sandbox")) {
        return "Simulation";
    }
    if (tagStr.includes("casual") || tagStr.includes("puzzle") || tagStr.includes("party")) {
        return "Casual";
    }
    if (tagStr.includes("indie")) {
        return "Indie";
    }
    return null;
}

function getGenreIcon(tag) {
    const genreIcons = {
        "Auto Battler": "⚔️",
        "Roguelike Deckbuilder": "🃏",
        "Action Roguelike": "🔥",
        "Metroidvania": "🦇",
        "Souls-like": "💀",
        "Survival Horror": "🩸",
        "Cozy Sim": "🌾",
        "Turn-Based Tactics": "♟️",
        "City Builder": "🏗️",
        "Retro FPS": "💥",
        "Action": "⚔️",
        "RPG": "🛡️",
        "Strategy": "♟️",
        "Adventure": "🗺️",
        "Simulation": "🚜",
        "Casual": "☕",
        "Indie": "✨"
    };
    return genreIcons[tag] || "🏷️";
}

/**
 * Dynamically Populate Synchronized Dropdowns with this Game's Exact Genres & Tags
 */
function populateGenreDropdowns(gameGenres = [], gameTags = []) {
    let optionsHtml = `<option value="all">All Steam Games</option>`;

    // 1 to n genres this game has
    const validGenres = Array.isArray(gameGenres) ? gameGenres.filter(Boolean) : [];
    if (validGenres.length > 0) {
        optionsHtml += `<optgroup label="Genre">`;
        validGenres.forEach(g => {
            optionsHtml += `<option value="${g}">${g}</option>`;
        });
        optionsHtml += `</optgroup>`;
    }

    // 1 to m tags this game has (excluding any duplicate of genre)
    const validTags = Array.isArray(gameTags) ? gameTags.filter(t => t && !validGenres.includes(t)) : [];
    if (validTags.length > 0) {
        optionsHtml += `<optgroup label="Tags">`;
        validTags.forEach(t => {
            optionsHtml += `<option value="${t}">${t}</option>`;
        });
        optionsHtml += `</optgroup>`;
    }

    document.querySelectorAll('.genre-sync-dropdown').forEach(dropdown => {
        dropdown.innerHTML = optionsHtml;
        dropdown.value = currentGenreLens === 'all' ? 'all' : currentGenreLens;
    });
}

/**
 * Helper to retrieve empirical benchmark profile for any genre or tag
 */
function getCategoryBenchmark(categoryKey) {
    if (!categoryKey || categoryKey === 'all') return null;
    if (typeof benchmarksData === 'undefined') return null;

    if (benchmarksData.tags && benchmarksData.tags[categoryKey]) {
        return { ...benchmarksData.tags[categoryKey], categoryType: "Tag" };
    }
    if (benchmarksData.genres && benchmarksData.genres[categoryKey]) {
        return { ...benchmarksData.genres[categoryKey], categoryType: "Genre" };
    }

    const allTags = benchmarksData.tags || {};
    const exactTag = Object.keys(allTags).find(k => k.toLowerCase() === categoryKey.toLowerCase());
    if (exactTag) return { ...allTags[exactTag], categoryType: "Tag" };

    const allGen = benchmarksData.genres || {};
    const exactGen = Object.keys(allGen).find(k => k.toLowerCase() === categoryKey.toLowerCase());
    if (exactGen) return { ...allGen[exactGen], categoryType: "Genre" };

    const partial = Object.keys(allTags).find(k => categoryKey.toLowerCase().includes(k.toLowerCase()) || k.toLowerCase().includes(categoryKey.toLowerCase()));
    if (partial) return { ...allTags[partial], categoryType: "Tag" };

    return {
        name: categoryKey,
        count: (benchmarksData.overall && benchmarksData.overall.total_games_analyzed) || 28754,
        tip: `Ensure high contrast and distinct hero readability for "${categoryKey}" audiences.`,
        contrast: { median: 58.4, mean: 59.2 },
        brightness: { median: 86.4, mean: 92.1 },
        saturation: { median: 104.2, mean: 108.5 },
        entropy: { median: 6.72, mean: 6.65 },
        edge_density: { median: 13.1, mean: 14.2 },
        warm_palette_pct: 42.8,
        categoryType: "Tag"
    };
}

/**
 * Switch Active Benchmark Comparison Lens (All Steam Games vs Specific Genre / Tag)
 */
function switchGenreLens(genreKey) {
    currentGenreLens = genreKey || 'all';

    // Update all dropdowns across panels
    document.querySelectorAll('.genre-sync-dropdown').forEach(dropdown => {
        dropdown.value = currentGenreLens === 'all' ? 'all' : currentGenreLens;
    });

    if (typeof currentCvResult !== 'undefined' && currentCvResult) {
        updateGenreBenchmarkDisplay(currentCvResult, currentGenreLens);
        renderSimulatorLineups(currentLoadedImgSrc, currentLoadedGameName, currentLoadedAppId, currentGenreLens);
        generateChecklist(currentCvResult, currentScores, currentGenreLens);
        updateAiPromptCard(currentCvResult, currentScores, currentLoadedGameName, currentLoadedAppId, currentLoadedImgSrc, currentGenreLens);
    }
}

/**
 * Render Ultra-Compact SVG Market Benchmark Radar / Spider Chart
 * Compares: This Capsule vs. Mega-Hit Benchmark vs. Selected Genre/Tag Median
 */
function drawBenchmarkRadar(cv, genreKey) {
    const svg = document.getElementById('benchmarkRadarSvg');
    if (!svg) return;

    const width = 380;
    const height = 320;
    const cx = 190;
    const cy = 155;
    const radius = 100;

    const axes = [
        { label: "⚡ Contrast", key: "contrast" },
        { label: "🎨 Warm Pop", key: "warmth" },
        { label: "🔍 Tonal Depth", key: "entropy" },
        { label: "📐 Sharpness", key: "edge" },
        { label: "💡 Spotlight", key: "focus" },
        { label: "🔤 Title AA", key: "text" }
    ];
    const totalAxes = axes.length;

    function getAngle(i) {
        return -Math.PI / 2 + (i * 2 * Math.PI / totalAxes);
    }

    function getPoint(score, i, rMax = radius) {
        const r = (Math.max(10, Math.min(100, score)) / 100) * rMax;
        const angle = getAngle(i);
        return {
            x: cx + r * Math.cos(angle),
            y: cy + r * Math.sin(angle)
        };
    }

    function pointsToString(pts) {
        return pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    }

    // 1. Compute Normalized Scores for Mega-Hit (Green Polygon)
    // Mega-Hit Baselines: Contrast 63.0 (74%), Warmth 50% (72%), Entropy 6.99 (88%), Edge 14.2% (70%), Spotlight (78%), Title 5.2:1 (70%)
    const megaHitScores = [74, 72, 88, 70, 78, 70];
    const megaHitPoints = megaHitScores.map((s, i) => getPoint(s, i));

    // 2. Compute Normalized Scores for Genre Median (Yellow Polygon)
    let genreScores = null;
    let genreName = null;
    if (genreKey && genreKey !== 'all') {
        const gData = getCategoryBenchmark(genreKey);
        if (gData) {
            genreName = gData.name || genreKey;
            const cScore = Math.min(100, Math.max(15, (gData.contrast.median / 85) * 100));
            const wScore = Math.min(100, Math.max(15, (gData.warm_palette_pct / 70) * 100));
            const eScore = Math.min(100, Math.max(15, ((gData.entropy.median - 4.0) / 3.4) * 100));
            const dScore = Math.min(100, Math.max(15, (gData.edge_density.median / 20) * 100));
            const fScore = 65;
            const tVal = (gData.text && gData.text.contrast && gData.text.contrast.median) || 3.8;
            const tScore = Math.min(100, Math.max(15, (tVal / 7.5) * 100));
            genreScores = [cScore, wScore, eScore, dScore, fScore, tScore];
        }
    }

    // 3. Compute Normalized Scores for This Capsule (Blue Polygon)
    let userScores = [50, 50, 50, 50, 50, 50];
    if (cv) {
        const cScore = Math.min(100, Math.max(15, (cv.brightnessStd / 85) * 100));
        const wScore = Math.min(100, Math.max(15, (cv.warmPct / 70) * 100));
        const eScore = Math.min(100, Math.max(15, ((cv.entropy - 4.0) / 3.4) * 100));
        const dScore = Math.min(100, Math.max(15, (cv.edgeDensity / 20) * 100));
        const fScore = cv.isCenterFocused ? 88 : 45;
        const tScore = Math.min(100, Math.max(15, (cv.titleContrast / 7.5) * 100));
        userScores = [cScore, wScore, eScore, dScore, fScore, tScore];
    }
    const userPoints = userScores.map((s, i) => getPoint(s, i));

    // Update Legends
    const genreLegendItem = document.getElementById('radarGenreLegendItem');
    const genreLegendLabel = document.getElementById('radarGenreLabel');
    if (genreScores && genreName) {
        if (genreLegendItem) genreLegendItem.style.display = 'inline-flex';
        if (genreLegendLabel) genreLegendLabel.textContent = `${genreName} Median`;
    } else {
        if (genreLegendItem) genreLegendItem.style.display = 'none';
    }

    // Build SVG Inner Elements
    let svgContent = '';

    // Concentric Web Grid Polygons (25%, 50%, 75%, 100%)
    const levels = [0.25, 0.50, 0.75, 1.0];
    levels.forEach((lvl, idx) => {
        const isOuter = idx === levels.length - 1;
        const pts = axes.map((_, i) => {
            const angle = getAngle(i);
            const r = lvl * radius;
            return `${(cx + r * Math.cos(angle)).toFixed(1)},${(cy + r * Math.sin(angle)).toFixed(1)}`;
        }).join(' ');
        svgContent += `<polygon points="${pts}" class="radar-grid-polygon ${isOuter ? 'outer' : ''}"></polygon>`;
    });

    // Radiating Axes Lines & Outer Labels
    axes.forEach((axis, i) => {
        const angle = getAngle(i);
        const xOuter = cx + radius * Math.cos(angle);
        const yOuter = cy + radius * Math.sin(angle);
        svgContent += `<line x1="${cx}" y1="${cy}" x2="${xOuter.toFixed(1)}" y2="${yOuter.toFixed(1)}" class="radar-axis-line"></line>`;

        // Axis Label Position
        const labelDist = radius + 22;
        const xLabel = cx + labelDist * Math.cos(angle);
        const yLabel = cy + labelDist * Math.sin(angle);

        let textAnchor = "middle";
        if (Math.abs(Math.cos(angle)) > 0.3) {
            textAnchor = Math.cos(angle) > 0 ? "start" : "end";
        }

        svgContent += `<text x="${xLabel.toFixed(1)}" y="${yLabel.toFixed(1)}" class="radar-axis-label" text-anchor="${textAnchor}">${axis.label}</text>`;
    });

    // 1. Mega-Hit Benchmark Polygon (Green Dashed)
    svgContent += `<polygon points="${pointsToString(megaHitPoints)}" class="radar-poly-megahit" title="Mega-Hit Avg Benchmark (Top 10%)"></polygon>`;

    // 2. Genre Polygon (Yellow)
    if (genreScores) {
        const genrePoints = genreScores.map((s, i) => getPoint(s, i));
        svgContent += `<polygon points="${pointsToString(genrePoints)}" class="radar-poly-genre" title="${genreName} Category Median"></polygon>`;
    }

    // 3. User Capsule Polygon (Cyan Glowing)
    svgContent += `<polygon points="${pointsToString(userPoints)}" class="radar-poly-user" title="This Capsule"></polygon>`;

    // User Vertex Dots with Glow
    userPoints.forEach((p, idx) => {
        svgContent += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" class="radar-vertex-circle" data-axis="${axes[idx].label}"><title>${axes[idx].label}: ${userScores[idx].toFixed(0)}/100</title></circle>`;
    });

    svg.innerHTML = svgContent;
}

/**
 * Update Dedicated Genre/Tag Benchmark Intelligence & Radar Panel
 */
function updateGenreBenchmarkDisplay(cv, genreKey) {
    const card = document.getElementById('genreBenchmarkCard');
    if (!card) return;

    const iconElem = document.getElementById('genreCardIcon');
    const titleElem = document.getElementById('genreCardTitle');

    // 1. Draw SVG Radar Chart
    drawBenchmarkRadar(cv, genreKey);

    // 2. Update Header (Single Icon & Clean Title)
    if (!genreKey || genreKey === 'all') {
        if (iconElem) iconElem.textContent = "🌐";
        if (titleElem) titleElem.textContent = "Market Benchmark Radar";
        card.style.display = 'block';
        return;
    }

    const gData = getCategoryBenchmark(genreKey);
    if (!gData) {
        card.style.display = 'none';
        return;
    }

    const icon = getGenreIcon(genreKey);
    if (iconElem) iconElem.textContent = icon;
    if (titleElem) titleElem.textContent = `${gData.name || genreKey} Market Radar`;

    card.style.display = 'block';
}

/**
 * Click-to-Analyze Visual Check Competitor Capsule
 */
function openSimulatorGame(appid, imageUrl, name, isUser) {
    if (isUser) {
        const heroBanner = document.getElementById('gameHugeTitleBanner');
        if (heroBanner) heroBanner.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
    }

    // Switch to Home / Analyzer tab if not active
    const navHomeBtn = document.getElementById('navHomeBtn');
    const homeView = document.getElementById('homeView');
    const benchmarkView = document.getElementById('benchmarkView');
    const aiView = document.getElementById('aiView');

    if (navHomeBtn) {
        navHomeBtn.click();
    } else {
        if (homeView) homeView.style.display = 'block';
        if (benchmarkView) benchmarkView.style.display = 'none';
        if (aiView) aiView.style.display = 'none';
    }

    if (appid) {
        const url = `https://store.steampowered.com/app/${appid}/`;
        if (steamUrlInput) steamUrlInput.value = url;
        handleUrlInput(true);
        const heroBanner = document.getElementById('gameHugeTitleBanner');
        if (heroBanner) heroBanner.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (imageUrl) {
        if (steamUrlInput) steamUrlInput.value = imageUrl;
        handleUrlInput(true);
        const heroBanner = document.getElementById('gameHugeTitleBanner');
        if (heroBanner) heroBanner.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

const CHARTS_CONFIG = {
    all: {
        sub: "Comprehensive visual evidence plotted from OpenCV batch processing across 28,754 Steam games.",
        charts: [
            {
                id: 1,
                src: "benchmark/1_brightness_contrast.png",
                title: "Dynamic Contrast & Luminance",
                badge: "+6.2 pts higher contrast in Mega-Hits",
                alt: "Dynamic Contrast & Luminance Distribution Chart",
                modalTitle: "Dynamic Contrast & Luminance Across 5 Sales Tiers",
                footer: "<strong>The Contrast Cliff:</strong> Mega-hits score 63.0 contrast vs. 56.9 for flops. Successful games establish bright focal highlights against deep shadow vignetting, avoiding muddled midtone clustering."
            },
            {
                id: 2,
                src: "benchmark/2_palette_and_saturation.png",
                title: "Color Palette Dynamics & Saliency",
                badge: "+10.9% more warm accents in Top Tier",
                alt: "Color Palette & Saturation Chart",
                modalTitle: "Color Palette Distribution & Saliency on Steam UI",
                footer: "<strong>Steam Dark Navy Contrast:</strong> 49.9% of mega-hits leverage warm palettes (gold, amber, crimson) that naturally pop against Steam's navy client theme (#1b2838). 51.8% of flops blend in with drab neutral tones."
            },
            {
                id: 3,
                src: "benchmark/3_detail_complexity.png",
                title: "Visual Detail & Shannon Entropy",
                badge: "+26.8% sharper line art & silhouettes",
                alt: "Detail Complexity & Shannon Entropy Chart",
                modalTitle: "Visual Detail, Edge Density & Shannon Entropy",
                footer: "<strong>Tonal Depth vs. Screenshot Noise:</strong> Mega-hits exhibit 6.99 bits of entropy and 14.2% edge density. Flop games suffer from muddy raw screenshots or unlit 3D models that blur into noise at 120px scale."
            },
            {
                id: 4,
                src: "benchmark/4_text_readability.png",
                title: "Title Typography & Contrast",
                badge: "3.5:1 Average Text Contrast Ratio",
                alt: "Typography Readability Chart",
                modalTitle: "Title Typography Readability & Contrast Analysis",
                footer: "<strong>Thumbnail Glance Legibility:</strong> Top games maintain high contrast between title text and background art, ensuring title recognition even on mobile or compressed Steam Discovery queues."
            },
            {
                id: 5,
                src: "benchmark/5_title_positioning_heatmap.png",
                title: "Title Positioning Heatmap",
                badge: "Bottom-Center & Top-Center Standard",
                alt: "Title Positioning Heatmap Chart",
                modalTitle: "Title 3×3 Grid Positioning Heatmap",
                footer: "<strong>Unobstructed Character Silhouettes:</strong> Mega-hits strategically place title typography at Bottom-Center (13.3%) or Top-Center (10.7%), whereas flops often plaster text over the hero's face or dead-center."
            },
            {
                id: 6,
                src: "benchmark/6_composition_lighting.png",
                title: "Lighting Focus & Spotlight Vignette",
                badge: "71.9% Central Spotlight Focus in Hits",
                alt: "Composition & Lighting Chart",
                modalTitle: "Composition & Central Spotlight Vignetting",
                footer: "<strong>Anchoring Buyer Attention:</strong> 71.9% of top games concentrate lighting in the center/hero zone while applying subtle perimeter darkening to lock gaze during the critical 1-second browse glance."
            },
            {
                id: 7,
                src: "benchmark/7_genre_visual_profiles.png",
                title: "Genre-Specific Visual Signatures (23,641 Games)",
                badge: "Action vs. RPG vs. Strategy vs. Simulation",
                alt: "Genre Visual Profiles Chart",
                modalTitle: "Genre-Specific Visual Signatures & Profiles",
                footer: "<strong>Tailoring Art to Genre Conventions:</strong> RPG and Strategy games feature higher detail complexity and textural density, whereas Action and Arcade games prioritize high-contrast warm silhouettes for instant impulse clicks."
            }
        ]
    },
    indie: {
        sub: "Empirical comparison of 0-5 friend reviews vs. 6-10 milestone vs. 11-100 ignition vs. 100+ breakout indies.",
        charts: [
            {
                id: 1,
                src: "benchmark/indie_1_brightness_contrast.png",
                title: "Dynamic Contrast in the Indie Funnel",
                badge: "57.0 (Friend Zone) → 61.5+ (Breakouts)",
                alt: "Indie Dynamic Contrast & Luminance Chart",
                modalTitle: "Indie Funnel: Dynamic Contrast & Luminance Across 0 to 100+ Reviews",
                footer: "<strong>The Zero-Review Trap:</strong> Games stuck with 0–5 friend reviews average only 57.0 dynamic contrast and 90.4 brightness (muddled midtones). Crossing into 11–100 reviews requires pushing specular highlights above 60.0."
            },
            {
                id: 2,
                src: "benchmark/indie_2_palette_and_saturation.png",
                title: "Color Temperature in Indie Tiers",
                badge: "61% of 0-5 Rev Games Camouflaged",
                alt: "Indie Color Palette & Saturation Chart",
                modalTitle: "Indie Funnel: Color Temperature & Saliency on Steam UI",
                footer: "<strong>Escaping the Steam UI Camouflage:</strong> 61% of 0–5 review indie capsules use cool/neutral tones that blend into Steam's dark navy background. Breakout indies (100+) use 50% warm accent lighting to pop off the store page."
            },
            {
                id: 3,
                src: "benchmark/indie_3_detail_complexity.png",
                title: "Edge Density & Silhouette Definition",
                badge: "11.2% (Ghost) → 14.1% (100+ Reviews)",
                alt: "Indie Detail Complexity & Edge Density Chart",
                modalTitle: "Indie Funnel: Edge Density & Shannon Entropy",
                footer: "<strong>120px Discovery Queue Silhouette:</strong> 0–5 review games have muddy, low-definition edges (11.2%) that turn into blurry mush when downscaled. Breakout games achieve 14.1% crisp edge definition."
            },
            {
                id: 4,
                src: "benchmark/indie_4_text_readability.png",
                title: "Title Readability & WCAG AA Contrast",
                badge: "38% of 0-5 Rev Games Fail WCAG",
                alt: "Indie Typography & Readability Chart",
                modalTitle: "Indie Funnel: Title Typography & Contrast Analysis",
                footer: "<strong>Readability at a Glance:</strong> 38% of zero-review capsules fail WCAG 3:1 contrast, making titles unreadable against complex background art. Adding a subtle drop shadow or backdrop scrim instantly lifts CTR."
            },
            {
                id: 5,
                src: "benchmark/indie_5_title_positioning_heatmap.png",
                title: "Title Positioning Heatmap (0-5 vs 11-100 vs 100+)",
                badge: "Clean Top/Bottom Anchoring in Breakouts",
                alt: "Indie Title Positioning Heatmap Chart",
                modalTitle: "Indie Funnel: Title Positioning Heatmap Across Review Tiers",
                footer: "<strong>Protecting the Hero Silhouette:</strong> Flop indies (1–5 reviews) often crowd titles in the center where character art lives. Breakout indies anchor logos at Bottom-Center or Top-Center, leaving hero silhouettes unobstructed."
            },
            {
                id: 6,
                src: "benchmark/indie_6_composition_lighting.png",
                title: "Focal Lighting & Specular Ratio",
                badge: "+10% Specular Highlight Area in Breakouts",
                alt: "Indie Composition & Lighting Chart",
                modalTitle: "Indie Funnel: Composition & Central Spotlight Vignetting",
                footer: "<strong>Radial Spotlight Mastery:</strong> Games reaching 11–100+ reviews have 10% more bright highlight accents (>180) and apply 15% radial perimeter darkening to direct buyer eye-tracking directly to the focal point."
            },
            {
                id: 7,
                src: "benchmark/indie_7_genre_visual_profiles.png",
                title: "Zero-to-100 Quality Metric Progression",
                badge: "Relative Index: 0 → 100+ Review Milestones",
                alt: "Indie Quality Metric Progression Chart",
                modalTitle: "Indie Funnel: Zero-to-100 Quality Progression & Genre Distribution",
                footer: "<strong>The Breakthrough Milestone Index:</strong> Every visual metric (Dynamic Contrast, Entropy, Edge Density, Luminance) shows a steady, correlated climb from 0 reviews to 100+ breakout indies across all major genres."
            }
        ]
    }
};

let currentChartMode = 'all';

/**
 * Switch between All Steam Games (Macro) and Indie Zero-to-100 Funnel charts
 */
function switchChartMode(mode, updateUrl = false) {
    if (!CHARTS_CONFIG[mode]) return;
    currentChartMode = mode;

    const config = CHARTS_CONFIG[mode];

    const subElem = document.getElementById('benchmarkChartsSub');
    if (subElem) subElem.textContent = config.sub;

    const btnAll = document.getElementById('btnChartsAll');
    const btnIndie = document.getElementById('btnChartsIndie');
    if (btnAll) btnAll.classList.toggle('active', mode === 'all');
    if (btnIndie) btnIndie.classList.toggle('active', mode === 'indie');

    config.charts.forEach(c => {
        const titleElem = document.getElementById(`chart${c.id}Title`);
        const badgeElem = document.getElementById(`chart${c.id}Badge`);
        const wrapperElem = document.getElementById(`chart${c.id}Wrapper`);
        const imgElem = document.getElementById(`chart${c.id}Img`);
        const footerElem = document.getElementById(`chart${c.id}Footer`);

        if (titleElem) titleElem.textContent = c.title;
        if (badgeElem) badgeElem.textContent = c.badge;
        if (wrapperElem) {
            wrapperElem.setAttribute('data-chart-src', c.src);
            wrapperElem.setAttribute('data-chart-title', c.modalTitle);
        }
        if (imgElem) {
            imgElem.src = c.src;
            imgElem.alt = c.alt;
        }
        if (footerElem) footerElem.innerHTML = `<p>${c.footer}</p>`;
    });

    if (updateUrl) {
        const url = new URL(window.location);
        if (mode === 'all') {
            url.searchParams.delete('chart_mode');
            url.searchParams.delete('charts');
        } else {
            url.searchParams.set('chart_mode', mode);
        }
        window.history.replaceState({}, '', url.toString());
    }
}

// Expose switchChartMode globally
window.switchChartMode = switchChartMode;

const SHOWCASE_TABS_CONFIG = {
    top_rated: {
        icon: "🏆",
        title: "Top 25 Highest-Rated Steam Capsules",
        sub: "Masterpiece capsules achieving top scores (98–99/100) across Dynamic Contrast, Steam UI Pop, and Compositional Lighting.",
        type: "top"
    },
    lowest_rated: {
        icon: "🕳️",
        title: "Lowest 25 Rated Flop Capsules",
        sub: "Capsules scoring near-zero due to critical visual flaws (flat midtones, cold palette blending, unreadable titles).",
        type: "flop"
    },
    zero_reviews: {
        icon: "👻",
        title: "0 Reviews (Ghost Zone / Unbought Capsules)",
        sub: "Real Steam capsules with 0 reviews. Notice the flat lighting, unreadable text, and cold blue palettes that camouflage against Steam.",
        type: "flop"
    },
    reviews_1_5: {
        icon: "👥",
        title: "1–5 Reviews (Friend Reviews Only)",
        sub: "Games stuck in the 1–5 review range. These capsules rarely attract organic store impressions or discovery queue clicks.",
        type: "flop"
    },
    reviews_6_10: {
        icon: "⚡",
        title: "6–10 Reviews (Threshold Frontier)",
        sub: "Games right at the edge of unlocking the first official Steam Review Score badge (e.g. 'Positive').",
        type: "neutral"
    },
    reviews_11_100: {
        icon: "🚀",
        title: "11–100 Reviews (Algorithm Ignition)",
        sub: "Indies breaking into organic Steam Discovery Queue testing. Notice the sharper silhouettes and specular highlights.",
        type: "top"
    },
    reviews_100_500: {
        icon: "🌟",
        title: "100–500 Reviews (Sustainable Indie Breakouts)",
        sub: "Commercially validated indies with proven product-market fit, strong store conversion, punchy contrast (>60.0), and 50%+ warm accent lighting.",
        type: "top"
    },
    reviews_100_plus: {
        icon: "🌟",
        title: "100–500 Reviews (Sustainable Indie Breakouts)",
        sub: "Commercially validated indies with proven product-market fit, strong store conversion, punchy contrast (>60.0), and 50%+ warm accent lighting.",
        type: "top"
    }
};

let currentShowcaseTab = 'top_rated';

/**
 * Switch 5x5 Showcase Category Tab
 */
function switchShowcaseTab(tabKey, updateUrl = false) {
    if (!SHOWCASE_TABS_CONFIG[tabKey]) return;
    currentShowcaseTab = tabKey;

    const config = SHOWCASE_TABS_CONFIG[tabKey];

    const iconElem = document.getElementById('showcaseHeaderIcon');
    const titleElem = document.getElementById('showcaseHeaderTitle');
    const subElem = document.getElementById('showcaseHeaderSub');

    if (iconElem) iconElem.textContent = config.icon;
    if (titleElem) titleElem.textContent = config.title;
    if (subElem) subElem.textContent = config.sub;

    document.querySelectorAll('.showcase-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-showcase') === tabKey);
    });

    const grid = document.getElementById('benchmarkShowcaseGrid');
    if (!grid) return;

    let games = [];
    if (benchmarksData && benchmarksData.showcases && benchmarksData.showcases[tabKey]) {
        games = benchmarksData.showcases[tabKey];
    } else if (benchmarksData && benchmarksData[tabKey]) {
        games = benchmarksData[tabKey];
    }

    if (games && games.length > 0) {
        grid.innerHTML = games.map((game, idx) => createBenchmarkCard(game, idx, config.type)).join('');
        // Attach click listeners to cards to open in Capsulu Simulator / Analyzer
        grid.querySelectorAll('.benchmark-capsule-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.card-ext-link')) return; // Allow direct store link click
                const appid = card.getAttribute('data-appid');
                const img = card.getAttribute('data-img');
                const name = card.getAttribute('data-name');
                openSimulatorGame(appid, img, name, false);
            });
        });
    } else {
        grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 40px; text-align: center; color: #8f98a0;">Loading showcase capsules...</div>`;
    }

    if (updateUrl) {
        const url = new URL(window.location);
        if (tabKey === 'top_rated') {
            url.searchParams.delete('showcase');
            url.searchParams.delete('showcase_tab');
        } else {
            url.searchParams.set('showcase', tabKey);
        }
        window.history.replaceState({}, '', url.toString());
    }
}

// Expose switchShowcaseTab globally
window.switchShowcaseTab = switchShowcaseTab;

function createBenchmarkCard(game, index, type) {
    const isTop = type === 'top';
    const isNeutral = type === 'neutral';
    const cardClass = isTop ? 'card-top' : (isNeutral ? 'card-neutral' : 'card-flop');
    const revCount = Number(game.reviews !== undefined ? game.reviews : 0);
    const revText = `${revCount.toLocaleString()} ${revCount === 1 ? 'review' : 'reviews'}`;
    const tooltip = `${game.name} • #${index + 1} • ${game.palette_type || 'neutral'} • ${revText} (Click to Analyze)`;

    return `
        <div class="benchmark-capsule-card ${cardClass}" 
             data-appid="${game.appid}" 
             data-img="${game.imageUrl}" 
             data-name="${encodeURIComponent(game.name)}" 
             data-reviews="${game.reviews !== undefined ? game.reviews : ''}" 
             title="${tooltip}">
            <img src="${game.imageUrl}" alt="${game.name}" loading="lazy" class="card-capsule-img" onerror="this.onerror=null; this.src='https://cdn.akamai.steamstatic.com/steam/apps/${game.appid}/capsule_616x353.jpg';">
        </div>
    `;
}

/**
 * Retrieve Competitor Capsule Catalog for Specific Genre / Tag / All
 */
function getCompetitorsForLens(lensKey) {
    if (typeof benchmarksData === 'undefined' || !benchmarksData.genre_competitors) {
        return typeof STORE_CATALOG !== 'undefined' ? STORE_CATALOG : [];
    }
    const comps = benchmarksData.genre_competitors;
    if (!lensKey || lensKey === 'all' || lensKey.toLowerCase() === 'all steam games') {
        return comps['all'] || comps['overall'] || STORE_CATALOG;
    }

    // 1. Direct match
    if (comps[lensKey] && comps[lensKey].length > 0) {
        return comps[lensKey];
    }

    // 2. Exact case-insensitive match
    const exact = Object.keys(comps).find(k => k.toLowerCase() === lensKey.toLowerCase());
    if (exact && comps[exact] && comps[exact].length > 0) {
        return comps[exact];
    }

    // 3. Punctuation-normalized match (e.g. "Rogue-lite" vs "Roguelite", "Co-op" vs "Coop")
    const normKey = lensKey.toLowerCase().replace(/[^a-z0-9]/g, '');
    const normMatch = Object.keys(comps).find(k => k.toLowerCase().replace(/[^a-z0-9]/g, '') === normKey);
    if (normMatch && comps[normMatch] && comps[normMatch].length > 0) {
        return comps[normMatch];
    }

    // 4. Substring inclusion match
    const partial = Object.keys(comps).find(k => lensKey.toLowerCase().includes(k.toLowerCase()) || k.toLowerCase().includes(lensKey.toLowerCase()));
    if (partial && comps[partial] && comps[partial].length > 0) {
        return comps[partial];
    }

    // 5. Keyword token overlap match (e.g. "Action Adventure" -> matches "Action" or "Adventure")
    const words = lensKey.toLowerCase().split(/[\s\-_/]+/).filter(w => w.length > 2);
    for (const w of words) {
        const tokenMatch = Object.keys(comps).find(k => k.toLowerCase().includes(w));
        if (tokenMatch && comps[tokenMatch] && comps[tokenMatch].length > 0) {
            return comps[tokenMatch];
        }
    }

    return comps['all'] || comps['overall'] || STORE_CATALOG;
}

/**
 * Render In-Situ Competition Simulator (Contextual Genre/Tag Lineup with User in Center Position)
 */
function renderSimulatorLineups(userImgSrc, userGameName, appid, genreKey = 'all') {
    const catalog = getCompetitorsForLens(genreKey || 'all');

    // Filter out user's current game from the catalog
    let others = catalog.filter(g => String(g.appid) !== String(appid) && (g.name || "").toLowerCase() !== (userGameName || "").toLowerCase());

    // Backfill from global catalog if fewer than 8 competitors available for this niche tag
    if (others.length < 8) {
        const globalComps = (typeof benchmarksData !== 'undefined' && benchmarksData && benchmarksData.genre_competitors && benchmarksData.genre_competitors['all']) || STORE_CATALOG;
        for (const gc of globalComps) {
            if (others.length >= 8) break;
            if (String(gc.appid) !== String(appid) && !others.some(o => String(o.appid) === String(gc.appid))) {
                others.push(gc);
            }
        }
    }

    // Exactly 9 items: 4 surrounding games, USER CAPSULE (at index 4 / center), 4 surrounding games
    const fallbackGame = { name: "Steam Game", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg", appid: 1245620 };
    const items9 = [
        others[0] || fallbackGame,
        others[1] || fallbackGame,
        others[2] || fallbackGame,
        others[3] || fallbackGame,
        { name: userGameName || "This Game", imageUrl: userImgSrc, isUser: true, appid: appid }, // Center (Row 2, Col 2)
        others[4] || fallbackGame,
        others[5] || fallbackGame,
        others[6] || fallbackGame,
        others[7] || fallbackGame
    ];

    // In-Situ 3x3 Capsule Lineup (User in Exact Center)
    const largeGrid = document.getElementById('largeSimRow');
    if (largeGrid) {
        largeGrid.innerHTML = items9.map(g => `
            <div class="sim-capsule-item ${g.isUser ? 'user-capsule-item' : 'clickable-sim-item'}" 
                 data-appid="${g.appid || ''}" 
                 data-image-url="${g.imageUrl || ''}" 
                 data-name="${g.name || ''}" 
                 data-is-user="${g.isUser ? 'true' : 'false'}"
                 title="${g.isUser ? 'This Capsule (Current Analysis)' : `Click to analyze ${g.name}`}"
                 tabindex="${g.isUser ? '-1' : '0'}"
                 role="${g.isUser ? 'img' : 'button'}">
                <div class="sim-capsule-thumb">
                    <img src="${g.imageUrl}" alt="${g.name}" loading="lazy" onerror="this.onerror=null; this.src='https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg';">
                </div>
            </div>
        `).join('');
    }
}

/**
 * Look up known review count for an AppID or Game Name from benchmarksData
 */
function findKnownReviews(appid, gameName) {
    if (typeof benchmarksData === 'undefined' || !benchmarksData) return null;
    const numAppId = appid ? Number(appid) : null;
    const cleanName = gameName ? gameName.trim().toLowerCase() : null;

    function match(obj) {
        if (!obj) return false;
        if (numAppId && Number(obj.appid) === numAppId) return true;
        if (cleanName && obj.name && obj.name.trim().toLowerCase() === cleanName) return true;
        return false;
    }

    if (Array.isArray(benchmarksData.presets)) {
        const found = benchmarksData.presets.find(match);
        if (found && (found.reviews !== undefined || found.total_reviews !== undefined)) {
            return found.reviews !== undefined ? found.reviews : found.total_reviews;
        }
    }

    if (benchmarksData.showcases) {
        for (const key of Object.keys(benchmarksData.showcases)) {
            const list = benchmarksData.showcases[key];
            if (Array.isArray(list)) {
                const found = list.find(match);
                if (found && (found.reviews !== undefined || found.total_reviews !== undefined)) {
                    return found.reviews !== undefined ? found.reviews : found.total_reviews;
                }
            }
        }
    }

    if (benchmarksData.genre_competitors) {
        for (const key of Object.keys(benchmarksData.genre_competitors)) {
            const list = benchmarksData.genre_competitors[key];
            if (Array.isArray(list)) {
                const found = list.find(match);
                if (found && (found.reviews !== undefined || found.total_reviews !== undefined)) {
                    return found.reviews !== undefined ? found.reviews : found.total_reviews;
                }
            }
        }
    }

    return null;
}

/**
 * Main Analysis and Dashboard Update
 */
function analyzeAndDisplay(img, imgSrc, gameName, price, tags, appid, storeUrl, genres = [], reviews = null, precomputedCv = null, precomputedScores = null) {
    const cv = precomputedCv || runComputerVision(img);
    const scores = precomputedScores || evaluateScores(cv);

    // Save global state
    currentCvResult = cv;
    currentScores = scores;
    currentLoadedImgSrc = imgSrc;
    currentLoadedGameName = gameName || "Steam Game";
    currentLoadedAppId = appid;
    currentLoadedTags = tags || [];
    currentLoadedGenres = genres || [];

    // Default comparison selection is always All Steam Games ('all')
    currentGenreLens = 'all';

    // 1. Update TOP HERO CARD with Big Game Title, Direct Steam Link, and Image
    document.getElementById('resultHeroCapsuleImg').src = imgSrc;
    document.getElementById('resultGameTitleText').textContent = gameName || "Steam Game";

    const gameTitleLink = document.getElementById('resultGameTitleLink');
    const resultHeroCapsuleLink = document.getElementById('resultHeroCapsuleLink');
    const storeBtnLink = document.getElementById('resultStoreBtnLink');
    const appIdTag = document.getElementById('resultAppIdTag');
    const priceTag = document.getElementById('resultPriceTag');
    const reviewsTag = document.getElementById('resultReviewsTag');
    const heroTagsContainer = document.getElementById('resultHeroTags');

    const effectiveStoreUrl = storeUrl || (appid ? `https://store.steampowered.com/app/${appid}/` : null);

    if (resultHeroCapsuleLink) {
        if (effectiveStoreUrl) {
            resultHeroCapsuleLink.href = effectiveStoreUrl;
            resultHeroCapsuleLink.style.pointerEvents = 'auto';
            resultHeroCapsuleLink.style.cursor = 'pointer';
            resultHeroCapsuleLink.title = `Open ${gameName || 'game'} on Steam (New Tab)`;
        } else {
            resultHeroCapsuleLink.removeAttribute('href');
            resultHeroCapsuleLink.style.pointerEvents = 'none';
            resultHeroCapsuleLink.style.cursor = 'default';
            resultHeroCapsuleLink.title = 'Capsule Artwork';
        }
    }

    if (gameTitleLink) {
        if (effectiveStoreUrl) {
            gameTitleLink.href = effectiveStoreUrl;
            gameTitleLink.style.pointerEvents = 'auto';
        } else {
            gameTitleLink.removeAttribute('href');
            gameTitleLink.style.pointerEvents = 'none';
        }
    }

    if (storeBtnLink) {
        if (effectiveStoreUrl) {
            storeBtnLink.href = effectiveStoreUrl;
            storeBtnLink.style.display = 'inline-flex';
        } else {
            storeBtnLink.style.display = 'none';
        }
    }

    if (appIdTag) {
        appIdTag.textContent = appid ? `App ID: ${appid}` : 'Steam Store';
        appIdTag.style.display = 'inline-block';
    }

    if (priceTag) {
        if (price && price !== "N/A") {
            priceTag.textContent = price;
            priceTag.style.display = 'inline-block';
        } else {
            priceTag.style.display = 'none';
        }
    }

    const effectiveReviews = (reviews !== null && reviews !== undefined) ? reviews : findKnownReviews(appid, gameName);
    if (reviewsTag) {
        if (effectiveReviews !== null && effectiveReviews !== undefined && !isNaN(effectiveReviews) && effectiveReviews !== '') {
            const revNum = Number(effectiveReviews);
            const revLabel = revNum === 1 ? '1 review' : `${revNum.toLocaleString()} reviews`;
            reviewsTag.textContent = `💬 ${revLabel}`;
            reviewsTag.style.display = 'inline-block';
            reviewsTag.title = `Total Steam User Reviews: ${revNum.toLocaleString()}`;
        } else {
            reviewsTag.style.display = 'none';
        }
    }

    // Separate genres and pure tags (excluding duplicates)
    const genreList = Array.isArray(genres) ? genres.filter(Boolean) : [];
    const tagList = Array.isArray(tags) ? tags.filter(t => t && !genreList.some(g => g.toLowerCase() === t.toLowerCase())) : [];

    const heroGenresContainer = document.getElementById('resultHeroGenres');
    const heroGenresGroup = document.getElementById('resultHeroGenresGroup');
    if (heroGenresContainer && heroGenresGroup) {
        heroGenresContainer.innerHTML = '';
        if (genreList.length > 0) {
            heroGenresGroup.style.display = 'inline-flex';
            genreList.forEach(g => {
                const badge = document.createElement('span');
                badge.className = 'genre-pill-badge';
                badge.textContent = g;
                heroGenresContainer.appendChild(badge);
            });
        } else {
            heroGenresGroup.style.display = 'none';
        }
    }

    const heroTagsGroup = document.getElementById('resultHeroTagsGroup');
    if (heroTagsContainer && heroTagsGroup) {
        heroTagsContainer.innerHTML = '';
        if (tagList.length > 0) {
            heroTagsGroup.style.display = 'inline-flex';
            tagList.forEach(t => {
                const badge = document.createElement('span');
                badge.className = 'tag-pill-badge';
                badge.textContent = t;
                heroTagsContainer.appendChild(badge);
            });
        } else {
            heroTagsGroup.style.display = 'none';
        }
    }

    // 2. Populate Synchronized Dropdowns with this Game's Exact Genres & Tags
    populateGenreDropdowns(currentLoadedGenres, currentLoadedTags);

    // 3. Update Dedicated Genre Benchmark Radar Intelligence Card
    updateGenreBenchmarkDisplay(cv, currentGenreLens);

    // 4. Render Contextual Simulator Lineups
    renderSimulatorLineups(imgSrc, gameName || "Your Game", appid, currentGenreLens);

    // 5. Update Top Score Banner
    document.getElementById('overallScoreNum').textContent = scores.overallScore;

    const gaugeFill = document.getElementById('gaugeFill');
    const offset = 440 - (440 * scores.overallScore / 100);
    const themeColor = scores.overallScore >= 80 ? 'var(--green-pass)' : scores.overallScore >= 65 ? 'var(--gold)' : 'var(--red)';
    gaugeFill.style.strokeDashoffset = offset;
    gaugeFill.style.stroke = themeColor;

    const tierBadge = document.getElementById('predictedTierBadge');
    if (tierBadge) {
        tierBadge.textContent = scores.tierName;
        tierBadge.className = `tier-badge ${scores.tierBadgeClass}`;
    }

    const percentileElem = document.getElementById('percentileText');
    if (percentileElem) {
        percentileElem.textContent = scores.percentile;
    }
    document.getElementById('scoreHeadline').textContent = scores.headline;
    document.getElementById('scoreSummary').textContent = scores.summary;

    // 5.4 Update AI Commercial Forecast Card
    updateCommercialForecast(scores, cv, effectiveReviews, appid, img);

    // 5.5 Update Dominant Scorecard Quick-Metrics Table with Color-Coded Ratings
    // Contrast (Mega-Hit Benchmark: 63.0)
    const qsContrastElem = document.getElementById('qsContrast');
    if (qsContrastElem) {
        qsContrastElem.textContent = `${cv.brightnessStd} std dev`;
        qsContrastElem.className = `qm-val ${cv.brightnessStd >= 63 ? 'val-green' : cv.brightnessStd >= 58 ? 'val-gold' : 'val-red'}`;
    }
    const qmBadgeContrast = document.getElementById('qmBadgeContrast');
    if (qmBadgeContrast) {
        qmBadgeContrast.textContent = cv.brightnessStd >= 63 ? 'High Punch' : cv.brightnessStd >= 58 ? 'Moderate' : 'Flat Midtones';
        qmBadgeContrast.className = `qm-badge ${cv.brightnessStd >= 63 ? 'qm-badge-green' : cv.brightnessStd >= 58 ? 'qm-badge-gold' : 'qm-badge-red'}`;
    }
    const qmSubContrast = document.getElementById('qmSubContrast');
    if (qmSubContrast) {
        qmSubContrast.textContent = cv.brightnessStd >= 63 ? '✓ Beats Mega-Hit Avg (63.0)' : '⚠️ Below 63.0 Mega-Hit Avg (Flat Midtones)';
    }

    // Warmth / Saliency (Mega-Hit Benchmark: 45%)
    const qsPaletteElem = document.getElementById('qsPalette');
    if (qsPaletteElem) {
        qsPaletteElem.textContent = `${cv.warmPct}% Warm Saliency`;
        qsPaletteElem.className = `qm-val ${cv.warmPct >= 45 ? 'val-green' : cv.warmPct >= 35 ? 'val-gold' : 'val-red'}`;
    }
    const qmBadgePalette = document.getElementById('qmBadgePalette');
    if (qmBadgePalette) {
        qmBadgePalette.textContent = cv.warmPct >= 45 ? 'High Pop' : cv.warmPct >= 35 ? 'Moderate' : 'Low Pop (Cold Blend)';
        qmBadgePalette.className = `qm-badge ${cv.warmPct >= 45 ? 'qm-badge-green' : cv.warmPct >= 35 ? 'qm-badge-gold' : 'qm-badge-red'}`;
    }
    const qmSubPalette = document.getElementById('qmSubPalette');
    if (qmSubPalette) {
        qmSubPalette.textContent = cv.warmPct >= 45 ? '✓ Strong against Steam UI' : '⚠️ Mostly cool/neutral palette (Needs Warm Accent)';
    }

    // Entropy / Texture
    const qsEntropyElem = document.getElementById('qsEntropy');
    if (qsEntropyElem) {
        qsEntropyElem.textContent = `${cv.entropy} bits depth`;
        qsEntropyElem.className = `qm-val ${cv.entropy >= 6.8 ? 'val-green' : cv.entropy >= 6.2 ? 'val-gold' : 'val-red'}`;
    }
    const qmBadgeEntropy = document.getElementById('qmBadgeEntropy');
    if (qmBadgeEntropy) {
        qmBadgeEntropy.textContent = cv.entropy >= 6.8 ? 'Rich Detail' : cv.entropy >= 6.2 ? 'Adequate' : 'Low Detail';
        qmBadgeEntropy.className = `qm-badge ${cv.entropy >= 6.8 ? 'qm-badge-green' : cv.entropy >= 6.2 ? 'qm-badge-gold' : 'qm-badge-red'}`;
    }
    const qmSubEntropy = document.getElementById('qmSubEntropy');
    if (qmSubEntropy) {
        qmSubEntropy.textContent = cv.entropy >= 6.8 ? '✓ Deep tonal rendering' : '⚠️ Washed midtone gradients';
    }

    // Focal Lighting / Spotlight
    const qsFocusElem = document.getElementById('qsFocus');
    if (qsFocusElem) {
        qsFocusElem.textContent = cv.isCenterFocused ? `Spotlight (+${cv.spotlightRatio})` : 'Border-Heavy';
        qsFocusElem.className = `qm-val ${cv.isCenterFocused ? 'val-green' : 'val-gold'}`;
    }
    const qmBadgeFocus = document.getElementById('qmBadgeFocus');
    if (qmBadgeFocus) {
        qmBadgeFocus.textContent = cv.isCenterFocused ? 'Spotlit' : 'Needs Vignette';
        qmBadgeFocus.className = `qm-badge ${cv.isCenterFocused ? 'qm-badge-green' : 'qm-badge-gold'}`;
    }
    const qmSubFocus = document.getElementById('qmSubFocus');
    if (qmSubFocus) {
        qmSubFocus.textContent = cv.isCenterFocused ? '✓ Central hero illuminated' : '⚠️ Outer edges need vignette';
    }

    // Title Contrast & Clarity Quick Metric
    const qsTextElem = document.getElementById('qsText');
    if (qsTextElem) {
        qsTextElem.textContent = `${cv.titleContrast}:1 WCAG`;
        qsTextElem.className = `qm-val ${cv.titleContrast >= 4.5 ? 'val-green' : cv.titleContrast >= 3.0 ? 'val-gold' : 'val-red'}`;
    }
    const qmBadgeText = document.getElementById('qmBadgeText');
    if (qmBadgeText) {
        qmBadgeText.textContent = cv.titleContrast >= 4.5 ? 'High Clarity' : cv.titleContrast >= 3.0 ? 'Moderate' : 'Low Contrast';
        qmBadgeText.className = `qm-badge ${cv.titleContrast >= 4.5 ? 'qm-badge-green' : cv.titleContrast >= 3.0 ? 'qm-badge-gold' : 'qm-badge-red'}`;
    }
    const qmSubText = document.getElementById('qmSubText');
    if (qmSubText) {
        qmSubText.textContent = cv.titleContrast >= 4.5 ? '✓ Meets WCAG AA standard' : '⚠️ Text risks blending into art';
    }

    // Title Placement & Coverage Quick Metric
    const qsLogoZoneElem = document.getElementById('qsLogoZone');
    if (qsLogoZoneElem) {
        qsLogoZoneElem.textContent = `${cv.titleZone} (${cv.titleSizePct}%)`;
        qsLogoZoneElem.className = `qm-val ${cv.titleSizePct >= 12 && cv.titleSizePct <= 35 ? 'val-green' : 'val-gold'}`;
    }
    const qmBadgeLogoZone = document.getElementById('qmBadgeLogoZone');
    if (qmBadgeLogoZone) {
        qmBadgeLogoZone.textContent = cv.titleSizeLabel || cv.titleSizeClass;
        qmBadgeLogoZone.className = `qm-badge ${cv.titleSizePct >= 12 && cv.titleSizePct <= 35 ? 'qm-badge-green' : 'qm-badge-gold'}`;
    }
    const qmSubLogoZone = document.getElementById('qmSubLogoZone');
    if (qmSubLogoZone) {
        qmSubLogoZone.textContent = cv.titleSizePct >= 14 ? '✓ Clear at 120px scale' : '⚠️ Title text may be too small in queue';
    }

    // 6. Update Palette Swatches & D3 Cake Diagram
    renderPalettePieChart(cv.dominantColors);

    const swatchesContainer = document.getElementById('paletteSwatches');
    swatchesContainer.innerHTML = '';
    cv.dominantColors.forEach((c, index) => {
        const swatch = document.createElement('div');
        swatch.className = 'swatch-item';
        swatch.innerHTML = `
            <div class="swatch-preview" style="background-color: ${c.hex};"></div>
            <div class="swatch-hex">${c.hex}</div>
            <div class="swatch-pct">${c.pct}%</div>
        `;
        swatch.addEventListener("mouseenter", () => {
            const slices = d3.selectAll("#palettePieChart path");
            slices.filter((d, idx) => idx === index).transition().duration(150).attr("d", d3.arc().innerRadius(36).outerRadius(64).padAngle(0.03));
            const centerLabel = document.getElementById("pieCenterPct");
            if (centerLabel) centerLabel.textContent = c.pct + "%";
        });
        swatch.addEventListener("mouseleave", () => {
            const slices = d3.selectAll("#palettePieChart path");
            slices.filter((d, idx) => idx === index).transition().duration(150).attr("d", d3.arc().innerRadius(36).outerRadius(60).padAngle(0.03));
            const centerLabel = document.getElementById("pieCenterPct");
            if (centerLabel) centerLabel.textContent = "100%";
        });
        swatchesContainer.appendChild(swatch);
    });

    // 7. Update 6 Metric Rows
    updateMetricRow('mContrastScore', 'mContrastBar', 'mContrastVal', scores.contrastScore, `This: ${cv.brightnessStd} std dev`, (cv.brightnessStd / 85) * 100);
    updateMetricRow('mWarmthScore', 'mWarmthBar', 'mWarmthVal', scores.warmthScore, `This: ${cv.warmPct}% Warm`, Math.min(100, cv.warmPct * 1.5));
    updateMetricRow('mEntropyScore', 'mEntropyBar', 'mEntropyVal', scores.entropyScore, `This: ${cv.entropy} bits`, (cv.entropy / 7.5) * 100);
    updateMetricRow('mEdgeScore', 'mEdgeBar', 'mEdgeVal', scores.edgeScore, `This: ${cv.edgeDensity}% Edge`, (cv.edgeDensity / 22) * 100);
    updateMetricRow('mFocusScore', 'mFocusBar', 'mFocusVal', scores.focusScore, cv.isCenterFocused ? `Center Focused (+${cv.spotlightRatio})` : 'Border-Heavy', cv.isCenterFocused ? 85 : 45);
    updateMetricRow('mTextScore', 'mTextBar', 'mTextVal', scores.textScore, `This: ${cv.titleContrast}:1 (${cv.titleReadabilityLabel})`, Math.min(100, (cv.titleContrast / 10) * 100));

    // 8. Generate Tailored Checklist & AI Art Fix Prompt
    generateChecklist(cv, scores, currentGenreLens);
    updateAiPromptCard(cv, scores, gameName, appid, imgSrc, currentGenreLens);

    // 8.5 Bind Click-to-Scroll on Quick Metric Cells
    bindQuickMetricsScroll();

    // Show Dashboard & Smooth Scroll
    resultsDashboard.style.display = 'block';

    setTimeout(() => {
        const target = document.getElementById('gameHugeTitleBanner') || document.querySelector('.top-hero-two-col-grid') || resultsDashboard;
        if (target) {
            const nav = document.querySelector('.steam-global-nav');
            const navHeight = nav ? nav.offsetHeight : 64;
            const targetY = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;
            window.scrollTo({
                top: Math.max(0, targetY),
                behavior: 'smooth'
            });
        }
    }, 50);
}

/**
 * Scroll to Design Recommendations & Highlight the Target Checklist Item
 */
function scrollToRecommendation(recId) {
    const recsPanel = document.getElementById('recsPanel');
    if (!recsPanel) return;

    const nav = document.querySelector('.steam-global-nav');
    const navHeight = nav ? nav.offsetHeight : 64;
    const targetY = recsPanel.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;

    window.scrollTo({
        top: Math.max(0, targetY),
        behavior: 'smooth'
    });

    if (recId) {
        setTimeout(() => {
            const card = document.getElementById(recId);
            if (card) {
                card.classList.remove('rec-highlight-pulse');
                void card.offsetWidth; // trigger reflow
                card.classList.add('rec-highlight-pulse');
                card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }, 350);
    }
}

/**
 * Bind Quick Metric Cells to Scroll to their Respective Recommendation Cards
 */
function bindQuickMetricsScroll() {
    const qmBindings = [
        { id: 'qmCellContrast', recId: 'rec-contrast' },
        { id: 'qmCellPalette', recId: 'rec-palette' },
        { id: 'qmCellEntropy', recId: 'rec-entropy' },
        { id: 'qmCellFocus', recId: 'rec-focus' },
        { id: 'qmCellText', recId: 'rec-text' },
        { id: 'qmCellLogoZone', recId: 'rec-logo-zone' },
        { id: 'mRowContrast', recId: 'rec-contrast' },
        { id: 'mRowWarmth', recId: 'rec-palette' },
        { id: 'mRowEntropy', recId: 'rec-entropy' },
        { id: 'mRowEdge', recId: 'rec-edge' },
        { id: 'mRowFocus', recId: 'rec-focus' },
        { id: 'mRowText', recId: 'rec-text' }
    ];

    qmBindings.forEach(b => {
        const elem = document.getElementById(b.id);
        if (elem && !elem.dataset.boundScroll) {
            elem.dataset.boundScroll = 'true';
            elem.style.cursor = 'pointer';
            elem.title = 'Click to view design recommendation';
            elem.addEventListener('click', () => {
                scrollToRecommendation(b.recId);
            });
        }
    });
}

function formatZoneName(zoneKey) {
    const map = {
        top_left: "Top Left",
        top_center: "Top Center",
        top_right: "Top Right",
        mid_left: "Middle Left",
        mid_center: "Middle Center",
        mid_right: "Middle Right",
        bot_left: "Bottom Left",
        bot_center: "Bottom Center",
        bot_right: "Bottom Right"
    };
    return map[zoneKey] || zoneKey || "Middle Center";
}

function updateMetricRow(badgeId, barId, valId, score, valText, barWidthPct) {
    const badge = document.getElementById(badgeId);
    if (badge) {
        badge.textContent = `${score}/100`;
        badge.className = `metric-tag ${score >= 85 ? 'tag-green' : score >= 70 ? 'tag-gold' : 'tag-red'}`;
    }

    const bar = document.getElementById(barId);
    if (bar) {
        bar.style.width = `${Math.min(100, Math.max(10, barWidthPct))}%`;
        bar.className = `metric-progress-fill ${score >= 85 ? 'fill-pass' : score >= 70 ? 'fill-warn' : 'fill-fail'}`;
    }

    const valElem = document.getElementById(valId);
    if (valElem) {
        valElem.textContent = valText;
    }
}

/**
 * Generate Tailored Checklist Recommendations (with Genre-Specific Intelligence)
 */
function generateChecklist(cv, scores, genreKey = 'all') {
    const container = document.getElementById('checklistContainer');
    container.innerHTML = '';

    const items = [];

    // 1. Genre-specific tailored card at the top
    let targetGenre = genreKey;
    if (!targetGenre || targetGenre === 'all') {
        targetGenre = detectGenreFromTags(currentLoadedTags) || 'Action';
    }

    if (typeof benchmarksData !== 'undefined' && benchmarksData.genres && benchmarksData.genres[targetGenre]) {
        const gMeta = benchmarksData.genres[targetGenre];
        items.push({
            id: 'rec-tag',
            status: 'pass',
            title: `🏷️ ${targetGenre} Tag Market Advice`,
            desc: gMeta.tip
        });
    }

    // 2. Title Contrast & Readability
    if (cv.titleContrast >= 4.5) {
        items.push({
            id: 'rec-text',
            status: 'pass',
            title: 'Title Typography Contrast & Legibility',
            desc: `The title typography achieves a strong ${cv.titleContrast}:1 contrast ratio against the backdrop (WCAG AA standard). It will remain sharp on small mobile screens and browse carousels.`
        });
    } else if (cv.titleContrast >= 3.0) {
        items.push({
            id: 'rec-text',
            status: 'warn',
            title: 'Enhance Title Text Backdrop Contrast',
            desc: `Title contrast is moderate (${cv.titleContrast}:1 vs 5.2:1 Mega-Hit avg). Consider adding a subtle dark drop shadow, outer stroke outline, or dark scrim behind the title text to prevent blending into the background.`
        });
    } else {
        items.push({
            id: 'rec-text',
            status: 'fail',
            title: 'Critical: Low Title Contrast (< 3.0:1)',
            desc: `The title contrast (${cv.titleContrast}:1) is very low. The title text blends directly into the artwork and may be unreadable at 120px browse resolutions. Add a dark scrim, heavy drop shadow, or highlight stroke.`
        });
    }

    // 3. Title Placement & Scale Coverage
    if (cv.titleSizePct >= 14 && cv.titleSizePct <= 28) {
        items.push({
            id: 'rec-logo-zone',
            status: 'pass',
            title: 'Title Placement & Sizing',
            desc: `The title text occupies ${cv.titleSizePct}% of the capsule in the ${cv.titleZone} zone, hitting the optimal commercial balance between title readability and hero art visibility.`
        });
    } else if (cv.titleSizePct < 14) {
        items.push({
            id: 'rec-logo-zone',
            status: 'warn',
            title: 'Increase Title Text Scale',
            desc: `Title text coverage is relatively compact (${cv.titleSizePct}% vs optimal 18-25%). Scale up the title typography by 15-25% in the ${cv.titleZone} area so game branding remains instantly recognizable when downscaled to 120px browse thumbnails.`
        });
    } else {
        items.push({
            id: 'rec-logo-zone',
            status: 'warn',
            title: 'Scale Down Title Text to Reveal Artwork',
            desc: `The title text occupies ${cv.titleSizePct}% of the frame (dominant coverage). It may obscure key character silhouettes, action focal points, or environmental lighting. Trim outer text padding by 10-15%.`
        });
    }

    // 4. Contrast item
    if (cv.brightnessStd >= 62) {
        items.push({
            id: 'rec-contrast',
            status: 'pass',
            title: 'Dynamic Range & Contrast',
            desc: `The contrast score (${cv.brightnessStd}) matches or exceeds the Mega-Hit average (63.0). Highlights and shadow values are clearly separated.`
        });
    } else {
        items.push({
            id: 'rec-contrast',
            status: 'fail',
            title: 'Low Dynamic Range (Flat Midtones)',
            desc: `The contrast (${cv.brightnessStd}) is below the Mega-Hit benchmark (63.0). Increase the brightness of the key light and deepen background shadows by 15-20%.`
        });
    }

    // 5. Warmth / Saliency item
    if (cv.warmPct >= 45) {
        items.push({
            id: 'rec-palette',
            status: 'pass',
            title: 'Steam UI Saliency',
            desc: `Warm accent colors (${cv.warmPct}%) provide strong chromatic contrast against Steam's dark navy client.`
        });
    } else {
        items.push({
            id: 'rec-palette',
            status: 'warn',
            title: 'Add Warm Accent Lighting',
            desc: `The palette is primarily neutral/cool (${cv.neutralPct}% neutral). Add a warm rim-light, fire ember, or golden title glow to immediately pop on Steam.`
        });
    }

    // 6. Entropy item
    if (cv.entropy >= 6.8) {
        items.push({
            id: 'rec-entropy',
            status: 'pass',
            title: 'Rendering Depth & Texture',
            desc: `High Shannon entropy (${cv.entropy} bits) indicates rich tonal gradients and professional key art rendering.`
        });
    } else {
        items.push({
            id: 'rec-entropy',
            status: 'fail',
            title: 'Soft / Low Information Depth',
            desc: `Entropy is low (${cv.entropy} bits vs 6.99 benchmark). Avoid flat unlit 3D models or washed-out backgrounds. Enhance texture sharpness and ambient lighting.`
        });
    }

    // 7. Composition / Spotlight item
    if (cv.isCenterFocused) {
        items.push({
            id: 'rec-focus',
            status: 'pass',
            title: 'Hero Spotlight Composition',
            desc: `Light is concentrated on the center character (+${cv.spotlightRatio}), framing the focal subject and guiding the viewer's eye.`
        });
    } else {
        items.push({
            id: 'rec-focus',
            status: 'warn',
            title: 'Apply Edge Vignetting',
            desc: `Light is currently scattered around the outer borders. Darken the outer 15% borders with a radial vignette to lock attention on the central hero subject.`
        });
    }

    // 8. Edge Line Density
    if (cv.edgeDensity >= 13.0) {
        items.push({
            id: 'rec-edge',
            status: 'pass',
            title: 'Silhouette & Structural Sharpness',
            desc: `Crisp line definition (${cv.edgeDensity}%) ensures silhouettes remain distinct even when downscaled to small carousel cards.`
        });
    } else {
        items.push({
            id: 'rec-edge',
            status: 'warn',
            title: 'Sharpen Character Silhouettes',
            desc: `Edge density is softer than average (${cv.edgeDensity}% vs 14.2% Mega-Hit avg). Add crisp rim-lighting or sharpen character outlines to separate layers.`
        });
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = `check-item-card item-${item.status}`;
        if (item.id) {
            card.id = item.id;
        }
        card.innerHTML = `
            <div class="item-badge-icon icon-${item.status}">
                ${item.status === 'pass' ? '✓' : item.status === 'warn' ? '!' : '✕'}
            </div>
            <div class="item-text">
                <h4>${item.title}</h4>
                <p>${item.desc}</p>
            </div>
        `;
        container.appendChild(card);
    });
}

/**
 * Generate Customized AI Art Optimization Prompt
 */
function generateAiPrompt(cv, scores, gameName, appid, imgSrc, genreKey = 'all') {
    // 1. Contrast assessment
    let contrastGuidance = "";
    if (cv.brightnessStd < 55) {
        contrastGuidance = `• Deepen cast shadows and push specular highlights on the main hero/subject to increase dynamic contrast std dev from ${cv.brightnessStd} up to the Steam Mega-Hit benchmark of >= 63.0.`;
    } else if (cv.brightnessStd < 63) {
        contrastGuidance = `• Slightly amplify the key light and darken background elements to push dynamic contrast from ${cv.brightnessStd} to >= 63.0.`;
    } else {
        contrastGuidance = `• Maintain the strong lighting contrast (${cv.brightnessStd} std dev), which already exceeds commercial benchmarks.`;
    }

    // 2. Warmth / Saliency assessment
    let warmGuidance = "";
    if (cv.warmPct < 30) {
        warmGuidance = `• Introduce warm accents (e.g. golden/amber rim-lighting, torch flame, magical particle glow) to increase warm pixel share from ${cv.warmPct}% towards ~45% so the capsule pops against Steam's dark navy #171a21 interface.`;
    } else {
        warmGuidance = `• Color temperature is well balanced (${cv.warmPct}% warm color share). Ensure focal elements retain primary chromatic emphasis.`;
    }

    // 3. Title Typography assessment
    let titleGuidance = "";
    if (cv.titleContrast < 4.5) {
        titleGuidance = `• Title text at ${cv.titleZone} currently has low photometric contrast (${cv.titleContrast}:1). Add a subtle dark drop shadow, outer stroke, or backdrop gradient scrim to achieve at least 4.5:1 WCAG AA readability.`;
    } else {
        titleGuidance = `• Title text at ${cv.titleZone} has high readability (${cv.titleContrast}:1 WCAG). Keep font lettering sharp and unhindered by clutter.`;
    }

    // 4. Focal hierarchy / Vignette
    let vignetteGuidance = cv.isCenterFocused
        ? `• Good hero illumination. Keep secondary background elements subdued.`
        : `• Apply a subtle 15% radial edge vignette (darkening borders) to funnel the viewer's gaze toward the center hero character.`;

    // 5. 120px scale readability
    let scaleGuidance = `• Ensure the hero silhouette and title typography remain instantly legible when downscaled to 120px wide (as seen in Steam Discovery Queue). But do not add a thumbnail to the image.`;

    const prompt = `Please optimize this attached steam capsule artwork:

1. Dynamic Contrast & Lighting:
${contrastGuidance}

2. Color Temperature & Steam UI Pop:
${warmGuidance}

3. Title Typography & Readability:
${titleGuidance}

4. Compositional Hierarchy:
${vignetteGuidance}

5. Thumbnail Downscaling (120px Discovery Queue):
${scaleGuidance}

Compliance: Adhere strictly to Steam asset rules (clean title typography only, no review quotes, no discount stickers). Do not add stuff, this needs to be the final capsule art that can be uploaded.`;

    return prompt;
}

let currentAutofixCanvas = null;
let isAutofixAppliedToSim = false;
let currentWebGpuCanvas = null;
let isWebGpuAppliedToSim = false;

/**
 * Update the 3-Box Improve Master Section (AI Chat, 1-Click Autofix, WebGPU Diffusion)
 */
function updateAiPromptCard(cv, scores, gameName, appid, imgSrc, genreKey) {
    const textarea = document.getElementById('aiPromptTextarea');

    if (textarea) {
        const promptText = generateAiPrompt(cv, scores, gameName, appid, imgSrc, genreKey);
        textarea.textContent = promptText;
    }

    // Reset step suggestion highlights for new analysis
    const btnCopy = document.getElementById('btnCopyAiPrompt');
    if (btnCopy) btnCopy.classList.remove('step-suggested');
    const step3 = document.getElementById('aiStep3Group');
    if (step3) {
        step3.classList.remove('visible');
        step3.classList.remove('step-suggested');
    }
    const inlineTargets = document.getElementById('aiChatTargetsInline');
    if (inlineTargets) {
        inlineTargets.style.display = 'none';
    }

    // Update 1-Click Autofix Pane
    updateAutofixPane(cv, scores, gameName, imgSrc);

    // Update WebGPU Hardware Status Pane
    updateWebGpuPane(cv, scores, gameName);
}

/**
 * Generates instant classical computer vision enhancement & updates before/after split slider
 */
function updateAutofixPane(cv, scores, gameName, imgSrc) {
    if (!window.CapsuluAutofix) return;

    function renderWithSource(sourceObj) {
        try {
            const enhancedCanvas = window.CapsuluAutofix.applyCapsuluAutofix(sourceObj);
            currentAutofixCanvas = enhancedCanvas;

            const nativeW = sourceObj.naturalWidth || sourceObj.videoWidth || sourceObj.width || 460;
            const nativeH = sourceObj.naturalHeight || sourceObj.videoHeight || sourceObj.height || 215;

            // Render before canvas
            const canvasBefore = document.getElementById('autofixCanvasBefore');
            if (canvasBefore) {
                canvasBefore.width = nativeW;
                canvasBefore.height = nativeH;
                const ctxB = canvasBefore.getContext('2d');
                ctxB.imageSmoothingEnabled = true;
                ctxB.imageSmoothingQuality = 'high';
                ctxB.clearRect(0, 0, nativeW, nativeH);
                ctxB.drawImage(sourceObj, 0, 0, nativeW, nativeH);
            }

            // Render after canvas
            const canvasAfter = document.getElementById('autofixCanvasAfter');
            if (canvasAfter) {
                canvasAfter.width = nativeW;
                canvasAfter.height = nativeH;
                const ctxA = canvasAfter.getContext('2d');
                ctxA.imageSmoothingEnabled = true;
                ctxA.imageSmoothingQuality = 'high';
                ctxA.clearRect(0, 0, nativeW, nativeH);
                ctxA.drawImage(enhancedCanvas, 0, 0, nativeW, nativeH);
            }

            // Initialize Before / After Slider
            window.CapsuluAutofix.initBeforeAfterSlider('beforeAfterSlider');

            // Reset Sim toggle button state
            isAutofixAppliedToSim = false;
            const testBtnText = document.getElementById('testSimText');
            const testBtnIcon = document.getElementById('testSimIcon');
            if (testBtnText) testBtnText.textContent = 'Test in 3×3 Simulator';
            if (testBtnIcon) testBtnIcon.textContent = '👁️';
        } catch (err) {
            console.warn('Autofix generation error:', err);
        }
    }

    const heroImg = document.getElementById('resultHeroCapsuleImg');
    if (cvCanvas && cvCanvas.width > 0) {
        renderWithSource(cvCanvas);
    } else if (heroImg && heroImg.complete && heroImg.naturalWidth > 0) {
        renderWithSource(heroImg);
    } else if (imgSrc) {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => renderWithSource(img);
        img.src = imgSrc;
    }
}

/**
 * Checks hardware WebGPU capabilities and updates the WebGPU diffusion status panel
 */
async function updateWebGpuPane(cv, scores, gameName) {
    if (!window.CapsuluWebGpu) return;

    const badge = document.getElementById('webgpuBadge');
    const statusText = document.getElementById('webgpuStatusText');
    const deviceLabel = document.getElementById('webgpuDeviceLabel');
    const explainer = document.getElementById('webgpuExplainerText');
    const runText = document.getElementById('runWebGpuText');
    const webgpuProgressCard = document.getElementById('webgpuProgressCard');
    const webgpuResultCard = document.getElementById('webgpuResultCard');

    // Reset studio panels for new analysis
    if (webgpuProgressCard) webgpuProgressCard.style.display = 'none';
    if (webgpuResultCard) webgpuResultCard.style.display = 'none';
    isWebGpuAppliedToSim = false;

    try {
        const gpuStatus = await window.CapsuluWebGpu.getWebGpuDevice();
        const isCached = await window.CapsuluWebGpu.checkModelCached();

        if (runText) {
            runText.textContent = isCached 
                ? 'Run In-Browser WebGPU Diffusion (Model Cached)' 
                : 'Run In-Browser WebGPU Diffusion (~1 GB)';
        }

        if (gpuStatus.supported) {
            if (badge) badge.className = 'webgpu-badge badge-supported';
            if (statusText) statusText.textContent = 'WebGPU Hardware Accelerated';
            if (deviceLabel) deviceLabel.textContent = gpuStatus.info ? `${gpuStatus.info.device || gpuStatus.info.vendor}` : 'Hardware Accelerated Device';
            if (explainer) {
                explainer.textContent = `Your GPU supports direct in-browser tensor computation (SD-Turbo/LCM). Weights are stored in IndexedDB so the ~1 GB download runs only once.`;
            }
        } else {
            if (badge) badge.className = 'webgpu-badge badge-unsupported';
            if (statusText) statusText.textContent = 'WebGPU: Software/Cloud Fallback';
            if (deviceLabel) deviceLabel.textContent = gpuStatus.reason || 'No WebGPU adapter detected';
            if (explainer) {
                explainer.textContent = `WebGPU hardware acceleration is not active in this browser session. You can run software diffusion or copy the neural prompt.`;
            }
        }
    } catch (e) {
        console.warn('WebGPU check error:', e);
    }
}

/**
 * Reliably downloads the currently analyzed capsule artwork directly to the browser Downloads folder
 */
async function downloadCurrentCapsule() {
    const filename = `${(currentLoadedGameName || 'steam_capsule').toLowerCase().replace(/[^a-z0-9]/g, '_')}_capsule.jpg`;
    const btn = document.getElementById('btnDownloadCapsule');
    const btnText = document.getElementById('downloadBtnText');

    if (btnText) btnText.textContent = '1. Downloading...';
    if (btn) btn.classList.add('downloading');

    function resetBtn(success = true) {
        if (btnText) btnText.textContent = success ? '1. Downloaded!' : '1. Download Art';
        setTimeout(() => {
            if (btnText) btnText.textContent = '1. Download Art';
            if (btn) btn.classList.remove('downloading');
        }, 2000);
    }

    function triggerBlob(blob) {
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 3000);
        resetBtn(true);
    }

    // 1. Try to export directly from cvCanvas (crisp render)
    if (cvCanvas && cvCanvas.width > 0) {
        try {
            cvCanvas.toBlob((blob) => {
                if (blob && blob.size > 0) {
                    triggerBlob(blob);
                    return;
                }
                fallbackDownload();
            }, 'image/jpeg', 0.95);
            return;
        } catch (e) {
            console.warn('Canvas export tainted by cross-origin image, using blob fetch:', e);
        }
    }

    fallbackDownload();

    async function fallbackDownload() {
        if (!currentLoadedImgSrc) {
            resetBtn(false);
            return;
        }

        try {
            let fetchUrl = currentLoadedImgSrc;
            if (currentLoadedImgSrc.startsWith('http://') || currentLoadedImgSrc.startsWith('https://')) {
                fetchUrl = `https://images.weserv.nl/?url=${encodeURIComponent(currentLoadedImgSrc)}&output=jpg`;
            }
            const res = await fetch(fetchUrl);
            if (res.ok) {
                const blob = await res.blob();
                triggerBlob(blob);
                return;
            }
        } catch (err) {
            console.warn('Blob fetch failed, falling back to direct anchor:', err);
        }

        // Fallback: direct download link
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = currentLoadedImgSrc;
        a.download = filename;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        resetBtn(true);
    }
}
