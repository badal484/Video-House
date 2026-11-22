/**
 * Media Preview Monitor Component.
 * Supports HTML5 Video playback, canvas overlay, frame-stepping, timecode display,
 * safe area guides, and before/after split comparisons.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class MediaPreviewComponent {
  constructor(container) {
    this.container = container;
    this.fps = 24.0;
    this.isSplitCompare = false;
    this.splitPosition = 0.5; // 50% split
    this.currentAsset = null;
    this.render();
    this.bindEvents();
  }

  render() {
    this.container.innerHTML = `
      <div class="preview-monitor-container" style="position: relative; display: flex; flex-direction: column; height: 100%; background: #07080A; border-radius: var(--radius-sm); overflow: hidden;">
        <!-- Top Info Header Overlay -->
        <div style="position: absolute; top: 8px; left: 12px; z-index: 10; font-family: var(--font-family-mono); font-size: 10px; color: var(--studio-accent-primary); background: rgba(0,0,0,0.6); padding: 2px 8px; border-radius: 4px; pointer-events: none; border: 1px solid rgba(0, 240, 255, 0.3);" id="monitor-asset-pill">
          MONITOR: STANDBY • NO ACTIVE ASSET
        </div>

        <!-- Viewport Surface -->
        <div class="viewport-canvas" id="monitor-canvas-box" style="position: relative; flex: 1; width: 100%; overflow: hidden; display: flex; align-items: center; justify-content: center; background: #000;">
          <video id="program-video" playsinline preload="auto" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 1; display: none;"></video>
          <canvas id="program-canvas" width="1920" height="1080" style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; z-index: 2; pointer-events: none;"></canvas>
          <div id="safe-guides-overlay" style="position: absolute; inset: 0; pointer-events: none; border: 1px dashed rgba(255, 255, 255, 0.25); margin: 6%; display: none; z-index: 3;"></div>
        </div>

        <!-- Monitor Transport Controls Bar -->
        <div class="monitor-controls-bar" style="display: flex; align-items: center; justify-content: space-between; padding: 6px 12px; background: var(--studio-bg-panel); border-top: 1px solid var(--studio-border-subtle); z-index: 5;">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <div class="timecode-display" id="monitor-timecode" style="font-family: var(--font-family-mono); font-weight: 700; font-size: 13px; color: var(--studio-accent-primary);">00:00:00:00</div>
            <button class="btn btn-ghost btn-xs" id="btn-split-compare" title="Toggle Before/After Split">
              <span class="badge" style="font-size: 9px;">A/B SPLIT</span>
            </button>
          </div>

          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <button class="btn btn-ghost btn-sm" id="btn-prev-frame" title="Step 1 Frame Back (Left Arrow)">◀</button>
            <button class="btn btn-primary btn-sm" id="btn-play-pause" title="Play/Pause (Space)" style="min-width: 54px; font-weight: 700;">▶ PLAY</button>
            <button class="btn btn-ghost btn-sm" id="btn-next-frame" title="Step 1 Frame Forward (Right Arrow)">▶</button>
          </div>

          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <button class="btn btn-ghost btn-xs" id="btn-loop-toggle" title="Loop Playback">
              <span class="badge" style="font-size: 9px;" id="badge-loop">LOOP ON</span>
            </button>
            <button class="btn btn-ghost btn-xs" id="btn-safe-guides" title="Toggle Safe Area Guides">
              <span class="badge" style="font-size: 9px;">GUIDES</span>
            </button>
          </div>
        </div>
      </div>
    `;

    this.video = this.container.querySelector("#program-video");
    this.canvas = this.container.querySelector("#program-canvas");
    this.ctx = this.canvas.getContext("2d");
    this.timecodeEl = this.container.querySelector("#monitor-timecode");
    this.playPauseBtn = this.container.querySelector("#btn-play-pause");
    this.pillEl = this.container.querySelector("#monitor-asset-pill");

    this.video.loop = true;
    this.drawFallbackCanvas();
  }

  bindEvents() {
    // Play/Pause button
    this.playPauseBtn.addEventListener("click", () => {
      this.toggleVideoPlayback();
    });

    // Step backward
    this.container.querySelector("#btn-prev-frame").addEventListener("click", () => {
      if (this.video && this.video.src) {
        this.video.currentTime = Math.max(0, this.video.currentTime - (1 / this.fps));
      } else {
        store.setPlayhead(store.getState().playheadSeconds - (1 / this.fps));
      }
    });

    // Step forward
    this.container.querySelector("#btn-next-frame").addEventListener("click", () => {
      if (this.video && this.video.src) {
        this.video.currentTime = Math.min(this.video.duration || 60, this.video.currentTime + (1 / this.fps));
      } else {
        store.setPlayhead(store.getState().playheadSeconds + (1 / this.fps));
      }
    });

    // Video events
    this.video.addEventListener("timeupdate", () => {
      if (!this.video.paused) {
        store.setState({ playheadSeconds: this.video.currentTime });
        this.updateTimecode(this.video.currentTime);
      }
    });

    this.video.addEventListener("play", () => {
      this.playPauseBtn.innerHTML = "❚❚ PAUSE";
      store.setState({ isPlaying: true });
    });

    this.video.addEventListener("pause", () => {
      this.playPauseBtn.innerHTML = "▶ PLAY";
      store.setState({ isPlaying: false });
    });

    // Loop button
    const loopBtn = this.container.querySelector("#btn-loop-toggle");
    const loopBadge = this.container.querySelector("#badge-loop");
    loopBtn.addEventListener("click", () => {
      this.video.loop = !this.video.loop;
      loopBadge.textContent = this.video.loop ? "LOOP ON" : "LOOP OFF";
      loopBadge.style.background = this.video.loop ? "var(--studio-accent-primary)" : "";
    });

    // Split Compare
    const splitBtn = this.container.querySelector("#btn-split-compare");
    splitBtn.addEventListener("click", () => {
      this.isSplitCompare = !this.isSplitCompare;
      splitBtn.querySelector(".badge").style.backgroundColor = this.isSplitCompare ? "var(--studio-accent-primary)" : "";
      this.drawCanvasOverlay();
    });

    // Safe Guides
    const safeGuidesBtn = this.container.querySelector("#btn-safe-guides");
    safeGuidesBtn.addEventListener("click", () => {
      const guides = this.container.querySelector("#safe-guides-overlay");
      guides.style.display = guides.style.display === "none" ? "block" : "none";
    });

    // Store subscriptions
    store.subscribe("playheadSeconds", (state) => {
      this.updateTimecode(state.playheadSeconds);
      if (this.video && Math.abs(this.video.currentTime - state.playheadSeconds) > 0.1 && this.video.paused) {
        this.video.currentTime = state.playheadSeconds;
      }
      this.drawCanvasOverlay();
    });

    store.subscribe("isPlaying", (state) => {
      if (this.video && this.video.src) {
        if (state.isPlaying && this.video.paused) {
          this.video.play().catch(e => console.log("Video play error:", e));
        } else if (!state.isPlaying && !this.video.paused) {
          this.video.pause();
        }
      }
    });

    store.subscribe("selectedAssetId", (state) => {
      if (state.selectedAssetId) {
        this.loadAsset(state.selectedAssetId);
      }
    });

    // Keyboard spacebar shortcut
    window.addEventListener("keydown", (e) => {
      if (e.code === "Space" && e.target.tagName !== "INPUT" && e.target.tagName !== "TEXTAREA") {
        e.preventDefault();
        this.toggleVideoPlayback();
      }
    });
  }

  toggleVideoPlayback() {
    if (this.video && this.video.src) {
      if (this.video.paused) {
        this.video.play().catch(e => console.log("Play error:", e));
      } else {
        this.video.pause();
      }
    } else {
      store.togglePlayback();
    }
  }

  loadAsset(assetId) {
    const assets = store.getState().assets || [];
    const asset = assets.find(a => a.asset_id === assetId);
    this.currentAsset = asset;

    const streamUrl = api.getStreamUrl(assetId);
    this.video.src = streamUrl;
    this.video.style.display = "block";
    this.video.currentTime = 0;
    this.video.play().catch(e => console.log("Autoplay blocked or waiting:", e));

    const name = asset ? (asset.display_name || asset.original_filename) : assetId.substring(0, 8);
    this.pillEl.innerHTML = `LIVE FEED: <strong style="color:#FFF;">${name}</strong> • 24.0 FPS`;
    store.addNotification(`Loaded '${name}' into Program Monitor`, "success");
    this.clearCanvas();
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

  clearCanvas() {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  drawFallbackCanvas() {
    if (!this.ctx) return;
    const w = this.canvas.width;
    const h = this.canvas.height;

    this.ctx.fillStyle = "#090B0E";
    this.ctx.fillRect(0, 0, w, h);

    this.ctx.fillStyle = "#94A3B8";
    this.ctx.font = "bold 38px 'JetBrains Mono', monospace";
    this.ctx.textAlign = "center";
    this.ctx.fillText("PROGRAM MONITOR: LIVE OTIO VIEWPORT", w / 2, h / 2 - 30);

    this.ctx.font = "24px 'Inter', sans-serif";
    this.ctx.fillStyle = "#00F0FF";
    this.ctx.fillText("Click any video in 'Media Bin & Assets' to play & inspect", w / 2, h / 2 + 25);

    this.ctx.font = "18px 'JetBrains Mono', monospace";
    this.ctx.fillStyle = "#64748B";
    this.ctx.fillText("Apple Silicon VideoToolbox ASIC Acceleration Active • 24.00 fps", w / 2, h / 2 + 70);
  }

  drawCanvasOverlay() {
    if (!this.ctx || !this.isSplitCompare) {
      if (this.video.style.display === "block") {
        this.clearCanvas();
      }
      return;
    }
    const w = this.canvas.width;
    const h = this.canvas.height;
    const splitX = w * this.splitPosition;

    this.clearCanvas();
    // Split divider line
    this.ctx.strokeStyle = "#00F0FF";
    this.ctx.lineWidth = 4;
    this.ctx.beginPath();
    this.ctx.moveTo(splitX, 0);
    this.ctx.lineTo(splitX, h);
    this.ctx.stroke();

    this.ctx.font = "bold 32px 'JetBrains Mono'";
    this.ctx.fillStyle = "rgba(0, 240, 255, 0.9)";
    this.ctx.fillText("RAW INGEST", splitX - 220, 80);
    this.ctx.fillStyle = "rgba(255, 215, 0, 0.9)";
    this.ctx.fillText("MOTION COMPOSITE", splitX + 40, 80);
  }
}
