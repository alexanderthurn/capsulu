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
            .on('mouseenter', function(event, d) {
                d3.select(this).transition().duration(150).attr('d', arcHover);
                if (centerLabel) centerLabel.textContent = d.data.pct + "%";
                
                // Highlight matching swatch
                const swatches = document.querySelectorAll('.palette-dedicated-panel .swatch-item');
                if (swatches[d.index]) swatches[d.index].classList.add('highlighted');
            })
            .on('mouseleave', function(event, d) {
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
window.switchSimView = function(mode) {
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
});

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
        const res = await fetch('benchmarks.json');
        if (res.ok) {
            benchmarksData = await res.json();
            if (benchmarksData.overall && benchmarksData.overall.total_games_analyzed) {
                if (benchmarkCountBadge) {
                    benchmarkCountBadge.textContent = `${benchmarksData.overall.total_games_analyzed.toLocaleString()} Games Analyzed`;
                }
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
    const homeView = document.getElementById('homeView');
    const benchmarkView = document.getElementById('benchmarkView');
    const brandHomeLink = document.getElementById('brandHomeLink');

    if (brandHomeLink) {
        brandHomeLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (navHomeBtn && navBenchmarkBtn) {
                navHomeBtn.classList.add('active');
                navBenchmarkBtn.classList.remove('active');
                homeView.style.display = 'block';
                benchmarkView.style.display = 'none';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }

    if (navHomeBtn && navBenchmarkBtn) {
        navHomeBtn.addEventListener('click', () => {
            navHomeBtn.classList.add('active');
            navBenchmarkBtn.classList.remove('active');
            homeView.style.display = 'block';
            benchmarkView.style.display = 'none';
        });

        navBenchmarkBtn.addEventListener('click', () => {
            navBenchmarkBtn.classList.add('active');
            navHomeBtn.classList.remove('active');
            homeView.style.display = 'none';
            benchmarkView.style.display = 'block';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    window.addEventListener('popstate', () => {
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

    // Genre Comparison Lens Switcher Listeners
    document.querySelectorAll('.genre-pill-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const selectedGenre = btn.getAttribute('data-genre') || 'all';
            switchGenreLens(selectedGenre);
        });
    });

    // Synchronized Genre Dropdowns Listeners across all panels
    document.querySelectorAll('.genre-sync-dropdown').forEach(dropdown => {
        dropdown.addEventListener('change', (e) => {
            const val = e.target.value;
            if (val === 'auto') {
                const autoGenre = detectGenreFromTags(currentLoadedTags) || 'all';
                switchGenreLens(autoGenre);
            } else {
                switchGenreLens(val);
            }
        });
    });


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

            saveRecentItem({
                name: finalName,
                appid: appid,
                url: storeUrl,
                imageUrl: detailsData.header_image,
                price: displayPrice,
                tags: detailsData.genres
            });

            loadImageWithFallbacks(
                [
                    `https://images.weserv.nl/?url=${encodeURIComponent(detailsData.header_image)}`,
                    `https://wsrv.nl/?url=${encodeURIComponent(detailsData.header_image)}`,
                    detailsData.header_image
                ],
                finalName,
                displayPrice,
                detailsData.genres,
                appid,
                storeUrl
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

        loadImageWithFallbacks(candidates, gameTitle, null, null, appid, storeUrl);
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
        loadImageWithFallbacks([rawInput, `https://images.weserv.nl/?url=${encodeURIComponent(rawInput)}`], gameTitle, null, null, null, rawInput);
    } else {
        alert('Unrecognized format. Please paste a full Steam store URL (e.g. store.steampowered.com/app/4429000), an App ID, or an image URL.');
    }
}

/**
 * Sequential Candidate Loader
 */
function loadImageWithFallbacks(urls, gameTitle, price, tags, appid, storeUrl) {
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
            analyzeAndDisplay(img, currentUrl, gameTitle, price, tags, appid, storeUrl);
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

function showLoading(show) {
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
                -2 * lumArray[y * w + (x - 1)]       + 2 * lumArray[y * w + (x + 1)] +
                -1 * lumArray[(y + 1) * w + (x - 1)] + 1 * lumArray[(y + 1) * w + (x + 1)];

            const gy = 
                -1 * lumArray[(y - 1) * w + (x - 1)] + -2 * lumArray[(y - 1) * w + x] + -1 * lumArray[(y - 1) * w + (x + 1)] +
                 1 * lumArray[(y + 1) * w + (x - 1)] +  2 * lumArray[(y + 1) * w + x] +  1 * lumArray[(y + 1) * w + (x + 1)];

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
        dominantColors: dominantColors
    };
}

function extractDominantColors(samples) {
    if (!samples.length) return [];
    
    const buckets = {};
    samples.forEach(([r, g, b]) => {
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

function round(val, dec) {
    return Number(val.toFixed(dec));
}

/**
 * Score Evaluation Engine
 */
function evaluateScores(cv) {
    let contrastScore = 100;
    if (cv.brightnessStd < 63) {
        contrastScore = Math.max(30, 100 - (63 - cv.brightnessStd) * 6);
    } else {
        contrastScore = Math.min(100, 95 + (cv.brightnessStd - 63) * 1);
    }

    let warmthScore = 100;
    if (cv.warmPct < 45) {
        warmthScore = Math.max(35, 100 - (45 - cv.warmPct) * 2.5);
    } else {
        warmthScore = 96;
    }

    let entropyScore = 100;
    if (cv.entropy < 6.90) {
        entropyScore = Math.max(30, 100 - (6.90 - cv.entropy) * 75);
    } else {
        entropyScore = 98;
    }

    let edgeScore = 100;
    if (cv.edgeDensity < 13.5) {
        edgeScore = Math.max(35, 100 - (13.5 - cv.edgeDensity) * 12);
    } else {
        edgeScore = 95;
    }

    let focusScore = cv.isCenterFocused ? 92 : 60;
    if (cv.spotlightRatio > 10) focusScore = 98;

    const overallScore = Math.round(
        contrastScore * 0.30 +
        warmthScore * 0.20 +
        entropyScore * 0.20 +
        edgeScore * 0.15 +
        focusScore * 0.15
    );

    let tierName = "🏆 Mega-Hit Grade";
    let tierBadgeClass = "badge-gold";
    let percentile = "Top 10% of Steam Capsules";
    let headline = "High-Converting Store Art";
    let summary = "Your capsule features punchy contrast, crisp silhouettes, and vibrant accents that stand out against Steam's dark store interface.";

    if (overallScore >= 88) {
        tierName = "🏆 Mega-Hit Grade";
        tierBadgeClass = "badge-gold";
        percentile = "Top 10% of Steam Capsules";
        headline = "Exceptional, High-Converting Key Art";
    } else if (overallScore >= 75) {
        tierName = "🌟 Solid Indie Grade";
        tierBadgeClass = "badge-green";
        percentile = "Top 35% of Steam Capsules";
        headline = "Strong Visual Foundation";
        summary = "Well-balanced capsule with solid contrast and focal hierarchy. Minor tweaks to highlight contrast can push it to top-tier.";
    } else if (overallScore >= 60) {
        tierName = "📊 Moderate Visibility";
        tierBadgeClass = "badge-blue";
        percentile = "Median 50% Distribution";
        headline = "Average Store Visibility";
        summary = "Readable, but risks blending into the browse queue due to neutral color temperatures or softer midtone contrast.";
    } else if (overallScore >= 48) {
        tierName = "📉 Struggling Grade";
        tierBadgeClass = "badge-orange";
        percentile = "Bottom 30% of Steam Capsules";
        headline = "Low Store Contrast Risk";
        summary = "Artwork is too flat or dark. When scaled down to small browse cards, character details and title text will blur together.";
    } else {
        tierName = "🕳️ Near-Zero Flop Risk";
        tierBadgeClass = "badge-red";
        percentile = "Bottom 15% of Steam Capsules";
        headline = "Critical Contrast & Clarity Issues";
        summary = "Your capsule lacks dynamic highlights, deep shadows, and color punch. Highly recommended to re-render with higher contrast lighting.";
    }

    return {
        overallScore,
        contrastScore: Math.round(contrastScore),
        warmthScore: Math.round(warmthScore),
        entropyScore: Math.round(entropyScore),
        edgeScore: Math.round(edgeScore),
        focusScore: Math.round(focusScore),
        tierName,
        tierBadgeClass,
        percentile,
        headline,
        summary
    };
}

/**
 * Genre Detection Helper
 */
function detectGenreFromTags(tags) {
    if (!tags || tags.length === 0) return null;
    const tagStr = tags.join(" ").toLowerCase();

    if (tagStr.includes("action") || tagStr.includes("shooter") || tagStr.includes("hack and slash") || tagStr.includes("fps") || tagStr.includes("fighting")) {
        return "Action";
    }
    if (tagStr.includes("rpg") || tagStr.includes("role-playing") || tagStr.includes("souls-like") || tagStr.includes("dark fantasy")) {
        return "RPG";
    }
    if (tagStr.includes("strategy") || tagStr.includes("tactics") || tagStr.includes("deckbuilder") || tagStr.includes("rts") || tagStr.includes("turn-based")) {
        return "Strategy";
    }
    if (tagStr.includes("adventure") || tagStr.includes("metroidvania") || tagStr.includes("exploration") || tagStr.includes("platformer")) {
        return "Adventure";
    }
    if (tagStr.includes("simulation") || tagStr.includes("management") || tagStr.includes("sandbox") || tagStr.includes("building") || tagStr.includes("farming")) {
        return "Simulation";
    }
    if (tagStr.includes("casual") || tagStr.includes("puzzle") || tagStr.includes("cozy") || tagStr.includes("party")) {
        return "Casual";
    }
    if (tagStr.includes("indie")) {
        return "Indie";
    }
    return null;
}

/**
 * Switch Active Benchmark Comparison Lens (All Steam Games vs Genre Specific)
 */
function switchGenreLens(genreKey) {
    currentGenreLens = genreKey || 'all';

    // Update pill buttons active state
    document.querySelectorAll('.genre-pill-btn').forEach(btn => {
        const g = btn.getAttribute('data-genre') || 'all';
        if (g.toLowerCase() === currentGenreLens.toLowerCase()) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update all dropdowns across panels
    document.querySelectorAll('.genre-sync-dropdown').forEach(dropdown => {
        dropdown.value = currentGenreLens === 'all' ? 'all' : currentGenreLens;
    });

    if (typeof currentCvResult !== 'undefined' && currentCvResult) {
        updateGenreBenchmarkDisplay(currentCvResult, currentGenreLens);
        renderSimulatorLineups(currentLoadedImgSrc, currentLoadedGameName, currentLoadedAppId, currentGenreLens);
        generateChecklist(currentCvResult, currentScores, currentGenreLens);
    }
}

/**
 * Update Dedicated Genre Benchmark Intelligence Card
 */
function updateGenreBenchmarkDisplay(cv, genreKey) {
    const card = document.getElementById('genreBenchmarkCard');
    if (!card) return;

    let targetGenre = genreKey;
    if (!targetGenre || targetGenre === 'all') {
        targetGenre = detectGenreFromTags(currentLoadedTags) || 'Action';
    }

    if (typeof benchmarksData === 'undefined' || !benchmarksData.genres || !benchmarksData.genres[targetGenre]) {
        card.style.display = 'none';
        return;
    }

    const gData = benchmarksData.genres[targetGenre];
    const genreIcons = {
        "Action": "⚔️",
        "RPG": "🛡️",
        "Strategy": "♟️",
        "Adventure": "🗺️",
        "Simulation": "🚜",
        "Casual": "☕",
        "Indie": "✨"
    };

    const icon = genreIcons[targetGenre] || "🎯";

    const iconElem = document.getElementById('genreCardIcon');
    if (iconElem) iconElem.textContent = icon;

    const titleElem = document.getElementById('genreCardTitle');
    if (titleElem) titleElem.textContent = `${icon} ${targetGenre} Genre Market Benchmark`;

    const subtitleElem = document.getElementById('genreCardSubtitle');
    if (subtitleElem) subtitleElem.textContent = `Empirical baseline derived from ${gData.count.toLocaleString()} verified ${targetGenre} games on Steam`;

    const matchBadge = document.getElementById('genreMatchBadge');
    if (matchBadge) matchBadge.textContent = `${targetGenre} Lens Active`;

    // 1. Contrast
    const genreContrast = gData.contrast.median;
    const diffContrast = round(cv.brightnessStd - genreContrast, 1);
    const medContrastElem = document.getElementById('genreMedContrast');
    if (medContrastElem) medContrastElem.textContent = `${genreContrast} std dev`;
    const deltaContrastElem = document.getElementById('genreDeltaContrast');
    if (deltaContrastElem) {
        deltaContrastElem.textContent = `Your: ${cv.brightnessStd} (${diffContrast >= 0 ? '+' : ''}${diffContrast} vs median)`;
        deltaContrastElem.className = `genre-stat-delta ${diffContrast >= 0 ? 'delta-pos' : 'delta-neg'}`;
    }

    // 2. Warmth
    const genreWarm = gData.warm_palette_pct;
    const diffWarm = round(cv.warmPct - genreWarm, 1);
    const warmShareElem = document.getElementById('genreWarmShare');
    if (warmShareElem) warmShareElem.textContent = `${genreWarm}% Warm`;
    const deltaWarmElem = document.getElementById('genreDeltaWarm');
    if (deltaWarmElem) {
        deltaWarmElem.textContent = `Your: ${cv.warmPct}% (${diffWarm >= 0 ? '+' : ''}${diffWarm}% vs genre)`;
        deltaWarmElem.className = `genre-stat-delta ${diffWarm >= 0 ? 'delta-pos' : 'delta-neutral'}`;
    }

    // 3. Entropy
    const genreEntropy = gData.entropy.median;
    const diffEntropy = round(cv.entropy - genreEntropy, 2);
    const entropyElem = document.getElementById('genreEntropy');
    if (entropyElem) entropyElem.textContent = `${genreEntropy} bits`;
    const deltaEntropyElem = document.getElementById('genreDeltaEntropy');
    if (deltaEntropyElem) {
        deltaEntropyElem.textContent = `Your: ${cv.entropy} (${diffEntropy >= 0 ? '+' : ''}${diffEntropy} bits)`;
        deltaEntropyElem.className = `genre-stat-delta ${diffEntropy >= 0 ? 'delta-pos' : 'delta-neg'}`;
    }

    // 4. Edge Density
    const genreEdge = gData.edge_density.median;
    const diffEdge = round(cv.edgeDensity - genreEdge, 1);
    const edgeElem = document.getElementById('genreEdgeDensity');
    if (edgeElem) edgeElem.textContent = `${genreEdge}% Edge`;
    const deltaEdgeElem = document.getElementById('genreDeltaEdge');
    if (deltaEdgeElem) {
        deltaEdgeElem.textContent = `Your: ${cv.edgeDensity}% (${diffEdge >= 0 ? '+' : ''}${diffEdge}%)`;
        deltaEdgeElem.className = `genre-stat-delta ${diffEdge >= 0 ? 'delta-pos' : 'delta-neg'}`;
    }

    // Tailored Recommendation Tip
    const recElem = document.getElementById('genreRecommendationText');
    if (recElem) recElem.innerHTML = `<strong>Tailored ${targetGenre} Advice:</strong> ${gData.tip}`;

    card.style.display = 'block';
}

/**
 * Render In-Situ Competition Simulator (Contextual Genre Lineup with User in Center Position)
 */
function renderSimulatorLineups(userImgSrc, userGameName, appid, genreKey = 'all') {
    let catalog = typeof STORE_CATALOG !== 'undefined' ? STORE_CATALOG : [];

    // Pick contextual genre competitors if available
    let targetGenre = genreKey;
    if (targetGenre === 'all') {
        targetGenre = detectGenreFromTags(currentLoadedTags) || 'all';
    }

    if (typeof benchmarksData !== 'undefined' && benchmarksData.genre_competitors && benchmarksData.genre_competitors[targetGenre]) {
        catalog = benchmarksData.genre_competitors[targetGenre];
    }

    // Filter out user's current game from the catalog
    const others = catalog.filter(g => String(g.appid) !== String(appid) && (g.name || "").toLowerCase() !== (userGameName || "").toLowerCase());
    
    // Exactly 9 items: 4 surrounding games, USER CAPSULE (at index 4 / center), 4 surrounding games
    const fallbackGame = { name: "Steam Game", imageUrl: "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg" };
    const items9 = [
        others[0] || fallbackGame,
        others[1] || fallbackGame,
        others[2] || fallbackGame,
        others[3] || fallbackGame,
        { name: userGameName || "Your Game", imageUrl: userImgSrc, isUser: true }, // Center (Row 2, Col 2)
        others[4] || fallbackGame,
        others[5] || fallbackGame,
        others[6] || fallbackGame,
        others[7] || fallbackGame
    ];

    // 1. Large Browse 3x3 Grid (9 Entries)
    const largeGrid = document.getElementById('largeSimRow');
    if (largeGrid) {
        largeGrid.innerHTML = items9.map(g => `
            <div class="sim-capsule-item ${g.isUser ? 'user-capsule-item' : ''}" title="${g.name}">
                <div class="sim-capsule-thumb">
                    <img src="${g.imageUrl}" alt="${g.name}" loading="lazy">
                </div>
            </div>
        `).join('');
    }

    // 2. Seamless 120px Discovery Queue 3x3 Matrix (9 Entries, gapless, borderless)
    const microMatrix = document.getElementById('microSimQueue');
    if (microMatrix) {
        microMatrix.innerHTML = items9.map(g => `
            <div class="micro-matrix-item ${g.isUser ? 'user-micro-item' : ''}" title="${g.name}">
                <img src="${g.imageUrl}" alt="${g.name}" loading="lazy">
            </div>
        `).join('');
    }
}

/**
 * Main Analysis and Dashboard Update
 */
function analyzeAndDisplay(img, imgSrc, gameName, price, tags, appid, storeUrl) {
    const cv = runComputerVision(img);
    const scores = evaluateScores(cv);

    // Save global state
    currentCvResult = cv;
    currentScores = scores;
    currentLoadedImgSrc = imgSrc;
    currentLoadedGameName = gameName || "Steam Game";
    currentLoadedAppId = appid;
    currentLoadedTags = tags || [];

    // Detect target genre or respect user manual dropdown selection
    let initialGenre = 'all';
    if (typeof genreSelectDropdown !== 'undefined' && genreSelectDropdown && genreSelectDropdown.value !== 'auto') {
        initialGenre = genreSelectDropdown.value;
    } else {
        const detected = detectGenreFromTags(tags);
        if (detected) initialGenre = detected;
    }
    currentGenreLens = initialGenre;

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

    if (heroTagsContainer) {
        heroTagsContainer.innerHTML = '';
        if (tags && tags.length > 0) {
            tags.slice(0, 4).forEach(t => {
                const span = document.createElement('span');
                span.className = 'meta-pill';
                span.textContent = t;
                heroTagsContainer.appendChild(span);
            });
        }
    }

    // 2. Update Genre Lens Pills & Synchronized Dropdowns
    document.querySelectorAll('.genre-pill-btn').forEach(btn => {
        const g = btn.getAttribute('data-genre') || 'all';
        if (g.toLowerCase() === currentGenreLens.toLowerCase()) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    document.querySelectorAll('.genre-sync-dropdown').forEach(dropdown => {
        dropdown.value = currentGenreLens === 'all' ? 'all' : currentGenreLens;
    });

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
    tierBadge.textContent = scores.tierName;
    tierBadge.className = `tier-badge ${scores.tierBadgeClass}`;

    document.getElementById('percentileText').textContent = scores.percentile;
    document.getElementById('scoreHeadline').textContent = scores.headline;
    document.getElementById('scoreSummary').textContent = scores.summary;

    document.getElementById('qsContrast').textContent = `${cv.brightnessStd > 60 ? 'High' : 'Flat'} (${cv.brightnessStd})`;
    document.getElementById('qsPalette').textContent = `${cv.warmPct > 45 ? 'Warm Pop' : 'Cool/Neutral'}`;
    document.getElementById('qsEntropy').textContent = `${cv.entropy} bits`;
    document.getElementById('qsFocus').textContent = cv.isCenterFocused ? 'Center Hero' : 'Edge-Heavy';

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

    // 7. Update 5 Metric Rows
    updateMetricRow('mContrastScore', 'mContrastBar', 'mContrastVal', scores.contrastScore, `Your: ${cv.brightnessStd} std dev`, (cv.brightnessStd / 85) * 100);
    updateMetricRow('mWarmthScore', 'mWarmthBar', 'mWarmthVal', scores.warmthScore, `Your: ${cv.warmPct}% Warm`, Math.min(100, cv.warmPct * 1.5));
    updateMetricRow('mEntropyScore', 'mEntropyBar', 'mEntropyVal', scores.entropyScore, `Your: ${cv.entropy} bits`, (cv.entropy / 7.5) * 100);
    updateMetricRow('mEdgeScore', 'mEdgeBar', 'mEdgeVal', scores.edgeScore, `Your: ${cv.edgeDensity}% Edge`, (cv.edgeDensity / 22) * 100);
    updateMetricRow('mFocusScore', 'mFocusBar', 'mFocusVal', scores.focusScore, cv.isCenterFocused ? `Center Focused (+${cv.spotlightRatio})` : 'Border-Heavy', cv.isCenterFocused ? 85 : 45);

    // 8. Generate Tailored Checklist
    generateChecklist(cv, scores, currentGenreLens);

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

function updateMetricRow(badgeId, barId, valId, score, valText, barWidthPct) {
    const badge = document.getElementById(badgeId);
    badge.textContent = `${score}/100`;
    badge.className = `metric-tag ${score >= 85 ? 'tag-green' : score >= 70 ? 'tag-gold' : 'tag-red'}`;

    const bar = document.getElementById(barId);
    bar.style.width = `${Math.min(100, Math.max(10, barWidthPct))}%`;
    bar.className = `metric-progress-fill ${score >= 85 ? 'fill-pass' : score >= 70 ? 'fill-warn' : 'fill-fail'}`;

    document.getElementById(valId).textContent = valText;
}

/**
 * Generate Tailored Checklist Recommendations (with Genre-Specific Intelligence)
 */
function generateChecklist(cv, scores, genreKey = 'all') {
    const container = document.getElementById('checklistContainer');
    container.innerHTML = '';

    const items = [];

    // Genre-specific tailored card at the top
    let targetGenre = genreKey;
    if (!targetGenre || targetGenre === 'all') {
        targetGenre = detectGenreFromTags(currentLoadedTags) || 'Action';
    }

    if (typeof benchmarksData !== 'undefined' && benchmarksData.genres && benchmarksData.genres[targetGenre]) {
        const gMeta = benchmarksData.genres[targetGenre];
        items.push({
            status: 'pass',
            title: `🎯 ${targetGenre} Genre Market Advice`,
            desc: gMeta.tip
        });
    }

    // Contrast item
    if (cv.brightnessStd >= 62) {
        items.push({
            status: 'pass',
            title: 'Dynamic Range & Contrast',
            desc: `Your contrast score (${cv.brightnessStd}) matches or exceeds the Mega-Hit average (63.0). Highlights and shadow values are clearly separated.`
        });
    } else {
        items.push({
            status: 'fail',
            title: 'Low Dynamic Range (Flat Midtones)',
            desc: `Your contrast (${cv.brightnessStd}) is below the Mega-Hit benchmark (63.0). Increase the brightness of your key light and deepen background shadows by 15-20%.`
        });
    }

    // Warmth item
    if (cv.warmPct >= 45) {
        items.push({
            status: 'pass',
            title: 'Steam UI Saliency',
            desc: `Warm accent colors (${cv.warmPct}%) provide strong chromatic contrast against Steam's dark navy client.`
        });
    } else {
        items.push({
            status: 'warn',
            title: 'Add Warm Accent Lighting',
            desc: `Your palette is primarily neutral/cool (${cv.neutralPct}% neutral). Add a warm rim-light, fire ember, or golden title glow to immediately pop on Steam.`
        });
    }

    // Entropy item
    if (cv.entropy >= 6.8) {
        items.push({
            status: 'pass',
            title: 'Rendering Depth & Texture',
            desc: `High Shannon entropy (${cv.entropy} bits) indicates rich tonal gradients and professional key art rendering.`
        });
    } else {
        items.push({
            status: 'fail',
            title: 'Soft / Low Information Depth',
            desc: `Entropy is low (${cv.entropy} bits vs 6.99 benchmark). Avoid flat unlit 3D models or washed-out backgrounds.`
        });
    }

    // Composition item
    if (cv.isCenterFocused) {
        items.push({
            status: 'pass',
            title: 'Hero Spotlight Composition',
            desc: `Light is concentrated on the center character, framing the focal subject and guiding the viewer's eye.`
        });
    } else {
        items.push({
            status: 'warn',
            title: 'Apply Edge Vignetting',
            desc: `Light is currently scattered around the borders. Darken the outer 15% edges to lock attention on your hero character.`
        });
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = `check-item-card item-${item.status}`;
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
