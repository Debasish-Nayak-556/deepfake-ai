/**
 * DeepFake AI Studio — Frontend App
 * ===================================
 * Handles: Theme toggle, Tab navigation, Drag-and-drop,
 *          API calls, Progress simulation, Particle canvas,
 *          Toast notifications, Result rendering.
 */

"use strict";

// ══════════════════════════════════════════════════════
// Particle Background
// ══════════════════════════════════════════════════════

(function initParticles() {
  const canvas = document.getElementById("particleCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let W, H, particles, animId;

  const isDark = () => document.documentElement.getAttribute("data-theme") !== "light";

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function createParticles() {
    const count = Math.min(Math.floor((W * H) / 14000), 90);
    particles = Array.from({ length: count }, () => ({
      x:   Math.random() * W,
      y:   Math.random() * H,
      r:   Math.random() * 1.4 + 0.3,
      dx:  (Math.random() - 0.5) * 0.4,
      dy:  (Math.random() - 0.5) * 0.4,
      hue: Math.random() < 0.5 ? 187 : 330,  // cyan or pink
    }));
  }

  function drawLine(a, b, dist) {
    const alpha = (1 - dist / 120) * (isDark() ? 0.22 : 0.12);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = `hsla(${a.hue}, 100%, ${isDark() ? 70 : 50}%, ${alpha})`;
    ctx.lineWidth = 0.5;
    ctx.stroke();
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];

      // Move
      p.x += p.dx;
      p.y += p.dy;
      if (p.x < 0 || p.x > W) p.dx *= -1;
      if (p.y < 0 || p.y > H) p.dy *= -1;

      // Draw dot
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${p.hue}, 100%, ${isDark() ? 70 : 50}%, ${isDark() ? 0.7 : 0.5})`;
      ctx.fill();

      // Connect nearby
      for (let j = i + 1; j < particles.length; j++) {
        const q  = particles[j];
        const dx = p.x - q.x;
        const dy = p.y - q.y;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < 120) drawLine(p, q, d);
      }
    }

    animId = requestAnimationFrame(draw);
  }

  function init() {
    cancelAnimationFrame(animId);
    resize();
    createParticles();
    draw();
  }

  window.addEventListener("resize", init, { passive: true });
  init();
})();


// ══════════════════════════════════════════════════════
// Theme Toggle
// ══════════════════════════════════════════════════════

(function initTheme() {
  const root   = document.documentElement;
  const btn    = document.getElementById("themeToggle");
  const icon   = btn.querySelector(".theme-icon");
  const stored = localStorage.getItem("df-theme") || "dark";

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    icon.textContent = theme === "dark" ? "◐" : "◑";
    localStorage.setItem("df-theme", theme);
  }

  apply(stored);
  btn.addEventListener("click", () => {
    apply(root.getAttribute("data-theme") === "dark" ? "light" : "dark");
  });
})();


// ══════════════════════════════════════════════════════
// Tab Navigation
// ══════════════════════════════════════════════════════

document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${tab}`)?.classList.add("active");
  });
});


// ══════════════════════════════════════════════════════
// Toast Notifications
// ══════════════════════════════════════════════════════

function toast(message, type = "info", duration = 3500) {
  const container = document.getElementById("toastContainer");
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => {
    el.style.animation = "toastIn 0.3s ease reverse forwards";
    setTimeout(() => el.remove(), 300);
  }, duration);
}


// ══════════════════════════════════════════════════════
// Progress Overlay
// ══════════════════════════════════════════════════════

let progressInterval = null;

const PROGRESS_STEPS = [
  { pct: 10, label: "Loading AI engine..." },
  { pct: 25, label: "Detecting faces in source..." },
  { pct: 40, label: "Detecting faces in target..." },
  { pct: 58, label: "Aligning face geometry..." },
  { pct: 72, label: "Blending with Poisson cloning..." },
  { pct: 85, label: "Applying enhancement pass..." },
  { pct: 95, label: "Finalising output..." },
];

function showProgress(title = "PROCESSING...") {
  const overlay  = document.getElementById("progressOverlay");
  const bar      = document.getElementById("progressBar");
  const label    = document.getElementById("progressLabel");
  const titleEl  = document.getElementById("progressTitle");

  overlay.classList.remove("hidden");
  titleEl.textContent = title;
  bar.style.width     = "0%";

  let step = 0;
  progressInterval = setInterval(() => {
    if (step >= PROGRESS_STEPS.length) return;
    bar.style.width   = PROGRESS_STEPS[step].pct + "%";
    label.textContent = PROGRESS_STEPS[step].label;
    step++;
  }, 600);
}

function hideProgress() {
  clearInterval(progressInterval);
  const bar     = document.getElementById("progressBar");
  const overlay = document.getElementById("progressOverlay");
  bar.style.width = "100%";
  setTimeout(() => {
    overlay.classList.add("hidden");
    bar.style.width = "0%";
  }, 400);
}

document.getElementById("progressCancel").addEventListener("click", () => {
  hideProgress();
  toast("Processing cancelled.", "error");
});


// ══════════════════════════════════════════════════════
// Drag & Drop + Preview  (shared helper)
// ══════════════════════════════════════════════════════

function initDropZone(zoneId, fileInputId, previewId, isVideo = false) {
  const zone    = document.getElementById(zoneId);
  const input   = document.getElementById(fileInputId);
  const preview = document.getElementById(previewId);

  if (!zone || !input) return;

  function showPreview(file) {
    if (!preview) return;
    const url = URL.createObjectURL(file);
    if (isVideo) {
      preview.src = url;
    } else {
      preview.src = url;
    }
    // Hide placeholder elements
    zone.querySelectorAll(".drop-icon, .drop-text, .drop-hint").forEach(el => {
      el.style.display = "none";
    });
    preview.classList.remove("hidden");
  }

  zone.addEventListener("click", () => input.click());

  zone.addEventListener("dragover", e => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });

  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));

  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) {
      input.files = e.dataTransfer.files;  // assign to input for FormData
      showPreview(file);
    }
  });

  input.addEventListener("change", () => {
    if (input.files[0]) showPreview(input.files[0]);
  });
}

// Init all drop zones
initDropZone("sourceZone",  "sourceFile",  "sourcePreview");
initDropZone("targetZone",  "targetFile",  "targetPreview");
initDropZone("vSourceZone", "vSourceFile", "vSourcePreview");
initDropZone("vTargetZone", "vTargetFile", "vTargetPreview", true);
initDropZone("detectZone",  "detectFile",  "detectPreview");


// ══════════════════════════════════════════════════════
// Range Sliders Live Update
// ══════════════════════════════════════════════════════

function bindRange(sliderId, valId, suffix = "") {
  const s = document.getElementById(sliderId);
  const v = document.getElementById(valId);
  if (!s || !v) return;
  s.addEventListener("input", () => { v.textContent = s.value + suffix; });
}

bindRange("blendSlider", "blendVal",      "%");
bindRange("frameSkip",   "frameSkipVal",  "");
bindRange("maxFrames",   "maxFramesVal",  "");


// ══════════════════════════════════════════════════════
// Build Meta HTML
// ══════════════════════════════════════════════════════

function buildMeta(data) {
  const rows = [
    ["Processing Time", (data.processing_time_sec ?? "—") + "s"],
    ["Source Faces",    data.source_faces_found ?? "—"],
    ["Target Faces",    data.target_faces_found ?? "—"],
    ["Blend Strength",  data.blend_strength != null ? (data.blend_strength * 100).toFixed(0) + "%" : "—"],
    ["Enhance",         data.enhance != null ? (data.enhance ? "ON" : "OFF") : "—"],
  ];
  return rows.map(([k, v]) =>
    `<div class="meta-row"><span class="meta-key">${k}</span><span class="meta-val">${v}</span></div>`
  ).join("");
}


// ══════════════════════════════════════════════════════
// API — Image Swap
// ══════════════════════════════════════════════════════

document.getElementById("swapImageBtn").addEventListener("click", async () => {
  const sourceFile = document.getElementById("sourceFile").files[0];
  const targetFile = document.getElementById("targetFile").files[0];

  if (!sourceFile) return toast("Please upload a source face image.", "error");
  if (!targetFile) return toast("Please upload a target image.", "error");

  const formData = new FormData();
  formData.append("source",  sourceFile);
  formData.append("target",  targetFile);
  formData.append("enhance", document.getElementById("enhanceToggle").checked ? "true" : "false");
  formData.append("blend",   (document.getElementById("blendSlider").value / 100).toFixed(2));

  showProgress("PROCESSING IMAGE SWAP...");

  try {
    const res  = await fetch("/api/swap/image", { method: "POST", body: formData });
    const data = await res.json();
    hideProgress();

    if (!data.success) {
      toast("Error: " + data.error, "error", 5000);
      return;
    }

    // Show result
    const panel    = document.getElementById("imageResult");
    const img      = document.getElementById("resultImg");
    const meta     = document.getElementById("imageMeta");
    const download = document.getElementById("imageDownload");

    img.src         = data.output_url + "?t=" + Date.now();
    meta.innerHTML  = buildMeta(data);
    download.href   = data.output_url;
    download.setAttribute("download", "deepfake_result.jpg");
    panel.classList.remove("hidden");

    toast("Face swap complete! ✓", "success");

  } catch (err) {
    hideProgress();
    toast("Network error: " + err.message, "error", 5000);
    console.error(err);
  }
});


// ══════════════════════════════════════════════════════
// API — Video Swap
// ══════════════════════════════════════════════════════

document.getElementById("swapVideoBtn").addEventListener("click", async () => {
  const srcFile = document.getElementById("vSourceFile").files[0];
  const vidFile = document.getElementById("vTargetFile").files[0];

  if (!srcFile) return toast("Please upload a source face image.", "error");
  if (!vidFile) return toast("Please upload a target video.", "error");

  const formData = new FormData();
  formData.append("source",       srcFile);
  formData.append("target_video", vidFile);
  formData.append("frame_skip",   document.getElementById("frameSkip").value);
  formData.append("max_frames",   document.getElementById("maxFrames").value);

  showProgress("PROCESSING VIDEO SWAP...");

  try {
    const res  = await fetch("/api/swap/video", { method: "POST", body: formData });
    const data = await res.json();
    hideProgress();

    if (!data.success) {
      toast("Error: " + data.error, "error", 5000);
      return;
    }

    const panel    = document.getElementById("videoResult");
    const vid      = document.getElementById("resultVideo");
    const meta     = document.getElementById("videoMeta");
    const download = document.getElementById("videoDownload");

    vid.src = data.output_url + "?t=" + Date.now();
    vid.load();
    meta.innerHTML = `
      <div class="meta-row"><span class="meta-key">Frames Total</span><span class="meta-val">${data.frames_total}</span></div>
      <div class="meta-row"><span class="meta-key">Frames Processed</span><span class="meta-val">${data.frames_processed}</span></div>
      <div class="meta-row"><span class="meta-key">Processing Time</span><span class="meta-val">${data.processing_time_sec}s</span></div>
    `;
    download.href = data.output_url;
    download.setAttribute("download", "deepfake_video.mp4");
    panel.classList.remove("hidden");

    toast("Video processing complete! ✓", "success");

  } catch (err) {
    hideProgress();
    toast("Network error: " + err.message, "error", 5000);
    console.error(err);
  }
});


// ══════════════════════════════════════════════════════
// API — Face Detection
// ══════════════════════════════════════════════════════

document.getElementById("detectBtn").addEventListener("click", async () => {
  const imgFile = document.getElementById("detectFile").files[0];
  if (!imgFile) return toast("Please upload an image to analyse.", "error");

  const formData = new FormData();
  formData.append("image", imgFile);

  showProgress("SCANNING FOR FACES...");

  try {
    const res  = await fetch("/api/detect", { method: "POST", body: formData });
    const data = await res.json();
    hideProgress();

    if (!data.success) {
      toast("Error: " + data.error, "error", 5000);
      return;
    }

    const panel = document.getElementById("detectResult");
    const chip  = document.getElementById("faceCountChip");
    const meta  = document.getElementById("detectMeta");
    const count = data.face_count;

    chip.textContent = `${count} FACE${count !== 1 ? "S" : ""}`;

    if (count === 0) {
      meta.innerHTML = `<p style="font-family:var(--font-mono);font-size:0.75rem;color:var(--neon-pink);padding:20px 0;">No faces detected in this image.</p>`;
    } else {
      const rows = data.faces.map((f, i) => {
        const [x, y, w, h] = f.bbox;
        return `<tr>
          <td>#${i + 1}</td>
          <td>${x}, ${y}</td>
          <td>${w} × ${h}px</td>
          <td>${(f.confidence * 100).toFixed(1)}%</td>
        </tr>`;
      }).join("");

      meta.innerHTML = `
        <div class="detect-table-wrap">
          <table class="detect-table">
            <thead>
              <tr>
                <th>#</th>
                <th>POSITION (X, Y)</th>
                <th>SIZE (W × H)</th>
                <th>CONFIDENCE</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    }

    panel.classList.remove("hidden");
    toast(`Detected ${count} face(s). ✓`, count > 0 ? "success" : "info");

  } catch (err) {
    hideProgress();
    toast("Network error: " + err.message, "error", 5000);
    console.error(err);
  }
});


// ══════════════════════════════════════════════════════
// Server Health Check
// ══════════════════════════════════════════════════════

async function checkServer() {
  const dot    = document.getElementById("serverStatus");
  const footer = document.getElementById("footerStatus");
  try {
    const res  = await fetch("/api/health");
    const data = await res.json();
    if (data.status === "ok") {
      dot.className    = "status-dot online";
      footer.textContent = "Server Online ✓";
    } else {
      throw new Error();
    }
  } catch {
    dot.className      = "status-dot offline";
    footer.textContent = "Server Offline";
  }
}

checkServer();
setInterval(checkServer, 30_000);   // re-check every 30 s
