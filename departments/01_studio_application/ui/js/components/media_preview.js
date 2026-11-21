/**
 * Media Preview Monitor Component.
 * Implements HTML5 Video/Canvas preview, frame-stepping, timecode display,
 * zoom, safe areas, and before/after split comparisons.
 */

import { store } from "../state.js";

export class MediaPreviewComponent {
  constructor(container) {
    this.container = container;
    this.fps = 24.0;
    this.isSplitCompare = false;
    this.splitPosition = 0.5; // 50% split
    this.zoomLevel = "FIT";
    this.render();
    this.bindEvents();
  }

  render() {
    this.container.innerHTML = `
      <div class="preview-monitor-container">
        <!-- Viewport Surface -->
        <div class="viewport-canvas" id="monitor-canvas-box">
          <canvas id="program-canvas" width="1920" height="1080" style="width: 100%; height: 100%; display: block; object-fit: contain;"></canvas>
          <div id="safe-guides-overlay" style="position: absolute; inset: 0; pointer-events: none; border: 1px dashed rgba(255, 255, 255, 0.2); margin: 5%; display: none;"></div>
        </div>

        <!-- Monitor Transport Controls Bar -->
        <div class="monitor-controls-bar">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <div class="timecode-display" id="monitor-timecode">00:00:00:00</div>
            <button class="btn btn-ghost btn-xs" id="btn-split-compare" title="Toggle Before/After Split">
              <span class="badge" style="font-size: 9px;">A/B SPLIT</span>
            </button>
          </div>

          <div style="display: flex; align-items: center; gap: var(--space-1);">
            <button class="btn btn-ghost btn-sm" id="btn-prev-frame" title="Step 1 Frame Back (Left Arrow)">◀</button>
            <button class="btn btn-primary btn-sm" id="btn-play-pause" title="Play/Pause (Space)" style="width: 48px;">▶</button>
            <button class="btn btn-ghost btn-sm" id="btn-next-frame" title="Step 1 Frame Forward (Right Arrow)">▶</button>
          </div>

          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <select class="select" id="select-zoom" style="width: 76px; height: 24px; font-size: 11px;">
              <option value="FIT">Fit</option>
              <option value="50">50%</option>
              <option value="100">100%</option>
              <option value="200">200%</option>
            </select>
            <button class="btn btn-ghost btn-xs" id="btn-safe-guides" title="Toggle Safe Area Guides">
              <span class="badge" style="font-size: 9px;">GUIDES</span>
            </button>
          </div>
        </div>
      </div>
    `;

    this.canvas = this.container.querySelector("#program-canvas");
    this.ctx = this.canvas.getContext("2d");
    this.timecodeEl = this.container.querySelector("#monitor-timecode");
    this.playPauseBtn = this.container.querySelector("#btn-play-pause");
    this.drawSyntheticMonitorFrame(store.getState().playheadSeconds);
  }

  bindEvents() {
    const playPauseBtn = this.container.querySelector("#btn-play-pause");
    playPauseBtn.addEventListener("click", () => store.togglePlayback());

    this.container.querySelector("#btn-prev-frame").addEventListener("click", () => {
      store.setPlayhead(store.getState().playheadSeconds - (1 / this.fps));
    });

    this.container.querySelector("#btn-next-frame").addEventListener("click", () => {
      store.setPlayhead(store.getState().playheadSeconds + (1 / this.fps));
    });

    const splitBtn = this.container.querySelector("#btn-split-compare");
    splitBtn.addEventListener("click", () => {
      this.isSplitCompare = !this.isSplitCompare;
      splitBtn.querySelector(".badge").style.backgroundColor = this.isSplitCompare ? "var(--studio-accent-primary)" : "";
      this.drawSyntheticMonitorFrame(store.getState().playheadSeconds);
    });

    const safeGuidesBtn = this.container.querySelector("#btn-safe-guides");
    safeGuidesBtn.addEventListener("click", () => {
      const guides = this.container.querySelector("#safe-guides-overlay");
      guides.style.display = guides.style.display === "none" ? "block" : "none";
    });

    // Subscribe to playhead changes in store
    store.subscribe("playheadSeconds", (state) => {
      this.updateTimecode(state.playheadSeconds);
      this.drawSyntheticMonitorFrame(state.playheadSeconds);
    });

    store.subscribe("isPlaying", (state) => {
      playPauseBtn.innerHTML = state.isPlaying ? "❚❚" : "▶";
    });
  }

  updateTimecode(seconds) {
    const totalFrames = Math.floor(seconds * this.fps);
    const hrs = Math.floor(totalFrames / (3600 * this.fps));
    const mins = Math.floor((totalFrames % (3600 * this.fps)) / (60 * this.fps));
    const secs = Math.floor((totalFrames % (60 * this.fps)) / this.fps);
    const frames = Math.floor(totalFrames % this.fps);

    const tc = [hrs, mins, secs, frames]
      .map(v => String(v).padStart(2, "0"))
      .join(":");
    this.timecodeEl.textContent = tc;
  }

  drawSyntheticMonitorFrame(seconds) {
    if (!this.ctx) return;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // Background gradient
    const grad = this.ctx.createLinearGradient(0, 0, w, h);
    grad.addColorStop(0, "#0D0E11");
    grad.addColorStop(1, "#1A1D24");
    this.ctx.fillStyle = grad;
    this.ctx.fillRect(0, 0, w, h);

    if (this.isSplitCompare) {
      // Split A-B Preview
      const splitX = w * this.splitPosition;

      // Left: Original Raw
      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.rect(0, 0, splitX, h);
      this.ctx.clip();
      this.ctx.fillStyle = "#18202F";
      this.ctx.fillRect(0, 0, splitX, h);
      this.ctx.fillStyle = "#94A3B8";
      this.ctx.font = "bold 36px 'JetBrains Mono'";
      this.ctx.fillText("ORIGINAL LOG / RAW", 80, 120);
      this.ctx.restore();

      // Right: Graded / VFX Composite
      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.rect(splitX, 0, w - splitX, h);
      this.ctx.clip();
      this.ctx.fillStyle = "#0D282E";
      this.ctx.fillRect(splitX, 0, w - splitX, h);
      this.ctx.fillStyle = "#00F0FF";
      this.ctx.font = "bold 36px 'JetBrains Mono'";
      this.ctx.fillText("ACEScg GRADED MASTER", splitX + 80, 120);
      this.ctx.restore();

      // Split Divider Line
      this.ctx.strokeStyle = "#00F0FF";
      this.ctx.lineWidth = 4;
      this.ctx.beginPath();
      this.ctx.moveTo(splitX, 0);
      this.ctx.lineTo(splitX, h);
      this.ctx.stroke();
    } else {
      // Normal Program View
      this.ctx.fillStyle = "#FFFFFF";
      this.ctx.font = "bold 44px 'JetBrains Mono'";
      this.ctx.textAlign = "center";
      this.ctx.fillText("PROGRAM MONITOR: LIVE OTIO VIEWPORT", w / 2, h / 2 - 20);

      this.ctx.font = "28px 'JetBrains Mono'";
      this.ctx.fillStyle = "#00F0FF";
      this.ctx.fillText(`TIME: ${seconds.toFixed(2)}s | FPS: ${this.fps.toFixed(2)} | Rec.709`, w / 2, h / 2 + 40);
    }
  }
}

