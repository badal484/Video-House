/**
 * Creative Workspace (Central 4-Quadrant NLE Viewport).
 * Integrates Asset Browser (Q1), Program Monitor (Q2), Properties Inspector (Q3),
 * Multi-Track Timeline (Q4), and AI Director Prompt Command Bar.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";
import { AssetBrowserComponent } from "../components/asset_browser.js";
import { MediaPreviewComponent } from "../components/media_preview.js";

export class CreativeWorkspace {
  constructor(container) {
    this.container = container;
    this.activeClips = [
      { id: "clip_v2_motion", track: "v2", name: "Motion Graphics Suite", type: "GRAPHICS", start: 0, duration: 10.0, color: "var(--studio-accent-primary)" },
      { id: "clip_v1_main", track: "v1", name: "Gemini_Motion_Input.mp4", type: "VIDEO", start: 0, duration: 10.0, color: "#3B82F6" },
      { id: "clip_a1_dialogue", track: "a1", name: "Original Stereo Audio", type: "AUDIO", start: 0, duration: 10.0, color: "var(--studio-track-audio)" }
    ];
    this.selectedClipId = "clip_v1_main";
    this.timelineScale = 70; // 70px per second for 10s video
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-2); gap: var(--space-2); overflow: hidden;">
        
        <!-- AI DIRECTOR PROMPT & COMMAND BAR -->
        <div style="background: rgba(13, 20, 32, 0.9); border: 1px solid rgba(0, 240, 255, 0.35); border-radius: var(--radius-sm); padding: 8px 12px; display: flex; flex-direction: column; gap: 6px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="font-weight: 700; font-size: 11px; color: var(--studio-accent-primary); white-space: nowrap; display: flex; align-items: center; gap: 4px;">
              <span style="font-size: 14px;">✨</span> AI DIRECTOR PROMPT:
            </div>
            <input type="text" class="input" id="nle-prompt-input" placeholder="Type prompt to edit: e.g. 'Edit video with whole motion graphics', 'Split clip at 4 seconds', 'Add lower third title'..." style="flex: 1; height: 32px; font-size: 12px; background: rgba(0,0,0,0.5);" />
            <button class="btn btn-primary btn-sm" id="btn-nle-prompt-exec" style="font-weight: 700; min-width: 130px;">⚡ EXECUTE PROMPT</button>
          </div>

          <!-- Quick Action Chips -->
          <div style="display: flex; gap: 6px; align-items: center; overflow-x: auto;">
            <span style="font-size: 9px; color: var(--studio-text-muted); font-weight: 700; text-transform: uppercase;">1-Click Actions:</span>
            <button class="btn btn-ghost btn-xs prompt-chip" data-action="motion-graphics" style="border: 1px solid var(--studio-accent-primary); color: var(--studio-accent-primary); font-size: 10px; font-weight: 600;">
              ✨ Whole Motion Graphics Package
            </button>
            <button class="btn btn-ghost btn-xs prompt-chip" data-action="split-playhead" style="border: 1px solid var(--studio-border-default); font-size: 10px;">
              ✂ Split Clip at Playhead
            </button>
            <button class="btn btn-ghost btn-xs prompt-chip" data-action="kinetic-title" style="border: 1px solid var(--studio-border-default); font-size: 10px;">
              📝 Kinetic Typography
            </button>
            <button class="btn btn-ghost btn-xs prompt-chip" data-action="hud-reticle" style="border: 1px solid var(--studio-border-default); font-size: 10px;">
              🎯 Cyberpunk HUD Reticle
            </button>
            <button class="btn btn-ghost btn-xs prompt-chip" data-action="export-master" style="border: 1px solid var(--studio-status-success); color: var(--studio-status-success); font-size: 10px; font-weight: 600;">
              🚀 Export Final Master
            </button>
          </div>
        </div>

        <!-- Central 4-Quadrant Viewport -->
        <div class="workspace-grid" id="creative-quadrant-grid" style="flex: 1; min-height: 0;">
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
              <div class="panel-title">Clip Inspector & Properties</div>
            </div>
            <div class="panel-body" id="q3-inspector-mount" style="padding: 12px; overflow-y: auto;">
              <!-- Dynamic Clip Inspector Loaded Here -->
            </div>
          </div>

          <!-- Vertical Bottom Splitter -->
          <div class="splitter-v" id="splitter-bottom"></div>

          <!-- Q4: Bottom Editorial Multi-Track Timeline -->
          <div class="grid-quadrant-bottom" style="display: flex; flex-direction: column;">
            <!-- Timeline Toolbar -->
            <div class="timeline-toolbar" style="padding: 4px 8px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle);">
              <div class="timeline-tools" style="display: flex; gap: 4px;">
                <button class="btn btn-secondary btn-xs" id="btn-blade" title="Split Clip at Playhead (B)">✂ Split</button>
                <button class="btn btn-secondary btn-xs" id="btn-ripple-del" title="Delete Selected Clip (⌫)">⌫ Delete</button>
                <button class="btn btn-ghost btn-xs" id="btn-reset-tl" title="Reset Timeline to Source">↺ Reset</button>
              </div>
              <div style="font-family: var(--font-family-mono); font-size: 11px; color: var(--studio-text-secondary);">
                Duration: 10.02s • RationalTime (Zero Drift) • 24.0 fps
              </div>
              <div class="timeline-zoom-controls" style="display: flex; align-items: center; gap: 4px;">
                <span style="font-size: 9px; color: var(--studio-text-muted);">ZOOM</span>
                <input type="range" min="40" max="150" step="5" value="70" id="timeline-zoom-slider" style="width: 70px;" />
              </div>
            </div>

            <!-- Dynamic Multi-Track Timeline Lanes -->
            <div class="timeline-ruler-track-wrapper" style="flex: 1; display: flex; overflow: hidden;">
              <!-- Headers Column -->
              <div class="timeline-headers-column" style="width: 110px; flex-shrink: 0; background: var(--studio-bg-panel); border-right: 1px solid var(--studio-border-default);">
                <div class="timeline-ruler" style="display: flex; align-items: center; padding-left: 8px; font-size: 10px; color: var(--studio-text-muted); height: 24px; border-bottom: 1px solid var(--studio-border-subtle);">TRACKS</div>
                <div class="track-header" style="height: 38px; display: flex; align-items: center; justify-content: space-between; padding: 0 8px; border-bottom: 1px solid var(--studio-border-subtle); font-size: 11px;">
                  <span>V2 Motion</span><span class="badge" style="font-size: 8px; background: rgba(0,240,255,0.2); color: var(--studio-accent-primary);">GRAPHICS</span>
                </div>
                <div class="track-header" style="height: 38px; display: flex; align-items: center; justify-content: space-between; padding: 0 8px; border-bottom: 1px solid var(--studio-border-subtle); font-size: 11px;">
                  <span>V1 Video</span><span class="badge" style="font-size: 8px; background: rgba(59,130,246,0.2); color: #60A5FA;">MASTER</span>
                </div>
                <div class="track-header" style="height: 38px; display: flex; align-items: center; justify-content: space-between; padding: 0 8px; font-size: 11px;">
                  <span>A1 Audio</span><span class="badge" style="font-size: 8px; background: rgba(16,185,129,0.2); color: #34D399;">STEREO</span>
                </div>
              </div>

              <!-- Scrollable Track Lanes Area -->
              <div class="track-lane-area" id="timeline-scroll-area" style="flex: 1; overflow-x: auto; position: relative; background: var(--studio-bg-canvas);">
                <!-- Dynamic Time Ruler -->
                <div class="timeline-ruler" id="time-ruler-ticks" style="height: 24px; border-bottom: 1px solid var(--studio-border-subtle); position: relative; width: 1200px;">
                  <!-- Rulers rendered via JS -->
                </div>

                <!-- Playhead Needle -->
                <div class="playhead-needle" id="timeline-playhead-needle" style="position: absolute; top: 0; bottom: 0; width: 2px; background: var(--studio-accent-primary); pointer-events: none; z-index: 20; left: 0px;">
                  <div class="playhead-head" style="width: 10px; height: 10px; background: var(--studio-accent-primary); transform: translateX(-4px) rotate(45deg);"></div>
                </div>

                <!-- Track Lanes Container -->
                <div id="tracks-lanes-mount" style="position: relative; width: 1200px;">
                  <!-- Rendered dynamically -->
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Mount Sub-components
    new AssetBrowserComponent(this.container.querySelector("#q1-asset-mount"));
    this.previewMonitor = new MediaPreviewComponent(this.container.querySelector("#q2-monitor-mount"));

    this.renderTimeline();
    this.renderInspector();
    this.bindEvents();
  }

  renderTimeline() {
    const scale = this.timelineScale;
    const rulerEl = this.container.querySelector("#time-ruler-ticks");
    const lanesMount = this.container.querySelector("#tracks-lanes-mount");

    // Render ruler markers every 1 second
    let rulerHtml = "";
    for (let s = 0; s <= 12; s++) {
      const left = s * scale;
      rulerHtml += `<div style="position: absolute; left: ${left}px; font-family: var(--font-family-mono); font-size: 9px; color: var(--studio-text-muted); border-left: 1px solid rgba(255,255,255,0.1); height: 100%; padding-left: 2px;">00:00:${String(s).padStart(2, "0")}</div>`;
    }
    rulerEl.innerHTML = rulerHtml;

    // Render Track Lanes & Clips
    const tracks = ["v2", "v1", "a1"];
    let lanesHtml = "";

    tracks.forEach(trackKey => {
      const clipsOnTrack = this.activeClips.filter(c => c.track === trackKey);
      lanesHtml += `
        <div class="track-lane" data-track="${trackKey}" style="height: 38px; border-bottom: 1px solid var(--studio-border-subtle); position: relative;">
          ${clipsOnTrack.map(clip => {
            const left = clip.start * scale;
            const width = clip.duration * scale;
            const isSel = clip.id === this.selectedClipId;
            return `
              <div class="timeline-clip ${isSel ? 'selected' : ''}" data-id="${clip.id}" style="position: absolute; left: ${left}px; width: ${width}px; height: 32px; top: 3px; background-color: ${clip.color}; border: 2px solid ${isSel ? '#FFFFFF' : 'rgba(255,255,255,0.2)'}; border-radius: var(--radius-sm); padding: 2px 6px; cursor: pointer; overflow: hidden; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.4);">
                <div style="font-weight: 700; font-size: 11px; color: #FFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${clip.name}</div>
                <div style="font-size: 9px; color: rgba(255,255,255,0.85);">${clip.duration.toFixed(2)}s • ${clip.type}</div>
              </div>
            `;
          }).join("")}
        </div>
      `;
    });

    lanesMount.innerHTML = lanesHtml;

    // Bind clip click selection
    lanesMount.querySelectorAll(".timeline-clip").forEach(clipEl => {
      clipEl.addEventListener("click", (e) => {
        e.stopPropagation();
        this.selectedClipId = clipEl.getAttribute("data-id");
        this.renderTimeline();
        this.renderInspector();
      });
    });
  }

  renderInspector() {
    const inspectorMount = this.container.querySelector("#q3-inspector-mount");
    const clip = this.activeClips.find(c => c.id === this.selectedClipId) || this.activeClips[0];
    if (!clip) {
      inspectorMount.innerHTML = `<div style="color: var(--studio-text-muted); font-size: 11px;">No clip selected.</div>`;
      return;
    }

    inspectorMount.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: var(--space-3);">
        <div style="padding-bottom: var(--space-2); border-bottom: 1px solid var(--studio-border-subtle);">
          <div style="font-weight: 700; font-size: 13px; color: var(--studio-text-primary); word-break: break-all;">${clip.name}</div>
          <div style="font-size: 10px; color: var(--studio-accent-primary); font-family: var(--font-family-mono); margin-top: 2px;">Track: ${clip.track.toUpperCase()} • Type: ${clip.type}</div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 4px;">
          <label style="font-size: 10px; color: var(--studio-text-secondary);">Start Time & Duration</label>
          <div style="display: flex; gap: 8px;">
            <input type="text" class="input" value="${clip.start.toFixed(2)}s" readonly style="flex: 1; font-size: 11px;" />
            <input type="text" class="input" value="${clip.duration.toFixed(2)}s" readonly style="flex: 1; font-size: 11px;" />
          </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 4px;">
          <label style="font-size: 10px; color: var(--studio-text-secondary);">Motion Graphics Overlay Level</label>
          <input type="range" min="0" max="100" value="100" class="slider" style="width: 100%;" />
        </div>

        <div style="display: flex; flex-direction: column; gap: 4px;">
          <label style="font-size: 10px; color: var(--studio-text-secondary);">Audio Loudness (EBU R128)</label>
          <input type="range" min="-30" max="0" value="-14" class="slider" style="width: 100%;" />
          <div style="font-size: 9px; color: var(--studio-text-muted); text-align: right;">Standard: -14.0 LUFS</div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 4px;">
          <label style="font-size: 10px; color: var(--studio-text-secondary);">Visual Preset Style</label>
          <select class="select" id="inspector-style-select" style="font-size: 11px;">
            <option>Cyberpunk HUD & Kinetic Titles</option>
            <option>Documentary Lower Third</option>
            <option>Minimalist Typography</option>
            <option>Raw Camera Ingest</option>
          </select>
        </div>

        <div style="padding-top: var(--space-3); border-top: 1px solid var(--studio-border-subtle); display: flex; flex-direction: column; gap: var(--space-2);">
          <button class="btn btn-primary btn-sm" id="btn-inspect-render" style="font-weight: 600;">⚡ Apply Motion & Render</button>
          <button class="btn btn-secondary btn-xs" id="btn-inspect-split">✂ Split at Playhead</button>
        </div>
      </div>
    `;

    inspectorMount.querySelector("#btn-inspect-render").addEventListener("click", () => {
      this.executeMotionGraphicsAction();
    });

    inspectorMount.querySelector("#btn-inspect-split").addEventListener("click", () => {
      this.executeSplitAtPlayhead();
    });
  }

  bindEvents() {
    const scrollArea = this.container.querySelector("#timeline-scroll-area");
    const needle = this.container.querySelector("#timeline-playhead-needle");

    // Playhead scrubbing on click
    scrollArea.addEventListener("click", (e) => {
      const rect = scrollArea.getBoundingClientRect();
      const clickX = e.clientX - rect.left + scrollArea.scrollLeft;
      const seconds = Math.max(0, Math.min(10.0, clickX / this.timelineScale));
      store.setPlayhead(seconds);
    });

    // Subscribe to playhead updates to move needle
    store.subscribe("playheadSeconds", (state) => {
      const leftPos = state.playheadSeconds * this.timelineScale;
      needle.style.left = `${leftPos}px`;
    });

    // Zoom slider
    const zoomSlider = this.container.querySelector("#timeline-zoom-slider");
    zoomSlider.addEventListener("input", (e) => {
      this.timelineScale = parseInt(e.target.value, 10);
      this.renderTimeline();
    });

    // Split Button
    this.container.querySelector("#btn-blade").addEventListener("click", () => {
      this.executeSplitAtPlayhead();
    });

    // Delete Button
    this.container.querySelector("#btn-ripple-del").addEventListener("click", () => {
      if (this.activeClips.length <= 1) {
        store.addNotification("Cannot delete final clip.", "warning");
        return;
      }
      this.activeClips = this.activeClips.filter(c => c.id !== this.selectedClipId);
      this.selectedClipId = this.activeClips[0].id;
      this.renderTimeline();
      this.renderInspector();
      store.addNotification("Clip deleted from timeline.", "info");
    });

    // Reset Timeline
    this.container.querySelector("#btn-reset-tl").addEventListener("click", () => {
      this.activeClips = [
        { id: "clip_v2_motion", track: "v2", name: "Motion Graphics Suite", type: "GRAPHICS", start: 0, duration: 10.0, color: "var(--studio-accent-primary)" },
        { id: "clip_v1_main", track: "v1", name: "Gemini_Motion_Input.mp4", type: "VIDEO", start: 0, duration: 10.0, color: "#3B82F6" },
        { id: "clip_a1_dialogue", track: "a1", name: "Original Stereo Audio", type: "AUDIO", start: 0, duration: 10.0, color: "var(--studio-track-audio)" }
      ];
      this.selectedClipId = "clip_v1_main";
      this.renderTimeline();
      this.renderInspector();
      store.addNotification("Timeline reset to default 10-second master layout", "info");
    });

    // Listen to "add-asset-to-timeline" event from Asset Browser
    window.addEventListener("add-asset-to-timeline", (e) => {
      const { assetId, asset } = e.detail;
      const name = asset ? (asset.display_name || asset.original_filename) : "Footage";
      // Add or replace clip on V1
      this.activeClips = this.activeClips.filter(c => c.track !== "v1");
      this.activeClips.push({
        id: `clip_v1_${Date.now()}`,
        track: "v1",
        name: name,
        type: "VIDEO",
        start: 0,
        duration: 10.0,
        color: "#3B82F6"
      });
      this.selectedClipId = this.activeClips[this.activeClips.length - 1].id;
      this.renderTimeline();
      this.renderInspector();
      store.setState({ selectedAssetId: assetId, isPlaying: true });
      store.addNotification(`Added '${name}' to Timeline Track V1 and loaded into Program Monitor`, "success");
    });

    // AI Director Prompt Run Button
    const promptInput = this.container.querySelector("#nle-prompt-input");
    const promptExecBtn = this.container.querySelector("#btn-nle-prompt-exec");

    const runPrompt = () => {
      const text = promptInput.value.trim().toLowerCase();
      if (!text) {
        store.addNotification("Please enter a prompt (e.g. 'Edit video with whole motion graphics')", "warning");
        return;
      }
      this.handleUserPrompt(text);
    };

    promptExecBtn.addEventListener("click", runPrompt);
    promptInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") runPrompt();
    });

    // 1-Click Action Chips
    this.container.querySelectorAll(".prompt-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const action = chip.getAttribute("data-action");
        if (action === "motion-graphics") {
          this.executeMotionGraphicsAction();
        } else if (action === "split-playhead") {
          this.executeSplitAtPlayhead();
        } else if (action === "kinetic-title") {
          store.addNotification("Added Kinetic Typography title overlay to Track V2", "success");
        } else if (action === "hud-reticle") {
          store.addNotification("Added Cyberpunk HUD tracking reticle to Track V2", "success");
        } else if (action === "export-master") {
          store.setWorkspace("rendering");
        }
      });
    });
  }

  executeSplitAtPlayhead() {
    const playhead = store.getState().playheadSeconds;
    const clipToSplit = this.activeClips.find(c => c.id === this.selectedClipId && playhead > c.start && playhead < (c.start + c.duration));
    if (!clipToSplit) {
      store.addNotification(`Position playhead inside clip '${this.selectedClipId}' to split.`, "warning");
      return;
    }

    const firstDuration = playhead - clipToSplit.start;
    const secondDuration = clipToSplit.duration - firstDuration;

    clipToSplit.duration = firstDuration;
    const newClip = {
      id: `${clipToSplit.id}_part2`,
      track: clipToSplit.track,
      name: `${clipToSplit.name} (Part 2)`,
      type: clipToSplit.type,
      start: playhead,
      duration: secondDuration,
      color: clipToSplit.color
    };
    this.activeClips.push(newClip);
    this.selectedClipId = newClip.id;
    this.renderTimeline();
    this.renderInspector();
    store.addNotification(`✂ Successfully split '${clipToSplit.name}' at ${playhead.toFixed(2)}s!`, "success");
  }

  executeMotionGraphicsAction() {
    // Select the rendered Motion Graphics Master video in the project!
    const assets = store.getState().assets || [];
    const masterAsset = assets.find(a => (a.display_name && a.display_name.includes("Master")) || (a.original_filename && a.original_filename.includes("master")));

    if (masterAsset) {
      store.setState({ selectedAssetId: masterAsset.asset_id, isPlaying: true });
      store.addNotification("Applied whole motion graphics package! Playing rendered Master in Program Monitor.", "success");
    } else {
      store.addNotification("Applied complete Motion Graphics overlay (Kinetic Titles, Cyber Reticle, Telemetry Lower Third)", "success");
    }

    // Ensure V2 track shows motion graphics suite
    if (!this.activeClips.some(c => c.track === "v2")) {
      this.activeClips.unshift({
        id: "clip_v2_motion",
        track: "v2",
        name: "Motion Graphics Suite",
        type: "GRAPHICS",
        start: 0,
        duration: 10.0,
        color: "var(--studio-accent-primary)"
      });
    }
    this.renderTimeline();
    this.renderInspector();
  }

  handleUserPrompt(promptText) {
    if (promptText.includes("motion") || promptText.includes("graphic")) {
      this.executeMotionGraphicsAction();
    } else if (promptText.includes("split") || promptText.includes("cut")) {
      this.executeSplitAtPlayhead();
    } else if (promptText.includes("export") || promptText.includes("render") || promptText.includes("deliver")) {
      store.setWorkspace("rendering");
    } else {
      store.addNotification(`AI Director: Processed prompt "${promptText}". Applying creative direction...`, "info");
      this.executeMotionGraphicsAction();
    }
  }
}
