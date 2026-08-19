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
 * Visual Check View Switcher (Small / Large)
 */
window.switchSimView = function (mode) {
    const simToggleSmall = document.getElementById('simToggleSmall');
    const simToggleLarge = document.getElementById('simToggleLarge');
    const simViewSmall = document.getElementById('simViewSmall');
    const simViewLarge = document.getElementById('simViewLarge');
    const wrapper = document.getElementById('simAndRecsWrapper');

    if (mode === 'small') {
        if (simToggleSmall) simToggleSmall.classList.add('active');
        if (simToggleLarge) simToggleLarge.classList.remove('active');
        if (simViewSmall) simViewSmall.style.display = 'block';
        if (simViewLarge) simViewLarge.style.display = 'none';
        if (wrapper) {
            wrapper.classList.add('mode-small');
            wrapper.classList.remove('mode-large');
        }
    } else if (mode === 'large') {
        if (simToggleLarge) simToggleLarge.classList.add('active');
        if (simToggleSmall) simToggleSmall.classList.remove('active');
        if (simViewSmall) simViewSmall.style.display = 'none';
        if (simViewLarge) simViewLarge.style.display = 'block';
        if (wrapper) {
            wrapper.classList.add('mode-large');
            wrapper.classList.remove('mode-small');
        }
    }
};

/**
 * Capsulu — Pure Client-Side JavaScript Computer Vision & Scoring Engine
 * Supports Deep Linking (?app=...), 3x3 Large Grid & Seamless 3x3 Micro Matrix (User in Center).
 */

let benchmarksData = null;
const CANVAS_WIDTH = 460;
const CANVAS_HEIGHT = 215;
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
            if (benchmarksData.top_rated || benchmarksData.lowest_rated) {
                renderBenchmarkShowcases(benchmarksData.top_rated || [], benchmarksData.lowest_rated || []);
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
            if (typeof benchmarksData !== 'undefined' && benchmarksData && (benchmarksData.top_rated || benchmarksData.lowest_rated)) {
                renderBenchmarkShowcases(benchmarksData.top_rated || [], benchmarksData.lowest_rated || []);
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

/**
 * Initialize / Render Merged Recent List
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

    if (!items || items.length < 9) {
        items = getDefaultSamples();
        localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(items));
    }

    renderRecentList(items);
}

function saveRecentItem(newItem) {
    try {
        let items = JSON.parse(localStorage.getItem(RECENT_STORAGE_KEY) || '[]');
        if (!items || items.length === 0) items = getDefaultSamples();

        items = items.filter(existing => {
            if (newItem.name && existing.name && existing.name.toLowerCase() === newItem.name.toLowerCase()) return false;
            if (newItem.appid && existing.appid && String(existing.appid) === String(newItem.appid)) return false;
            if (newItem.url && existing.url && existing.url === newItem.url) return false;
            return true;
        });

        items.unshift(newItem);
        items = items.slice(0, 12);

        localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(items));
        renderRecentList(items);
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
                detailsData.genres || []
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
function loadImageWithFallbacks(urls, gameTitle, price, tags, appid, storeUrl, genres = []) {
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
            analyzeAndDisplay(img, currentUrl, gameTitle, price, tags, appid, storeUrl, genres);
            showLoading(false);
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

    showLoading(true);

    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            saveRecentItem({
                name: gameName,
                url: null,
                isUpload: true
            });
            analyzeAndDisplay(img, e.target.result, gameName, null, ["Custom Artwork"], null, null);
            showLoading(false);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function showLoading(show, message = null) {
    loadingBar.style.display = show ? 'block' : 'none';
    if (show) resultsDashboard.style.display = 'none';
}

/**
 * Pure JavaScript Computer Vision Engine
 */
function runComputerVision(img) {
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
 * Isolates letter glyphs (vertical stroke run-lengths >= 10px) and finds the
 * primary horizontal title text baseline band, adhering to Steam graphical asset rules.
 */
function analyzeTitleText(rgbaData, lumArray, w, h) {
    const totalPixels = w * h;

    // 1. Horizontal gradient steps across pixels (detecting letter glyph edges)
    const diffX = new Uint8Array(totalPixels);
    for (let y = 0; y < h; y++) {
        const rowOffset = y * w;
        for (let x = 0; x < w - 1; x++) {
            const idx = rowOffset + x;
            const diff = Math.abs(lumArray[idx + 1] - lumArray[idx]);
            if (diff > 36) diffX[idx] = 1;
        }
    }

    // 2. Vertical stroke run-length filter
    // Letter stems (H, A, D, E, S) have continuous vertical edges spanning >= 10px.
    // Particle noise, flame embers, and film grain span < 8px and are rejected.
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

    // 3. Block-level letter stem density (10x10 blocks)
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

    // 4. Find the dominant horizontal text line band (sliding window of 3 to 6 rows)
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

    // Calculate centroid of the dominant title text band
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

    // Classify Y Axis
    let yKey = 'mid';
    let yLabel = 'Middle';
    if (cy < 0.38) {
        yKey = 'top';
        yLabel = 'Top';
    } else if (cy > 0.62) {
        yKey = 'bot';
        yLabel = 'Bottom';
    }

    // Classify X Axis
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

    // Size classification
    let sizeClass = "medium";
    let sizeLabel = "Optimal (14-28%)";
    if (sizePct > 28) {
        sizeClass = "large";
        sizeLabel = "Dominant (>28%)";
    } else if (sizePct < 14) {
        sizeClass = "small";
        sizeLabel = "Compact (<14%)";
    }

    // Contrast Ratio in Detected Title Text Region
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

function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

/**
 * Score Evaluation Engine (Strict Multi-Flaw Penalty & Full 0-100 Dynamic Range)
 */
function evaluateScores(cv) {
    // 1. Dynamic Contrast (Mega-Hit Benchmark: 63.0)
    let contrastScore = 100;
    if (cv.brightnessStd >= 63.0) {
        contrastScore = Math.min(100, 95 + (cv.brightnessStd - 63.0) * 0.8);
    } else {
        contrastScore = Math.max(0, 100 - (63.0 - cv.brightnessStd) * 3.5);
    }

    // 2. Warmth / Saliency (Mega-Hit Benchmark: 45.0%)
    let warmthScore = 100;
    if (cv.warmPct >= 45.0) {
        warmthScore = Math.min(100, 95 + (cv.warmPct - 45.0) * 0.2);
    } else {
        warmthScore = Math.max(0, 100 - (45.0 - cv.warmPct) * 2.0);
    }

    // 3. Shannon Entropy (Mega-Hit Benchmark: 6.90 bits)
    let entropyScore = 100;
    if (cv.entropy >= 6.90) {
        entropyScore = 98;
    } else {
        entropyScore = Math.max(0, 100 - (6.90 - cv.entropy) * 50.0);
    }

    // 4. Edge Density (Mega-Hit Benchmark: 13.5%)
    let edgeScore = 100;
    if (cv.edgeDensity >= 13.5) {
        edgeScore = 95;
    } else {
        edgeScore = Math.max(0, 100 - (13.5 - cv.edgeDensity) * 8.0);
    }

    // 5. Hero Spotlight / Composition
    let focusScore = 45;
    if (cv.isCenterFocused) {
        focusScore = cv.spotlightRatio > 10.0 ? 98 : 85;
    }

    // 6. Title Typography Contrast (Benchmark: 4.5:1, Floor: 1.2:1)
    let textScore = 90;
    if (cv.titleContrast >= 4.5) {
        textScore = Math.min(100, Math.round(92 + (cv.titleContrast - 4.5) * 2.0));
    } else if (cv.titleContrast >= 3.0) {
        textScore = Math.round(60 + ((cv.titleContrast - 3.0) / 1.5) * 25.0);
    } else {
        textScore = Math.max(0, Math.round(cv.titleContrast * 18.0));
    }

    const subScores = [contrastScore, warmthScore, entropyScore, edgeScore, focusScore, textScore];
    const baseScore = (
        contrastScore * 0.25 +
        warmthScore * 0.15 +
        entropyScore * 0.15 +
        edgeScore * 0.15 +
        focusScore * 0.15 +
        textScore * 0.15
    );

    // Strict Flaw Penalty:
    // Any section below benchmark (< 60 for warmth/contrast, or < 75 for other critical metrics)
    const isContrastFlaw = cv.brightnessStd < 58.0;
    const isWarmthFlaw = cv.warmPct < 35.0;
    const isEntropyFlaw = cv.entropy < 6.2;
    const isEdgeFlaw = cv.edgeDensity < 8.0;
    const isFocusFlaw = !cv.isCenterFocused;
    const isTextFlaw = cv.titleContrast < 3.0;

    const flawCount = [isContrastFlaw, isWarmthFlaw, isEntropyFlaw, isEdgeFlaw, isFocusFlaw, isTextFlaw].filter(Boolean).length;
    const minSub = Math.min(...subScores);
    
    let flawPenalty = 0;
    if (flawCount > 0) {
        flawPenalty = flawCount * 13.0 + Math.max(0, (40 - minSub) * 0.8);
    }

    const overallScore = Math.max(0, Math.min(100, Math.round(baseScore - flawPenalty)));

    let tierName = "🏆 Mega-Hit Grade";
    let tierBadgeClass = "badge-gold";
    let percentile = "Top 10% of Steam Capsules";
    let headline = "Exceptional";
    let summary = "Your capsule features punchy contrast, crisp silhouettes, and vibrant accents that stand out against Steam's dark store interface.";

    if (overallScore >= 88) {
        tierName = "🏆 Mega-Hit Grade";
        tierBadgeClass = "badge-gold";
        percentile = "Top 10% of Steam Capsules";
        headline = "Exceptional";
        summary = "Your capsule features punchy contrast, crisp silhouettes, and vibrant accents that stand out against Steam's dark store interface.";
    } else if (overallScore >= 72) {
        tierName = "🌟 Solid Indie Grade";
        tierBadgeClass = "badge-green";
        percentile = "Top 35% of Steam Capsules";
        headline = "Strong";
        summary = "Well-balanced capsule with solid contrast and focal hierarchy. Minor tweaks to highlight contrast can push it to top-tier.";
    } else if (overallScore >= 50) {
        tierName = "📊 Moderate Visibility";
        tierBadgeClass = "badge-blue";
        percentile = "Median 50% Distribution";
        headline = "Average";
        summary = "Readable, but risks blending into the browse queue due to neutral color temperatures or softer midtone contrast.";
    } else if (overallScore >= 30) {
        tierName = "📉 Struggling Grade";
        tierBadgeClass = "badge-orange";
        percentile = "Bottom 30% of Steam Capsules";
        headline = "Low";
        summary = "Artwork is too flat or dark. When scaled down to small browse cards, character details and title text will blur together.";
    } else {
        tierName = "🕳️ Near-Zero Flop Risk";
        tierBadgeClass = "badge-red";
        percentile = "Bottom 15% of Steam Capsules";
        headline = "Critical";
        summary = "Your capsule lacks dynamic highlights, deep shadows, or color punch. Highly recommended to re-render with higher contrast lighting.";
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

function round(val, dec) {
    return Number(val.toFixed(dec));
}

/**

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
        tip: `Ensure high contrast and distinct hero readability tailored for "${categoryKey}" audiences.`,
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
 * Update Dedicated Genre/Tag Benchmark Intelligence Card
 */
function updateGenreBenchmarkDisplay(cv, genreKey) {
    const card = document.getElementById('genreBenchmarkCard');
    if (!card) return;

    const iconElem = document.getElementById('genreCardIcon');
    const titleElem = document.getElementById('genreCardTitle');
    const subtitleElem = document.getElementById('genreCardSubtitle');
    const matchBadge = document.getElementById('genreMatchBadge');
    const medContrastElem = document.getElementById('genreMedContrast');
    const deltaContrastElem = document.getElementById('genreDeltaContrast');
    const warmShareElem = document.getElementById('genreWarmShare');
    const deltaWarmElem = document.getElementById('genreDeltaWarm');
    const entropyElem = document.getElementById('genreEntropy');
    const deltaEntropyElem = document.getElementById('genreDeltaEntropy');
    const edgeElem = document.getElementById('genreEdgeDensity');
    const deltaEdgeElem = document.getElementById('genreDeltaEdge');
    const recElem = document.getElementById('genreRecommendationText');

    if (!genreKey || genreKey === 'all') {
        if (iconElem) iconElem.textContent = "🌐";
        if (titleElem) titleElem.textContent = "All Steam Games Market Benchmark";
        if (subtitleElem) subtitleElem.textContent = "Empirical baseline derived from 28,754 verified Steam games";
        if (matchBadge) matchBadge.textContent = "All Games Active";

        const allContrast = 58.4;
        const diffContrast = round(cv.brightnessStd - allContrast, 1);
        if (medContrastElem) medContrastElem.textContent = `${allContrast} std dev`;
        if (deltaContrastElem) {
            deltaContrastElem.textContent = `Your: ${cv.brightnessStd} (${diffContrast >= 0 ? '+' : ''}${diffContrast} vs median)`;
            deltaContrastElem.className = `genre-stat-delta ${diffContrast >= 0 ? 'delta-pos' : 'delta-neg'}`;
        }

        const allWarm = 42.8;
        const diffWarm = round(cv.warmPct - allWarm, 1);
        if (warmShareElem) warmShareElem.textContent = `${allWarm}% Warm`;
        if (deltaWarmElem) {
            deltaWarmElem.textContent = `Your: ${cv.warmPct}% (${diffWarm >= 0 ? '+' : ''}${diffWarm}% vs all)`;
            deltaWarmElem.className = `genre-stat-delta ${diffWarm >= 0 ? 'delta-pos' : 'delta-neutral'}`;
        }

        const allEntropy = 6.72;
        const diffEntropy = round(cv.entropy - allEntropy, 2);
        if (entropyElem) entropyElem.textContent = `${allEntropy} bits`;
        if (deltaEntropyElem) {
            deltaEntropyElem.textContent = `Your: ${cv.entropy} (${diffEntropy >= 0 ? '+' : ''}${diffEntropy} bits)`;
            deltaEntropyElem.className = `genre-stat-delta ${diffEntropy >= 0 ? 'delta-pos' : 'delta-neg'}`;
        }

        const allEdge = 13.1;
        const diffEdge = round(cv.edgeDensity - allEdge, 1);
        if (edgeElem) edgeElem.textContent = `${allEdge}% Edge`;
        if (deltaEdgeElem) {
            deltaEdgeElem.textContent = `Your: ${cv.edgeDensity}% (${diffEdge >= 0 ? '+' : ''}${diffEdge}%)`;
            deltaEdgeElem.className = `genre-stat-delta ${diffEdge >= 0 ? 'delta-pos' : 'delta-neg'}`;
        }

        const allTextContrast = 3.5;
        const diffTextContrast = round(cv.titleContrast - allTextContrast, 1);
        const textContrastElem = document.getElementById('genreTextContrast');
        const deltaTextContrastElem = document.getElementById('genreDeltaTextContrast');
        if (textContrastElem) textContrastElem.textContent = `${allTextContrast}:1 WCAG`;
        if (deltaTextContrastElem) {
            deltaTextContrastElem.textContent = `Your: ${cv.titleContrast}:1 (${diffTextContrast >= 0 ? '+' : ''}${diffTextContrast})`;
            deltaTextContrastElem.className = `genre-stat-delta ${diffTextContrast >= 0 ? 'delta-pos' : 'delta-neg'}`;
        }

        const textZoneElem = document.getElementById('genreTextZone');
        const deltaTextZoneElem = document.getElementById('genreDeltaTextZone');
        if (textZoneElem) textZoneElem.textContent = "Middle Center";
        if (deltaTextZoneElem) {
            deltaTextZoneElem.textContent = `Your: ${cv.titleZone} (${cv.titleSizePct}% Area)`;
            deltaTextZoneElem.className = `genre-stat-delta delta-pos`;
        }

        if (recElem) recElem.innerHTML = `<strong>Global Steam Benchmark:</strong> High-converting capsules maintain contrast std dev > 63.0, sharp title contrast > 4.5:1, and strong center focal hierarchy across all categories.`;
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
    if (titleElem) titleElem.textContent = `${icon} ${gData.name || genreKey} Benchmark`;
    if (subtitleElem) subtitleElem.textContent = `Empirical baseline derived from ${gData.count.toLocaleString()} verified Steam games with "${genreKey}" ${gData.categoryType || 'Tag'}`;
    if (matchBadge) matchBadge.textContent = `${genreKey} Active`;

    // 1. Contrast
    const catContrast = gData.contrast.median;
    const diffContrast = round(cv.brightnessStd - catContrast, 1);
    if (medContrastElem) medContrastElem.textContent = `${catContrast} std dev`;
    if (deltaContrastElem) {
        deltaContrastElem.textContent = `Your: ${cv.brightnessStd} (${diffContrast >= 0 ? '+' : ''}${diffContrast} vs median)`;
        deltaContrastElem.className = `genre-stat-delta ${diffContrast >= 0 ? 'delta-pos' : 'delta-neg'}`;
    }

    // 2. Warmth
    const catWarm = gData.warm_palette_pct;
    const diffWarm = round(cv.warmPct - catWarm, 1);
    if (warmShareElem) warmShareElem.textContent = `${catWarm}% Warm`;
    if (deltaWarmElem) {
        deltaWarmElem.textContent = `Your: ${cv.warmPct}% (${diffWarm >= 0 ? '+' : ''}${diffWarm}% vs market)`;
        deltaWarmElem.className = `genre-stat-delta ${diffWarm >= 0 ? 'delta-pos' : 'delta-neutral'}`;
    }

    // 3. Entropy
    const catEntropy = gData.entropy.median;
    const diffEntropy = round(cv.entropy - catEntropy, 2);
    if (entropyElem) entropyElem.textContent = `${catEntropy} bits`;
    if (deltaEntropyElem) {
        deltaEntropyElem.textContent = `Your: ${cv.entropy} (${diffEntropy >= 0 ? '+' : ''}${diffEntropy} bits)`;
        deltaEntropyElem.className = `genre-stat-delta ${diffEntropy >= 0 ? 'delta-pos' : 'delta-neg'}`;
    }

    // 4. Edge Density
    const catEdge = gData.edge_density.median;
    const diffEdge = round(cv.edgeDensity - catEdge, 1);
    if (edgeElem) edgeElem.textContent = `${catEdge}% Edge`;
    if (deltaEdgeElem) {
        deltaEdgeElem.textContent = `Your: ${cv.edgeDensity}% (${diffEdge >= 0 ? '+' : ''}${diffEdge}%)`;
        deltaEdgeElem.className = `genre-stat-delta ${diffEdge >= 0 ? 'delta-pos' : 'delta-neg'}`;
    }

    // 5. Title Contrast
    const catTextContrast = (gData.text && gData.text.contrast && gData.text.contrast.median) || 3.5;
    const diffTextContrast = round(cv.titleContrast - catTextContrast, 1);
    const textContrastElem = document.getElementById('genreTextContrast');
    const deltaTextContrastElem = document.getElementById('genreDeltaTextContrast');
    if (textContrastElem) textContrastElem.textContent = `${catTextContrast}:1 WCAG`;
    if (deltaTextContrastElem) {
        deltaTextContrastElem.textContent = `Your: ${cv.titleContrast}:1 (${diffTextContrast >= 0 ? '+' : ''}${diffTextContrast})`;
        deltaTextContrastElem.className = `genre-stat-delta ${diffTextContrast >= 0 ? 'delta-pos' : 'delta-neg'}`;
    }

    // 6. Dominant Placement Zone
    const catTextZone = formatZoneName((gData.text && gData.text.top_zone) || 'mid_center');
    const textZoneElem = document.getElementById('genreTextZone');
    const deltaTextZoneElem = document.getElementById('genreDeltaTextZone');
    if (textZoneElem) textZoneElem.textContent = catTextZone;
    if (deltaTextZoneElem) {
        const isMatch = cv.titleZone.toLowerCase() === catTextZone.toLowerCase();
        deltaTextZoneElem.textContent = `Your: ${cv.titleZone} ${isMatch ? '(Matches)' : ''}`;
        deltaTextZoneElem.className = `genre-stat-delta ${isMatch ? 'delta-pos' : 'delta-neutral'}`;
    }

    // Tailored Recommendation Tip
    if (recElem) recElem.innerHTML = `<strong>Tailored "${genreKey}" Advice:</strong> ${gData.tip}`;

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

/**
 * Render 5x5 Top 25 Highest Rated and Lowest 25 Flop Capsules
 */
function renderBenchmarkShowcases(topRated, lowestRated) {
    const topGrid = document.getElementById('topRatedGrid');
    const lowGrid = document.getElementById('lowestRatedGrid');

    if (topGrid && topRated && topRated.length > 0) {
        topGrid.innerHTML = topRated.map((game, idx) => createBenchmarkCard(game, idx, 'top')).join('');
    }

    if (lowGrid && lowestRated && lowestRated.length > 0) {
        lowGrid.innerHTML = lowestRated.map((game, idx) => createBenchmarkCard(game, idx, 'flop')).join('');
    }

    // Attach click listeners to cards to open in Capsulu Simulator / Analyzer
    document.querySelectorAll('.benchmark-capsule-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('.card-ext-link')) return; // Allow direct store link click
            const appid = card.getAttribute('data-appid');
            const img = card.getAttribute('data-img');
            const name = card.getAttribute('data-name');
            openSimulatorGame(appid, img, name, false);
        });
    });
}

function createBenchmarkCard(game, index, type) {
    const isTop = type === 'top';
    
    return `
        <div class="benchmark-capsule-card ${isTop ? 'card-top' : 'card-flop'}" data-appid="${game.appid}" data-img="${game.imageUrl}" data-name="${encodeURIComponent(game.name)}" title="Click to analyze ${game.name} in Capsulu">
            <div class="card-img-container">
                <img src="${game.imageUrl}" alt="${game.name}" loading="lazy" class="card-capsule-img" onerror="this.onerror=null; this.src='https://cdn.akamai.steamstatic.com/steam/apps/${game.appid}/capsule_616x353.jpg';">
                <div class="card-hover-overlay">
                    <span class="card-analyze-btn">⚡ Analyze in Capsulu</span>
                </div>
            </div>
            <div class="card-body">
                <div class="card-title-row">
                    <h5 class="card-game-title">${game.name}</h5>
                </div>
                <div class="card-meta-row">
                    <span class="card-rank ${isTop ? 'rank-gold' : 'rank-red'}">#${index + 1}</span>
                    <span class="card-metric-tag ${game.palette_type === 'warm' ? 'tag-warm' : 'tag-neutral'}" title="Color Temperature">${game.palette_type}</span>
                    <span class="card-metric-tag" title="Total Steam Reviews">${Number(game.reviews).toLocaleString()} ${game.reviews === 1 ? 'review' : 'reviews'}</span>
                </div>
            </div>
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
        { name: userGameName || "Your Game", imageUrl: userImgSrc, isUser: true, appid: appid }, // Center (Row 2, Col 2)
        others[4] || fallbackGame,
        others[5] || fallbackGame,
        others[6] || fallbackGame,
        others[7] || fallbackGame
    ];

    // 1. Large Browse 3x3 Grid (9 Entries)
    const largeGrid = document.getElementById('largeSimRow');
    if (largeGrid) {
        largeGrid.innerHTML = items9.map(g => `
            <div class="sim-capsule-item ${g.isUser ? 'user-capsule-item' : 'clickable-sim-item'}" 
                 data-appid="${g.appid || ''}" 
                 data-image-url="${g.imageUrl || ''}" 
                 data-name="${g.name || ''}" 
                 data-is-user="${g.isUser ? 'true' : 'false'}"
                 title="${g.isUser ? 'Your Game (Current Analysis)' : `Click to analyze ${g.name}`}"
                 tabindex="${g.isUser ? '-1' : '0'}"
                 role="${g.isUser ? 'img' : 'button'}">
                <div class="sim-capsule-thumb">
                    <img src="${g.imageUrl}" alt="${g.name}" loading="lazy" onerror="this.onerror=null; this.src='https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg';">
                </div>
            </div>
        `).join('');
    }

    // 2. Seamless 120px Discovery Queue 3x3 Matrix (9 Entries, gapless, borderless)
    const microMatrix = document.getElementById('microSimQueue');
    if (microMatrix) {
        microMatrix.innerHTML = items9.map(g => `
            <div class="micro-matrix-item ${g.isUser ? 'user-micro-item' : 'clickable-sim-item'}" 
                 data-appid="${g.appid || ''}" 
                 data-image-url="${g.imageUrl || ''}" 
                 data-name="${g.name || ''}" 
                 data-is-user="${g.isUser ? 'true' : 'false'}"
                 title="${g.isUser ? 'Your Game (Current Analysis)' : `Click to analyze ${g.name}`}"
                 tabindex="${g.isUser ? '-1' : '0'}"
                 role="${g.isUser ? 'img' : 'button'}">
                <img src="${g.imageUrl}" alt="${g.name}" loading="lazy" onerror="this.onerror=null; this.src='https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg';">
            </div>
        `).join('');
    }
}

/**
 * Main Analysis and Dashboard Update
 */
function analyzeAndDisplay(img, imgSrc, gameName, price, tags, appid, storeUrl, genres = []) {
    const cv = runComputerVision(img);
    const scores = evaluateScores(cv);

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
    const storeBtnLink = document.getElementById('resultStoreBtnLink');
    const appIdTag = document.getElementById('resultAppIdTag');
    const priceTag = document.getElementById('resultPriceTag');
    const heroTagsContainer = document.getElementById('resultHeroTags');

    const effectiveStoreUrl = storeUrl || (appid ? `https://store.steampowered.com/app/${appid}/` : null);

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

    // 3. Update Dedicated Genre Benchmark Intelligence Card
    updateGenreBenchmarkDisplay(cv, currentGenreLens);

    // 4. Render Contextual Simulator Lineups
    renderSimulatorLineups(imgSrc, gameName || "Your Game", appid, currentGenreLens);

    // 5. Update Top Score Banner
    document.getElementById('overallScoreNum').textContent = scores.overallScore;

    const gaugeFill = document.getElementById('gaugeFill');
    const offset = 440 - (440 * scores.overallScore / 100);
    gaugeFill.style.strokeDashoffset = offset;
    gaugeFill.style.stroke = scores.overallScore >= 80 ? 'var(--green-pass)' : scores.overallScore >= 65 ? 'var(--gold)' : 'var(--red)';

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
    updateMetricRow('mContrastScore', 'mContrastBar', 'mContrastVal', scores.contrastScore, `Your: ${cv.brightnessStd} std dev`, (cv.brightnessStd / 85) * 100);
    updateMetricRow('mWarmthScore', 'mWarmthBar', 'mWarmthVal', scores.warmthScore, `Your: ${cv.warmPct}% Warm`, Math.min(100, cv.warmPct * 1.5));
    updateMetricRow('mEntropyScore', 'mEntropyBar', 'mEntropyVal', scores.entropyScore, `Your: ${cv.entropy} bits`, (cv.entropy / 7.5) * 100);
    updateMetricRow('mEdgeScore', 'mEdgeBar', 'mEdgeVal', scores.edgeScore, `Your: ${cv.edgeDensity}% Edge`, (cv.edgeDensity / 22) * 100);
    updateMetricRow('mFocusScore', 'mFocusBar', 'mFocusVal', scores.focusScore, cv.isCenterFocused ? `Center Focused (+${cv.spotlightRatio})` : 'Border-Heavy', cv.isCenterFocused ? 85 : 45);
    updateMetricRow('mTextScore', 'mTextBar', 'mTextVal', scores.textScore, `Your: ${cv.titleContrast}:1 (${cv.titleReadabilityLabel})`, Math.min(100, (cv.titleContrast / 10) * 100));

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
            desc: `Your title typography achieves a strong ${cv.titleContrast}:1 contrast ratio against the backdrop (WCAG AA standard). It will remain sharp on small mobile screens and browse carousels.`
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
            desc: `Your title contrast (${cv.titleContrast}:1) is very low. The title text blends directly into the artwork and may be unreadable at 120px browse resolutions. Add a dark scrim, heavy drop shadow, or highlight stroke.`
        });
    }

    // 3. Title Placement & Scale Coverage
    if (cv.titleSizePct >= 14 && cv.titleSizePct <= 28) {
        items.push({
            id: 'rec-logo-zone',
            status: 'pass',
            title: 'Title Placement & Sizing',
            desc: `Your title text occupies ${cv.titleSizePct}% of the capsule in the ${cv.titleZone} zone, hitting the optimal commercial balance between title readability and hero art visibility.`
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
            desc: `Title text occupies ${cv.titleSizePct}% of the frame (dominant coverage). It may obscure key character silhouettes, action focal points, or environmental lighting. Trim outer text padding by 10-15%.`
        });
    }

    // 4. Contrast item
    if (cv.brightnessStd >= 62) {
        items.push({
            id: 'rec-contrast',
            status: 'pass',
            title: 'Dynamic Range & Contrast',
            desc: `Your contrast score (${cv.brightnessStd}) matches or exceeds the Mega-Hit average (63.0). Highlights and shadow values are clearly separated.`
        });
    } else {
        items.push({
            id: 'rec-contrast',
            status: 'fail',
            title: 'Low Dynamic Range (Flat Midtones)',
            desc: `Your contrast (${cv.brightnessStd}) is below the Mega-Hit benchmark (63.0). Increase the brightness of your key light and deepen background shadows by 15-20%.`
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
            desc: `Your palette is primarily neutral/cool (${cv.neutralPct}% neutral). Add a warm rim-light, fire ember, or golden title glow to immediately pop on Steam.`
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
            desc: `Light is currently scattered around the outer borders. Darken the outer 15% borders with a radial vignette to lock attention on your central hero.`
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

/**
 * Update the AI Art Fix Prompt Card
 */
function updateAiPromptCard(cv, scores, gameName, appid, imgSrc, genreKey) {
    const card = document.getElementById('aiPromptCard');
    const textarea = document.getElementById('aiPromptTextarea');
    if (!card || !textarea) return;

    const promptText = generateAiPrompt(cv, scores, gameName, appid, imgSrc, genreKey);
    textarea.textContent = promptText;

    // Reset step suggestion highlights for new analysis
    const btnCopy = document.getElementById('btnCopyAiPrompt');
    if (btnCopy) btnCopy.classList.remove('step-suggested');
    const step3 = document.getElementById('aiStep3Group');
    if (step3) {
        step3.classList.remove('visible');
        step3.classList.remove('step-suggested');
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
