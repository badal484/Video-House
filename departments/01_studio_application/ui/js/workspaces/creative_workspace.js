/**
 * Creative Workspace (Central 4-Quadrant NLE Viewport).
 * Unites Quadrant 1 (Asset Browser), Quadrant 2 (Program Monitor),
 * Quadrant 3 (Properties Inspector), and Quadrant 4 (Multi-Track Timeline).
 */

import { store } from "../state.js";
import { AssetBrowserComponent } from "../components/asset_browser.js";
import { MediaPreviewComponent } from "../components/media_preview.js";

export class CreativeWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    this.container.innerHTML = `
      <div class="workspace-grid" id="creative-quadrant-grid">
        <!-- Q1: Left Asset Browser Panel -->
        <div class="grid-quadrant-left">
          <div class="panel-header">
            <div class="panel-title">Media Bin & Assets</div>
          </div>
          <div id="q1-asset-mount" style="flex: 1; overflow: hidden; display: flex;"></div>
        </div>

        <!-- Horizontal Left Splitter -->
        <div class="splitter-h splitter-left" id="splitter-left"></div>

        <!-- Q2: Center Program Monitor -->
        <div class="grid-quadrant-center">
          <div class="panel-header">
            <div class="panel-title">Program Monitor (Viewport)</div>
          </div>
          <div id="q2-monitor-mount" style="flex: 1; overflow: hidden; display: flex;"></div>
        </div>

        <!-- Horizontal Right Splitter -->
        <div class="splitter-h splitter-right" id="splitter-right"></div>

        <!-- Q3: Right Context Inspector -->
        <div class="grid-quadrant-right">
          <div class="panel-header">
            <div class="panel-title">Inspector & Properties</div>
          </div>
          <div class="panel-body" id="q3-inspector-mount">
            <div style="font-size: 11px; color: var(--studio-text-muted); padding: 12px; text-align: center;">
              Select a clip, track, or asset to inspect technical properties.
            </div>
          </div>
        </div>

        <!-- Vertical Bottom Splitter -->
        <div class="splitter-v" id="splitter-bottom"></div>

        <!-- Q4: Bottom Editorial Multi-Track Timeline -->
        <div class="grid-quadrant-bottom">
          <div class="timeline-toolbar">
            <div class="timeline-tools">
              <button class="btn btn-ghost btn-xs" id="btn-blade" title="Blade / Split Clip (B)">✂ Split</button>
              <button class="btn btn-ghost btn-xs" id="btn-ripple-del" title="Ripple Delete Clip">⌫ Delete</button>
              <button class="btn btn-ghost btn-xs" id="btn-undo" title="Undo (Cmd+Z)">↺ Undo</button>
              <button class="btn btn-ghost btn-xs" id="btn-redo" title="Redo (Cmd+Shift+Z)">↻ Redo</button>
            </div>
            <div class="timeline-zoom-controls">
              <span style="font-size: 10px; color: var(--studio-text-muted);">ZOOM</span>
              <input type="range" min="0.5" max="3" step="0.1" value="1" id="timeline-zoom-slider" style="width: 80px;" />
            </div>
          </div>

          <div class="timeline-ruler-track-wrapper">
            <!-- Headers Column -->
            <div class="timeline-headers-column">
              <div class="timeline-ruler" style="display: flex; align-items: center; padding-left: 8px; font-size: 10px; color: var(--studio-text-muted);">TRACKS</div>
              <div class="track-header"><span>V2 Graphics</span><span class="badge" style="font-size: 8px;">SVG</span></div>
              <div class="track-header"><span>V1 Video</span><span class="badge" style="font-size: 8px;">MASTER</span></div>
              <div class="track-header"><span>A1 Dialogue</span><span class="badge" style="font-size: 8px;">VOICE</span></div>
              <div class="track-header"><span>A2 Music</span><span class="badge" style="font-size: 8px;">SCORE</span></div>
            </div>

            <!-- Scrollable Track Lanes -->
            <div class="track-lane-area" id="timeline-scroll-area">
              <div class="timeline-ruler" id="time-ruler-ticks" style="width: 1200px; display: flex; align-items: center; font-size: 9px; color: var(--studio-text-muted); padding: 0 10px;">
                <span>00:00:00</span>
                <span style="margin-left: 200px;">00:00:10</span>
                <span style="margin-left: 200px;">00:00:20</span>
                <span style="margin-left: 200px;">00:00:30</span>
                <span style="margin-left: 200px;">00:00:40</span>
                <span style="margin-left: 200px;">00:00:50</span>
              </div>

              <div class="timeline-tracks-body" style="width: 1200px;">
                <!-- Playhead Needle -->
                <div class="playhead-needle" id="timeline-playhead-needle" style="left: 0px;">
                  <div class="playhead-head"></div>
                </div>

                <!-- V2 Graphics Track -->
                <div class="track-lane">
                  <div class="timeline-clip clip-graphics" style="left: 100px; width: 140px;" data-id="clip_title_01">
                    <div>Lower Third Title</div>
                    <div style="font-size: 8px; opacity: 0.8;">Motion Canvas SVG</div>
                  </div>
                </div>

                <!-- V1 Video Track -->
                <div class="track-lane">
                  <div class="timeline-clip" style="left: 20px; width: 280px;" data-id="clip_video_01">
                    <div>Shot 01: Establishing Pan</div>
                    <div style="font-size: 8px; opacity: 0.8;">ProRes 422 HQ</div>
                  </div>
                  <div class="timeline-clip" style="left: 310px; width: 220px;" data-id="clip_video_02">
                    <div>Shot 02: Close-up Action</div>
                    <div style="font-size: 8px; opacity: 0.8;">Runway Gen-3</div>
                  </div>
                </div>

                <!-- A1 Dialogue Track -->
                <div class="track-lane">
                  <div class="timeline-clip clip-audio" style="left: 30px; width: 260px;" data-id="clip_audio_01">
                    <div>Take 01 Voice Dub (EN)</div>
                    <div style="font-size: 8px; opacity: 0.8;">24-bit 48kHz WAV</div>
                  </div>
                </div>

                <!-- A2 Music Track -->
                <div class="track-lane">
                  <div class="timeline-clip clip-audio" style="left: 0px; width: 600px; background-color: var(--studio-track-music);" data-id="clip_music_01">
                    <div>Cinematic Ambient Score (-14 LUFS)</div>
                    <div style="font-size: 8px; opacity: 0.8;">Procedural Synth</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Mount Sub-components
    new AssetBrowserComponent(this.container.querySelector("#q1-asset-mount"));
    new MediaPreviewComponent(this.container.querySelector("#q2-monitor-mount"));

    this.bindEvents();
  }

  bindEvents() {
    // Playhead tracking
    const scrollArea = this.container.querySelector("#timeline-scroll-area");
    const needle = this.container.querySelector("#timeline-playhead-needle");

    scrollArea.addEventListener("click", (e) => {
      const rect = scrollArea.getBoundingClientRect();
      const clickX = e.clientX - rect.left + scrollArea.scrollLeft;
      needle.style.left = `${clickX}px`;
      const seconds = (clickX / 20); // 20px per second
      store.setPlayhead(seconds);
    });

    // Clip Selection
    this.container.querySelectorAll(".timeline-clip").forEach(clip => {
      clip.addEventListener("click", (e) => {
        e.stopPropagation();
        this.container.querySelectorAll(".timeline-clip").forEach(c => c.classList.remove("selected"));
        clip.classList.add("selected");
        const clipId = clip.getAttribute("data-id");
        store.setState({ selectedClipId: clipId });
        this.renderInspector(clipId);
      });
    });

    // Timeline editing buttons
    this.container.querySelector("#btn-blade").addEventListener("click", () => {
      const sel = store.getState().selectedClipId;
      if (sel) store.addNotification(`Blade cut executed on clip '${sel}' at playhead`, "info");
      else store.addNotification("Select a clip on the timeline first.", "warning");
    });

    this.container.querySelector("#btn-ripple-del").addEventListener("click", () => {
      const sel = store.getState().selectedClipId;
      if (sel) store.addNotification(`Ripple deleted clip '${sel}'`, "info");
    });
  }

  renderInspector(clipId) {
    const inspectorMount = this.container.querySelector("#q3-inspector-mount");
    inspectorMount.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: var(--space-3);">
        <div>
          <div style="font-weight: 600; font-size: 13px; color: var(--studio-text-primary);">${clipId}</div>
          <div style="font-size: 11px; color: var(--studio-text-muted);">OpenTimelineIO Track Item</div>
        </div>

        <div style="display: flex; flex-direction: column; gap: var(--space-1);">
          <label style="font-size: 10px; color: var(--studio-text-secondary);">Opacity (%)</label>
          <input type="range" min="0" max="100" value="100" style="width: 100%;" />
        </div>

        <div style="display: flex; flex-direction: column; gap: var(--space-1);">
          <label style="font-size: 10px; color: var(--studio-text-secondary);">Audio Gain (dB)</label>
          <input type="range" min="-24" max="12" value="0" style="width: 100%;" />
        </div>

        <div style="display: flex; flex-direction: column; gap: var(--space-1);">
          <label style="font-size: 10px; color: var(--studio-text-secondary);">Color Space IDT</label>
          <select class="select">
            <option>ACEScg</option>
            <option>Rec.709</option>
            <option>ARRI LogC4</option>
            <option>Sony S-Log3</option>
          </select>
        </div>

        <div style="padding-top: var(--space-2); border-top: 1px solid var(--studio-border-subtle); display: flex; gap: var(--space-2);">
          <button class="btn btn-secondary btn-xs" style="flex: 1;">Split (B)</button>
          <button class="btn btn-danger btn-xs" style="flex: 1;">Delete</button>
        </div>
      </div>
    `;
  }
}

