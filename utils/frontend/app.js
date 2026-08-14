// Global State
let config = {};
let availableFonts = [];
let availableTemplates = { meme_templates: [], poster_templates: [] };
let activeTab = "Poster"; // "Poster" or "Meme"
let activeBackdropSource = "gradient"; // "gradient", "templates", "ai-gen", "upload"
let activeGradientPalette = "Neon Cyberpunk";
let activeTemplateName = null;
let uploadedImageB64 = null;
let aiGeneratedImageB64 = null;
let captionsList = [];

// Initialize Page
document.addEventListener("DOMContentLoaded", async () => {
    await loadConfig();
    await loadFonts();
    await loadTemplates();
    
    // Set default visual layout
    switchTab("Poster");
    switchSourceTab("gradient");
    
    // Perform initial composition render
    setTimeout(() => {
        updateComposition();
    }, 400);
});

// Load aspect ratios, tones, palettes
async function loadConfig() {
    try {
        const res = await fetch("/api/config");
        config = await res.json();
        
        // Populate Aspect Ratios
        const aspectSelect = document.getElementById("select-aspect");
        aspectSelect.innerHTML = "";
        for (const [key, value] of Object.entries(config.aspect_ratios)) {
            const opt = document.createElement("option");
            opt.value = key;
            opt.textContent = key;
            if (key.includes("4:5")) opt.selected = true; // Default to Portrait
            aspectSelect.appendChild(opt);
        }
        
        // Populate Tones
        const toneSelect = document.getElementById("select-tone");
        toneSelect.innerHTML = "";
        config.tones.forEach(tone => {
            const opt = document.createElement("option");
            opt.value = tone;
            opt.textContent = tone;
            toneSelect.appendChild(opt);
        });

        // Populate Gradient Palette grid
        buildGradientGrid();
        
        // Update dimensions badge
        onAspectChanged();
    } catch (e) {
        console.error("Failed to load global config:", e);
    }
}

// Load fonts list
async function loadFonts() {
    try {
        const res = await fetch("/api/fonts");
        const data = await res.json();
        availableFonts = data.fonts;
        
        const fontSelect = document.getElementById("select-font");
        fontSelect.innerHTML = "";
        availableFonts.forEach(font => {
            const opt = document.createElement("option");
            opt.value = font;
            opt.textContent = font;
            if (font === "Montserrat Bold") opt.selected = true;
            fontSelect.appendChild(opt);
        });
    } catch (e) {
        console.error("Failed to load fonts:", e);
    }
}

// Load templates lists
async function loadTemplates() {
    try {
        const res = await fetch("/api/templates");
        availableTemplates = await res.json();
        buildTemplatesGrid();
    } catch (e) {
        console.error("Failed to load templates:", e);
    }
}

// Build Gradient Presets Grid
function buildGradientGrid() {
    const grid = document.getElementById("gradient-palette-grid");
    grid.innerHTML = "";
    
    if (!config.palettes) return;
    
    Object.keys(config.palettes).forEach((name, idx) => {
        const div = document.createElement("div");
        div.className = `grid-item ${name === activeGradientPalette ? 'active' : ''}`;
        div.textContent = name;
        div.onclick = () => {
            document.querySelectorAll("#gradient-palette-grid .grid-item").forEach(item => item.classList.remove("active"));
            div.classList.add("active");
            activeGradientPalette = name;
            updateComposition();
        };
        grid.appendChild(div);
    });
}

// Build Library templates grid
function buildTemplatesGrid() {
    const grid = document.getElementById("templates-grid");
    grid.innerHTML = "";
    
    const list = activeTab === "Meme" ? availableTemplates.meme_templates : availableTemplates.poster_templates;
    
    if (list.length === 0) {
        grid.innerHTML = `<div style="grid-column: span 3; font-size: 0.8rem; color: var(--text-secondary); text-align: center; padding: 1rem;">No templates available</div>`;
        return;
    }

    list.forEach(name => {
        const div = document.createElement("div");
        div.className = `grid-item ${name === activeTemplateName ? 'active' : ''}`;
        div.textContent = name;
        div.onclick = () => {
            document.querySelectorAll("#templates-grid .grid-item").forEach(item => item.classList.remove("active"));
            div.classList.add("active");
            activeTemplateName = name;
            updateComposition();
        };
        grid.appendChild(div);
    });
}

// Handle tab toggles (Meme vs Poster)
function switchTab(tab) {
    activeTab = tab;
    
    const tabPoster = document.getElementById("tab-poster");
    const tabMeme = document.getElementById("tab-meme");
    const posterFields = document.getElementById("poster-fields");
    const memeFields = document.getElementById("meme-fields");
    const darkenField = document.getElementById("darken-field");
    const selectFont = document.getElementById("select-font");
    
    if (tab === "Poster") {
        tabPoster.classList.add("active");
        tabMeme.classList.remove("active");
        posterFields.classList.add("active");
        memeFields.classList.remove("active");
        darkenField.style.display = "block";
        
        // Default safe margins and aspect ratio for Poster
        document.getElementById("input-margin").value = 80;
        selectFont.value = "Montserrat Bold";
    } else {
        tabPoster.classList.remove("active");
        tabMeme.classList.add("active");
        posterFields.classList.remove("active");
        memeFields.classList.add("active");
        darkenField.style.display = "none";
        
        // Default safe margins and aspect ratio for Meme
        document.getElementById("input-margin").value = 40;
        selectFont.value = "Impact";
    }

    // Refresh templates list for selected content type
    buildTemplatesGrid();
    updateComposition();
}

// Handle backdrop category switch
function switchSourceTab(source) {
    activeBackdropSource = source;
    
    document.querySelectorAll(".backdrop-sources .source-btn").forEach(btn => {
        if (btn.textContent.toLowerCase().includes(source.substring(0,3))) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    document.querySelectorAll(".src-content").forEach(content => {
        if (content.id === `src-${source}`) {
            content.classList.add("active");
        } else {
            content.classList.remove("active");
        }
    });
    
    updateComposition();
}

// Handle local uploaded files
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    document.getElementById("upload-filename").textContent = file.name;

    const reader = new FileReader();
    reader.onload = function(e) {
        uploadedImageB64 = e.target.result;
        updateComposition();
    };
    reader.readAsDataURL(file);
}

// Aspect ratio change updates badge dimensions representation
function onAspectChanged() {
    const aspectChoice = document.getElementById("select-aspect").value;
    if (config.aspect_ratios && config.aspect_ratios[aspectChoice]) {
        const dims = config.aspect_ratios[aspectChoice];
        document.getElementById("canvas-size-badge").textContent = `${dims[0]} x ${dims[1]}`;
    }
}

// Auto-craft prompt using generator
async function autoCraftPrompt() {
    const topic = document.getElementById("input-topic").value;
    const style = document.getElementById("select-ai-style").value;
    const mood = document.getElementById("select-ai-mood").value;
    
    try {
        const res = await fetch("/api/generate-prompt", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic,
                style,
                mood,
                event_type: activeTab
            })
        });
        const data = await res.json();
        document.getElementById("input-ai-prompt").value = data.prompt;
    } catch (e) {
        alert("Failed to auto-craft image prompt. Please try again.");
    }
}

// Generate image via API
async function generateAIImage() {
    const prompt = document.getElementById("input-ai-prompt").value;
    const aspectChoice = document.getElementById("select-aspect").value;
    const dims = config.aspect_ratios[aspectChoice] || [1080, 1080];
    const apiKey = document.getElementById("input-api-key").value;

    if (!prompt.trim()) {
        alert("Please enter or auto-craft a prompt first.");
        return;
    }

    const btn = document.querySelector("#src-ai-gen button[onclick='generateAIImage()']");
    const origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "⏳ Generating...";

    try {
        const res = await fetch("/api/generate-image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt,
                width: dims[0],
                height: dims[1],
                provider: "auto",
                api_key: apiKey ? apiKey : null
            })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "API Failure");
        }

        const data = await res.json();
        aiGeneratedImageB64 = data.image_b64;
        updateComposition();
        alert("AI Image generated successfully! Backdrop updated.");
    } catch (e) {
        alert(`Failed to generate AI image: ${e.message}\n\nFalling back to custom uploads or gradients.`);
    } finally {
        btn.disabled = false;
        btn.textContent = origText;
    }
}

// Fetch 5 captions via AI
async function generateAICaptions() {
    const topic = document.getElementById("input-topic").value;
    const tone = document.getElementById("select-tone").value;
    const apiKey = document.getElementById("input-api-key").value;
    
    const btn = document.getElementById("btn-generate-captions");
    const origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "⏳ Copying...";

    try {
        const res = await fetch("/api/captions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                topic,
                audience: "General Audience / Tech Enthusiasts",
                tone,
                event_type: activeTab,
                api_key: apiKey ? apiKey : null
            })
        });
        
        const data = await res.json();
        captionsList = data.captions;
        
        // Show banner notice if using fallback templates
        const noticeEl = document.getElementById("modal-notice");
        if (data.notice) {
            noticeEl.textContent = data.notice;
            noticeEl.style.display = "block";
        } else {
            noticeEl.style.display = "none";
        }

        buildCaptionsList();
        openModal();
    } catch (e) {
        alert(`Failed to generate captions: ${e.message}`);
    } finally {
        btn.disabled = false;
        btn.textContent = origText;
    }
}

// Render captions options in Modal
function buildCaptionsList() {
    const list = document.getElementById("captions-list-container");
    list.innerHTML = "";
    
    captionsList.forEach((cap, idx) => {
        const card = document.createElement("div");
        card.className = "suggestion-card";
        
        if (activeTab === "Meme") {
            card.innerHTML = `
                <div class="card-title">Meme Suggestion ${idx + 1}</div>
                <p><strong>Top:</strong> "${cap.top_text}"</p>
                <p><strong>Bottom:</strong> "${cap.bottom_text}"</p>
            `;
            card.onclick = () => {
                document.getElementById("meme-top").value = cap.top_text;
                document.getElementById("meme-bottom").value = cap.bottom_text;
                closeModal();
                updateComposition();
            };
        } else {
            card.innerHTML = `
                <div class="card-title">${cap.title}</div>
                <p>${cap.caption}</p>
                <div class="card-meta">
                    <span>🏷️ ${cap.badge}</span>
                    <span>🔗 ${cap.subtitle.substring(0, 30)}...</span>
                </div>
            `;
            card.onclick = () => {
                document.getElementById("poster-badge").value = cap.badge;
                document.getElementById("poster-title").value = cap.title;
                document.getElementById("poster-subtitle").value = cap.subtitle;
                document.getElementById("poster-caption").value = cap.caption;
                closeModal();
                updateComposition();
            };
        }
        
        list.appendChild(card);
    });
}

// Generate Composition
async function updateComposition() {
    const aspectChoice = document.getElementById("select-aspect").value;
    const dims = config.aspect_ratios ? (config.aspect_ratios[aspectChoice] || [1080, 1080]) : [1080, 1080];
    const safeMargin = parseInt(document.getElementById("input-margin").value) || 80;
    const fontName = document.getElementById("select-font").value;

    // Build payload structure
    const payload = {
        content_type: activeTab,
        target_size: dims,
        safe_margin: safeMargin,
        font_name: fontName
    };

    // Backdrop properties resolve
    if (activeBackdropSource === "gradient") {
        payload.gradient_palette = activeGradientPalette;
    } else if (activeBackdropSource === "templates") {
        payload.template_name = activeTemplateName;
    } else if (activeBackdropSource === "upload") {
        payload.base_image_b64 = uploadedImageB64;
    } else if (activeBackdropSource === "ai-gen") {
        payload.base_image_b64 = aiGeneratedImageB64;
    }

    if (activeTab === "Meme") {
        payload.top_text = document.getElementById("meme-top").value;
        payload.bottom_text = document.getElementById("meme-bottom").value;
        payload.font_size = parseInt(document.getElementById("meme-font-size").value) || 64;
        payload.stroke_width = parseInt(document.getElementById("meme-stroke-width").value) || 5;
        payload.uppercase = document.getElementById("meme-uppercase").checked;
        payload.vertical_offset = parseInt(document.getElementById("meme-offset").value) || 0;
    } else {
        payload.title = document.getElementById("poster-title").value;
        payload.subtitle = document.getElementById("poster-subtitle").value;
        payload.caption = document.getElementById("poster-caption").value;
        payload.badge_text = document.getElementById("poster-badge").value;
        payload.date_time = document.getElementById("poster-datetime").value;
        payload.location_cta = document.getElementById("poster-location").value;
        payload.show_border = document.getElementById("poster-border").checked;
        payload.overlay_opacity = parseFloat(document.getElementById("input-darken").value) || 0.60;
        payload.layout_align = document.getElementById("select-align").value;
    }

    // Update wrapper aspect ratio display to avoid squishing
    const canvasWrapper = document.querySelector(".canvas-wrapper");
    canvasWrapper.style.aspectRatio = `${dims[0]} / ${dims[1]}`;

    // Call API composition render
    try {
        const res = await fetch("/api/compose", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Composition Error");
        }

        const data = await res.json();
        const img = document.getElementById("composed-canvas");
        img.src = data.image_b64;
        document.getElementById("btn-download").disabled = false;
    } catch (e) {
        console.error("Composition error:", e);
    }
}

// Download final visual file
function downloadPNG() {
    const img = document.getElementById("composed-canvas");
    if (!img.src || img.src.startsWith("data:image/gif")) return;
    
    const link = document.createElement("a");
    link.href = img.src;
    
    // Build descriptive title
    const topic = document.getElementById("input-topic").value.toLowerCase().replace(/[^a-z0-9]+/g, "_");
    link.download = `${activeTab.toLowerCase()}_${topic}_studio.png`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Modal handling logic
function openModal() {
    document.getElementById("captions-modal").classList.add("active");
}

function closeModal() {
    document.getElementById("captions-modal").classList.remove("active");
}
