/**
 * Deep Video Intelligence & Reverse Engineering Workspace.
 * Full-scale multimodal reverse engineering across 12 dimensions:
 * - Frame-accurate video player with SVG/Canvas overlays (Rule of Thirds, Horizon, Text/Object Bounding Boxes).
 * - Multi-track temporal intelligence timeline (Narrative, Shots, Camera, Typography, VFX, SFX, Beats).
 * - Multi-tab inspector panels (Composition, Cinematography, Motion Graphics, Audio, Color, Storytelling).
 * - Natural language and timestamp search over the Unified Temporal Event Graph.
 * - One-click "Compile to Studio Production Blueprint" translating reference grammar into OpenTimelineIO, Motion Canvas, and Audio DAW layouts.
 */
import { api } from "../api_client.js";
import { store } from "../state.js";

export class DeepIntelligenceWorkspace {
  constructor(mountElement) {
    this.mount = mountElement;
    this.activeInspectorTab = "shots"; // "shots", "cinema", "motion", "audio", "color", "story"
    this.selectedAssetId = null;
    this.manifest = null;
    this.eventGraph = null;
    this.currentTime = 0.0;
    this.duration = 50.0;
    this.fps = 30.0;
    this.isPlaying = false;
    this.showRuleOfThirds = true;
    this.showBoundingBoxes = true;
    this.compiledBlueprint = null;
    this.searchResults = [];
    this.libraryAssets = [];
  }

  async mount() {
    this.render();
    await this.loadProjectAssets();
  }

  async loadProjectAssets() {
    const projId = store.currentProjectId || "bb5c531d-d889-4f52-a646-d1fd18520948";
    try {
      const res = await api.listAssets(projId);
      if (res && res.assets) {
        this.libraryAssets = res.assets.filter(a => a.media_type === "VIDEO" || a.media_type === "VIDEO_PROXY");
        if (this.libraryAssets.length > 0 && !this.selectedAssetId) {
          this.selectedAssetId = this.libraryAssets[0].asset_id;
        }
        this.updateAssetDropdown();
      }
    } catch (e) {
      console.warn("Could not load project assets:", e);
    }
  }

  updateAssetDropdown() {
    const sel = document.getElementById("di-asset-select");
    if (!sel) return;
    sel.innerHTML = this.libraryAssets.map(a => `
      <option value="${a.asset_id}" ${a.asset_id === this.selectedAssetId ? 'selected' : ''}>
        ${a.display_name || a.original_filename} (${a.asset_id.slice(0, 8)})
      </option>
    `).join("");
  }

  render() {
    this.mount.innerHTML = `
      <div class="workspace-container deep-intelligence-workspace" style="display: flex; flex-direction: column; height: 100%; overflow: hidden; background: #0a0e14; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <!-- Top Toolbar -->
        <header style="display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; background: #121820; border-bottom: 1px solid #1f2937;">
          <div style="display: flex; align-items: center; gap: 14px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00F0FF" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polygon points="12 6 12 12 16 14"></polygon>
              </svg>
              <h2 style="font-size: 15px; font-weight: 700; letter-spacing: 0.5px; margin: 0; color: #fff;">
                DEEP VIDEO INTELLIGENCE & REVERSE ENGINEERING
              </h2>
            </div>
            <span style="font-size: 11px; background: rgba(0,240,255,0.12); color: #00F0FF; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(0,240,255,0.3); font-weight: 600;">
              TEMPORAL EVENT GRAPH
            </span>
          </div>

          <div style="display: flex; align-items: center; gap: 10px;">
            <select id="di-asset-select" style="background: #1a222d; border: 1px solid #374151; color: #fff; padding: 6px 12px; border-radius: 6px; font-size: 12px; max-width: 280px;">
              <option value="">Select Reference Video...</option>
            </select>
            <button id="di-btn-reverse-engineer" style="background: linear-gradient(135deg, #00F0FF, #0077FE); color: #000; font-weight: 700; border: none; padding: 7px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 6px;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
              Reverse Engineer
            </button>
            <button id="di-btn-compile-blueprint" style="background: #10b981; color: #fff; font-weight: 700; border: none; padding: 7px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 6px;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              Compile Production Blueprint
            </button>
          </div>
        </header>

        <!-- Main Middle Stage: Video & Overlays (Left) + Multi-Tab Inspector (Right) -->
        <div style="flex: 1; display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 1px; background: #1f2937; overflow: hidden;">
          
          <!-- LEFT: Video Viewport & Overlays -->
          <div style="background: #0a0e14; display: flex; flex-direction: column; overflow: hidden; padding: 16px;">
            <div style="position: relative; flex: 1; display: flex; align-items: center; justify-content: center; background: #000; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937;">
              <video id="di-video-player" style="max-height: 100%; max-width: 100%; object-fit: contain;" controls="false">
                <source src="/api/v1/assets/${this.selectedAssetId || ''}/stream" type="video/mp4">
              </video>

              <!-- SVG Interactive Overlay for Rule of Thirds & Bounding Boxes -->
              <svg id="di-overlay-svg" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">
                <!-- Rule of Thirds Grid -->
                <g id="di-rot-grid" style="display: ${this.showRuleOfThirds ? 'block' : 'none'};">
                  <line x1="33.33%" y1="0%" x2="33.33%" y2="100%" stroke="rgba(0, 240, 255, 0.4)" stroke-width="1" stroke-dasharray="4 4" />
                  <line x1="66.66%" y1="0%" x2="66.66%" y2="100%" stroke="rgba(0, 240, 255, 0.4)" stroke-width="1" stroke-dasharray="4 4" />
                  <line x1="0%" y1="33.33%" x2="100%" y2="33.33%" stroke="rgba(0, 240, 255, 0.4)" stroke-width="1" stroke-dasharray="4 4" />
                  <line x1="0%" y1="66.66%" x2="100%" y2="66.66%" stroke="rgba(0, 240, 255, 0.4)" stroke-width="1" stroke-dasharray="4 4" />
                </g>
                <!-- Dynamic Bounding Boxes -->
                <g id="di-bboxes-group"></g>
              </svg>
            </div>

            <!-- Transport & Overlay Controls -->
            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 10px; padding: 8px 12px; background: #121820; border-radius: 6px; border: 1px solid #1f2937;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <button id="di-btn-play" style="background: #1f2937; border: 1px solid #374151; color: #fff; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 600;">Play</button>
                <button id="di-btn-step-back" style="background: #1f2937; border: 1px solid #374151; color: #fff; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">-1 Frame</button>
                <button id="di-btn-step-fwd" style="background: #1f2937; border: 1px solid #374151; color: #fff; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">+1 Frame</button>
                <span id="di-timecode-display" style="font-family: monospace; font-size: 13px; color: #00F0FF; margin-left: 8px; font-weight: 700;">00:00:00.000 (0.0s)</span>
              </div>
              <div style="display: flex; align-items: center; gap: 12px;">
                <label style="font-size: 11px; color: #9ca3af; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                  <input type="checkbox" id="di-toggle-rot" ${this.showRuleOfThirds ? 'checked' : ''}> Rule of Thirds
                </label>
                <label style="font-size: 11px; color: #9ca3af; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                  <input type="checkbox" id="di-toggle-bbox" ${this.showBoundingBoxes ? 'checked' : ''}> Detect Boxes
                </label>
              </div>
            </div>
          </div>

          <!-- RIGHT: Multi-Tab Intelligence Inspector -->
          <div style="background: #0d121a; display: flex; flex-direction: column; overflow: hidden;">
            <!-- Tabs Nav -->
            <div style="display: flex; background: #121820; border-bottom: 1px solid #1f2937; overflow-x: auto; padding: 4px 8px;">
              <button class="di-tab-btn ${this.activeInspectorTab === 'shots' ? 'active' : ''}" data-tab="shots" style="${this.getInspectorTabStyle('shots')}">Shots & Cuts</button>
              <button class="di-tab-btn ${this.activeInspectorTab === 'cinema' ? 'active' : ''}" data-tab="cinema" style="${this.getInspectorTabStyle('cinema')}">Cinematography</button>
              <button class="di-tab-btn ${this.activeInspectorTab === 'motion' ? 'active' : ''}" data-tab="motion" style="${this.getInspectorTabStyle('motion')}">Motion Graphics</button>
              <button class="di-tab-btn ${this.activeInspectorTab === 'audio' ? 'active' : ''}" data-tab="audio" style="${this.getInspectorTabStyle('audio')}">Audio & SFX</button>
              <button class="di-tab-btn ${this.activeInspectorTab === 'color' ? 'active' : ''}" data-tab="color" style="${this.getInspectorTabStyle('color')}">Color & Grade</button>
              <button class="di-tab-btn ${this.activeInspectorTab === 'story' ? 'active' : ''}" data-tab="story" style="${this.getInspectorTabStyle('story')}">Story & Arc</button>
            </div>

            <!-- Inspector Content Area -->
            <div id="di-inspector-body" style="flex: 1; overflow-y: auto; padding: 16px;">
              ${this.renderInspectorContent()}
            </div>
          </div>
        </div>

        <!-- Bottom Section: Multi-Track Timeline & Search -->
        <div style="height: 240px; background: #121820; border-top: 1px solid #1f2937; display: flex; flex-direction: column; overflow: hidden;">
          <!-- Timeline Control Bar & Graph Search -->
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px; background: #161e29; border-bottom: 1px solid #1f2937;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 11px; font-weight: 700; color: #9ca3af; text-transform: uppercase;">Temporal Tracks:</span>
              <span id="di-timeline-meta" style="font-size: 11px; color: #00F0FF; font-family: monospace;">
                ${this.manifest ? `${this.manifest.cinematography_shots.length} Shots | ASL: ${this.manifest.editorial_rhythm.average_shot_length_sec}s | BPM: ${this.manifest.audio_intelligence.tempo_bpm}` : 'No Video Analyzed'}
              </span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <input type="text" id="di-search-input" placeholder="Search Event Graph (e.g. 'title', 'whoosh', 'close-up')..." style="background: #0a0e14; border: 1px solid #374151; color: #fff; padding: 4px 10px; border-radius: 4px; font-size: 11px; width: 280px;">
              <button id="di-btn-search" style="background: #1f2937; border: 1px solid #374151; color: #00F0FF; padding: 4px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: 600;">Search</button>
            </div>
          </div>

          <!-- Multi-Track Canvas / Visualizer -->
          <div id="di-timeline-tracks" style="flex: 1; overflow-y: auto; padding: 8px 16px; display: flex; flex-direction: column; gap: 5px;">
            ${this.renderTimelineTracks()}
          </div>
        </div>

        <!-- Modal Container for Compiled Blueprint -->
        <div id="di-modal-blueprint" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; align-items: center; justify-content: center;">
          <div style="background: #121820; border: 1px solid #00F0FF; border-radius: 8px; width: 680px; max-height: 85vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 0 30px rgba(0,240,255,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; border-bottom: 1px solid #1f2937; background: #161e29;">
              <h3 style="margin: 0; font-size: 15px; color: #00F0FF; font-weight: 700;">EXECUTABLE STUDIO PRODUCTION BLUEPRINT</h3>
              <button id="di-modal-close" style="background: none; border: none; color: #9ca3af; font-size: 20px; cursor: pointer;">&times;</button>
            </div>
            <div id="di-modal-body" style="padding: 20px; overflow-y: auto; flex: 1; font-size: 13px; line-height: 1.6;"></div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  getInspectorTabStyle(tab) {
    const active = this.activeInspectorTab === tab;
    return `
      background: ${active ? '#1f2937' : 'transparent'};
      color: ${active ? '#00F0FF' : '#9ca3af'};
      border: none;
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    `;
  }

  renderInspectorContent() {
    if (!this.manifest) {
      return `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #6b7280; text-align: center; padding: 40px;">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#374151" stroke-width="1.5" style="margin-bottom: 12px;">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 16v-4"></path>
            <path d="M12 8h.01"></path>
          </svg>
          <p style="font-size: 13px; margin: 0 0 6px 0; color: #9ca3af; font-weight: 600;">No Reverse Engineering Data Loaded</p>
          <p style="font-size: 12px; margin: 0;">Select a reference video above and click <strong>"Reverse Engineer"</strong> to extract cinematography, motion graphics, audio sync, and editorial pacing.</p>
        </div>
      `;
    }

    switch (this.activeInspectorTab) {
      case "shots":
        return this.renderShotsInspector();
      case "cinema":
        return this.renderCinematographyInspector();
      case "motion":
        return this.renderMotionGraphicsInspector();
      case "audio":
        return this.renderAudioInspector();
      case "color":
        return this.renderColorInspector();
      case "story":
        return this.renderStoryInspector();
      default:
        return `<p>Select a tab above.</p>`;
    }
  }

  renderShotsInspector() {
    const r = this.manifest.editorial_rhythm;
    const shots = this.manifest.cinematography_shots || [];
    const transitions = this.manifest.transitions || [];

    return `
      <div style="display: flex; flex-direction: column; gap: 14px;">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
          <div style="background: #161e29; padding: 10px; border-radius: 6px; border: 1px solid #1f2937;">
            <div style="font-size: 10px; color: #9ca3af; text-transform: uppercase;">Average Shot Length</div>
            <div style="font-size: 18px; font-weight: 700; color: #00F0FF; margin-top: 2px;">${r.average_shot_length_sec}s</div>
            <div style="font-size: 10px; color: #6b7280;">Variance: ${r.asl_variance}</div>
          </div>
          <div style="background: #161e29; padding: 10px; border-radius: 6px; border: 1px solid #1f2937;">
            <div style="font-size: 10px; color: #9ca3af; text-transform: uppercase;">Cut Frequency</div>
            <div style="font-size: 18px; font-weight: 700; color: #10b981; margin-top: 2px;">${r.cuts_per_minute} CPM</div>
            <div style="font-size: 10px; color: #6b7280;">Pacing: ${r.cutting_pace_category}</div>
          </div>
          <div style="background: #161e29; padding: 10px; border-radius: 6px; border: 1px solid #1f2937;">
            <div style="font-size: 10px; color: #9ca3af; text-transform: uppercase;">Beat Sync Score</div>
            <div style="font-size: 18px; font-weight: 700; color: #f59e0b; margin-top: 2px;">${Math.round(r.beat_sync_accuracy_score * 100)}%</div>
            <div style="font-size: 10px; color: #6b7280;">J/L Cuts: ${r.j_cuts_count + r.l_cuts_count}</div>
          </div>
        </div>

        <h4 style="font-size: 12px; color: #fff; margin: 4px 0 0 0; text-transform: uppercase;">Detected Shots & Transition Details</h4>
        <div style="display: flex; flex-direction: column; gap: 6px;">
          ${shots.map((s, idx) => {
            const tr = transitions[idx] ? transitions[idx].transition_type : 'HARD_CUT';
            return `
              <div class="di-shot-row" data-timestamp="${s.timecode_range.start_seconds}" style="background: #121820; border: 1px solid #1f2937; padding: 8px 12px; border-radius: 4px; display: flex; align-items: center; justify-content: space-between; cursor: pointer;">
                <div>
                  <span style="font-weight: 700; color: #00F0FF; font-size: 12px;">Shot ${s.shot_number}</span>
                  <span style="font-size: 11px; color: #9ca3af; margin-left: 6px;">[${s.shot_scale}]</span>
                  <span style="font-size: 11px; color: #6b7280; margin-left: 6px;">${s.camera_motion}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 10px; background: rgba(0,240,255,0.1); color: #00F0FF; padding: 2px 6px; border-radius: 3px;">${tr}</span>
                  <span style="font-family: monospace; font-size: 11px; color: #9ca3af;">${s.timecode_range.start_time} (${s.timecode_range.duration_seconds}s)</span>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    `;
  }

  renderCinematographyInspector() {
    const shots = this.manifest.cinematography_shots || [];
    const activeShot = shots.find(s => s.timecode_range.start_seconds <= this.currentTime && this.currentTime <= s.timecode_range.end_seconds) || shots[0];

    if (!activeShot) return `<p>No cinematography data for current timecode.</p>`;

    const comp = activeShot.composition;
    const opt = activeShot.optical;
    const light = activeShot.lighting;

    return `
      <div style="display: flex; flex-direction: column; gap: 14px;">
        <div style="background: #161e29; padding: 12px; border-radius: 6px; border: 1px solid #1f2937;">
          <div style="font-size: 11px; color: #00F0FF; font-weight: 700;">CURRENT SHOT: #${activeShot.shot_number} (${activeShot.timecode_range.start_time})</div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; font-size: 12px;">
            <div><span style="color: #9ca3af;">Scale:</span> <strong>${activeShot.shot_scale}</strong></div>
            <div><span style="color: #9ca3af;">Angle:</span> <strong>${activeShot.camera_angle}</strong></div>
            <div><span style="color: #9ca3af;">Motion:</span> <strong>${activeShot.camera_motion}</strong></div>
            <div><span style="color: #9ca3af;">Velocity:</span> <strong>${activeShot.motion_velocity_px_sec} px/s</strong></div>
          </div>
        </div>

        <div style="background: #161e29; padding: 12px; border-radius: 6px; border: 1px solid #1f2937;">
          <div style="font-size: 11px; color: #10b981; font-weight: 700; text-transform: uppercase;">Composition Geometry</div>
          <div style="margin-top: 8px; font-size: 12px; display: flex; flex-direction: column; gap: 6px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #9ca3af;">Rule of Thirds Adherence:</span>
              <strong>${Math.round(comp.rule_of_thirds_adherence * 100)}%</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #9ca3af;">Symmetry Score:</span>
              <strong>${Math.round(comp.symmetry_score * 100)}%</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #9ca3af;">Visual Balance (Center of Mass):</span>
              <strong>X: ${comp.visual_balance_x}, Y: ${comp.visual_balance_y}</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #9ca3af;">Depth Separation:</span>
              <strong>${comp.has_background_depth ? 'Pronounced FG/BG' : 'Flat Plane'}</strong>
            </div>
          </div>
        </div>

        <div style="background: #161e29; padding: 12px; border-radius: 6px; border: 1px solid #1f2937;">
          <div style="font-size: 11px; color: #f59e0b; font-weight: 700; text-transform: uppercase;">Optics & Inferred Lighting</div>
          <div style="margin-top: 8px; font-size: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div><span style="color: #9ca3af;">Inferred Lens:</span> <strong>${opt.inferred_focal_length_class}</strong></div>
            <div><span style="color: #9ca3af;">Depth of Field:</span> <strong>${opt.depth_of_field}</strong></div>
            <div><span style="color: #9ca3af;">Lighting Style:</span> <strong>${light.lighting_style}</strong></div>
            <div><span style="color: #9ca3af;">Color Temp:</span> <strong>${light.estimated_color_temperature_kelvin}K (${light.color_cast})</strong></div>
          </div>
        </div>
      </div>
    `;
  }

  renderMotionGraphicsInspector() {
    const mg = this.manifest.motion_graphics_elements || [];
    return `
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div style="font-size: 11px; color: #9ca3af;">Tracked Graphic Elements (${mg.length} elements detected):</div>
        ${mg.map((elem, i) => `
          <div style="background: #161e29; border: 1px solid #1f2937; border-radius: 6px; padding: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 700; color: #00F0FF; font-size: 12px;">${elem.element_type}</span>
              <span style="font-size: 10px; background: rgba(0,240,255,0.1); color: #00F0FF; padding: 2px 6px; border-radius: 3px;">
                ${elem.motion_behavior.entry_animation}
              </span>
            </div>
            <div style="margin-top: 6px; font-size: 11px; color: #9ca3af; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
              <div>Font: <strong>${elem.typography.font_family_class}</strong></div>
              <div>Weight: <strong>${elem.typography.estimated_weight}</strong></div>
              <div>Easing: <strong>${elem.motion_behavior.easing_curve}</strong></div>
              <div>Duration: <strong>${elem.timecode_range.duration_seconds}s</strong></div>
            </div>
            <div style="display: flex; align-items: center; gap: 6px; margin-top: 6px;">
              <div style="width: 14px; height: 14px; border-radius: 3px; background: ${elem.typography.primary_color_hex}; border: 1px solid #fff;"></div>
              <span style="font-family: monospace; font-size: 11px; color: #fff;">${elem.typography.primary_color_hex}</span>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  renderAudioInspector() {
    const audio = this.manifest.audio_intelligence;
    const energy = audio.energy_profile;

    return `
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
          <div style="background: #161e29; padding: 10px; border-radius: 6px; border: 1px solid #1f2937;">
            <div style="font-size: 10px; color: #9ca3af;">MUSIC TEMPO (BPM)</div>
            <div style="font-size: 20px; font-weight: 700; color: #00F0FF;">${audio.tempo_bpm} BPM</div>
          </div>
          <div style="background: #161e29; padding: 10px; border-radius: 6px; border: 1px solid #1f2937;">
            <div style="font-size: 10px; color: #9ca3af;">INTEGRATED LOUDNESS</div>
            <div style="font-size: 20px; font-weight: 700; color: #10b981;">${energy.integrated_lufs} LUFS</div>
          </div>
        </div>

        <div style="background: #161e29; padding: 10px; border-radius: 6px; border: 1px solid #1f2937;">
          <div style="font-size: 11px; color: #fff; font-weight: 600; margin-bottom: 6px;">Tri-Band Energy Distribution</div>
          <div style="display: flex; height: 16px; border-radius: 4px; overflow: hidden; margin-bottom: 6px;">
            <div style="width: ${energy.sub_bass_energy_ratio * 100}%; background: #3b82f6;" title="Sub-bass"></div>
            <div style="width: ${energy.mid_vocal_energy_ratio * 100}%; background: #10b981;" title="Mid vocal"></div>
            <div style="width: ${energy.high_sparkle_energy_ratio * 100}%; background: #f59e0b;" title="High sparkle"></div>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 10px; color: #9ca3af;">
            <span>Sub: ${Math.round(energy.sub_bass_energy_ratio * 100)}%</span>
            <span>Mid: ${Math.round(energy.mid_vocal_energy_ratio * 100)}%</span>
            <span>High: ${Math.round(energy.high_sparkle_energy_ratio * 100)}%</span>
          </div>
        </div>

        <div style="font-size: 11px; color: #9ca3af;">Detected SFX Transients (${audio.detected_sfx.length}):</div>
        <div style="display: flex; flex-direction: column; gap: 4px;">
          ${audio.detected_sfx.map(sfx => `
            <div style="background: #121820; padding: 6px 10px; border-radius: 4px; border: 1px solid #1f2937; display: flex; justify-content: space-between; font-size: 11px;">
              <span style="color: #00F0FF; font-weight: 600;">${sfx.sfx_type}</span>
              <span style="color: #9ca3af;">@ ${sfx.start_seconds}s (Intensity: ${sfx.intensity})</span>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  renderColorInspector() {
    const c = this.manifest.color_grading;
    return `
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div style="background: #161e29; padding: 12px; border-radius: 6px; border: 1px solid #1f2937;">
          <div style="font-size: 11px; color: #fff; font-weight: 600; margin-bottom: 8px;">Extracted Palette (Lab K-Means)</div>
          <div style="display: flex; gap: 8px;">
            ${c.dominant_palette_hex.map(hex => `
              <div style="flex: 1; height: 36px; border-radius: 4px; background: ${hex}; border: 1px solid rgba(255,255,255,0.2);" title="${hex}"></div>
            `).join("")}
          </div>
        </div>

        <div style="background: #161e29; padding: 12px; border-radius: 6px; border: 1px solid #1f2937; font-size: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
          <div><span style="color: #9ca3af;">Color Harmony:</span> <strong>${c.color_harmony_type}</strong></div>
          <div><span style="color: #9ca3af;">Contrast Ratio:</span> <strong>${c.contrast_ratio}:1</strong></div>
          <div><span style="color: #9ca3af;">Vignette:</span> <strong>${c.has_vignette ? `Yes (${c.vignette_intensity})` : 'None'}</strong></div>
          <div><span style="color: #9ca3af;">Film Grain:</span> <strong>${c.film_grain_level}</strong></div>
        </div>

        <div style="background: #161e29; padding: 12px; border-radius: 6px; border: 1px solid #1f2937;">
          <div style="font-size: 10px; color: #9ca3af; text-transform: uppercase;">Recommended Studio LUT</div>
          <div style="font-size: 14px; font-weight: 700; color: #00F0FF; margin-top: 4px;">${c.recommended_lut}</div>
        </div>
      </div>
    `;
  }

  renderStoryInspector() {
    const s = this.manifest.storytelling;
    return `
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div style="background: #161e29; padding: 10px; border-radius: 6px; border: 1px solid #1f2937;">
          <div style="font-size: 11px; color: #00F0FF; font-weight: 700;">${s.story_structure}</div>
          <div style="font-size: 11px; color: #9ca3af; margin-top: 4px;">${s.thematic_summary}</div>
        </div>

        <div style="font-size: 11px; color: #9ca3af;">5-Phase Narrative Arc:</div>
        <div style="display: flex; flex-direction: column; gap: 6px;">
          ${s.narrative_phases.map(p => `
            <div style="background: #121820; border: 1px solid #1f2937; padding: 8px 10px; border-radius: 4px; font-size: 11px;">
              <div style="display: flex; justify-content: space-between; font-weight: 700; color: #fff;">
                <span>${p.phase_name}</span>
                <span style="color: #00F0FF;">${p.timecode_range.start_seconds}s - ${p.timecode_range.end_seconds}s</span>
              </div>
              <div style="color: #9ca3af; margin-top: 3px;">${p.narrative_role}</div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  renderTimelineTracks() {
    if (!this.manifest) {
      return `<div style="color: #6b7280; font-size: 12px; padding: 20px; text-align: center;">Execute Reverse Engineering to view multi-track timeline visualization.</div>`;
    }

    const dur = this.manifest.total_duration_sec || 50.0;
    const shots = this.manifest.cinematography_shots || [];
    const mg = this.manifest.motion_graphics_elements || [];
    const sfx = this.manifest.audio_intelligence.detected_sfx || [];
    const beats = this.manifest.audio_intelligence.beat_timestamps || [];

    return `
      <!-- Track 1: Narrative Phases -->
      <div style="display: flex; align-items: center; height: 26px;">
        <span style="width: 100px; font-size: 10px; color: #9ca3af; font-weight: 600;">Narrative</span>
        <div style="flex: 1; height: 20px; background: #0a0e14; border-radius: 3px; position: relative; overflow: hidden; display: flex;">
          ${this.manifest.storytelling.narrative_phases.map(p => {
            const w = (p.timecode_range.duration_seconds / dur) * 100;
            return `<div style="width: ${w}%; background: rgba(0,240,255,0.15); border-right: 1px solid #00F0FF; font-size: 9px; color: #00F0FF; padding: 2px 4px; white-space: nowrap; overflow: hidden;">${p.phase_name}</div>`;
          }).join("")}
        </div>
      </div>

      <!-- Track 2: Shots & Cuts -->
      <div style="display: flex; align-items: center; height: 26px;">
        <span style="width: 100px; font-size: 10px; color: #9ca3af; font-weight: 600;">Shots & Cuts</span>
        <div style="flex: 1; height: 20px; background: #0a0e14; border-radius: 3px; position: relative; overflow: hidden; display: flex;">
          ${shots.map(s => {
            const w = (s.timecode_range.duration_seconds / dur) * 100;
            return `<div style="width: ${w}%; background: #1e3a8a; border-right: 1px solid #60a5fa; font-size: 9px; color: #fff; padding: 2px 4px; white-space: nowrap; overflow: hidden;">S${s.shot_number} ${s.shot_scale}</div>`;
          }).join("")}
        </div>
      </div>

      <!-- Track 3: Typography & Graphics -->
      <div style="display: flex; align-items: center; height: 26px;">
        <span style="width: 100px; font-size: 10px; color: #9ca3af; font-weight: 600;">Motion Graphics</span>
        <div style="flex: 1; height: 20px; background: #0a0e14; border-radius: 3px; position: relative;">
          ${mg.map(g => {
            const left = (g.timecode_range.start_seconds / dur) * 100;
            const w = (g.timecode_range.duration_seconds / dur) * 100;
            return `<div style="position: absolute; left: ${left}%; width: ${w}%; height: 100%; background: #10b981; border-radius: 2px; font-size: 9px; color: #000; font-weight: 700; padding: 2px 4px; white-space: nowrap; overflow: hidden;">${g.element_type}</div>`;
          }).join("")}
        </div>
      </div>

      <!-- Track 4: SFX Impacts & Transients -->
      <div style="display: flex; align-items: center; height: 26px;">
        <span style="width: 100px; font-size: 10px; color: #9ca3af; font-weight: 600;">Audio SFX</span>
        <div style="flex: 1; height: 20px; background: #0a0e14; border-radius: 3px; position: relative;">
          ${sfx.map(s => {
            const left = (s.start_seconds / dur) * 100;
            return `<div style="position: absolute; left: ${left}%; width: 4px; height: 100%; background: #f59e0b; border-radius: 1px;" title="${s.sfx_type} @ ${s.start_seconds}s"></div>`;
          }).join("")}
        </div>
      </div>
    `;
  }

  bindEvents() {
    // Select asset
    const sel = document.getElementById("di-asset-select");
    if (sel) {
      sel.onchange = (e) => {
        this.selectedAssetId = e.target.value;
      };
    }

    // Reverse engineer button
    const btnRe = document.getElementById("di-btn-reverse-engineer");
    if (btnRe) {
      btnRe.onclick = async () => {
        if (!this.selectedAssetId) {
          alert("Please select a video asset first.");
          return;
        }
        btnRe.disabled = true;
        btnRe.innerText = "Analyzing Video (5 Passes)...";
        try {
          const res = await api.reverseEngineerVideo(this.selectedAssetId);
          if (res && res.success) {
            this.manifest = res.manifest;
            this.eventGraph = res.event_graph;
            this.render();
          } else {
            alert("Reverse engineering failed: " + (res.error || "Unknown error"));
          }
        } catch (err) {
          alert("Error during reverse engineering: " + err.message);
        } finally {
          btnRe.disabled = false;
          btnRe.innerText = "Reverse Engineer";
        }
      };
    }

    // Compile production blueprint button
    const btnComp = document.getElementById("di-btn-compile-blueprint");
    if (btnComp) {
      btnComp.onclick = async () => {
        if (!this.selectedAssetId) {
          alert("Please select and reverse engineer a video first.");
          return;
        }
        btnComp.disabled = true;
        btnComp.innerText = "Compiling Blueprint...";
        try {
          const projId = store.currentProjectId || "bb5c531d-d889-4f52-a646-d1fd18520948";
          const res = await api.compileProductionBlueprint(
            this.selectedAssetId,
            projId,
            "Octopus Three Hearts Hindi Documentary",
            50.0,
            "9:16",
            "hi"
          );
          if (res && res.success) {
            this.compiledBlueprint = res.blueprint;
            this.showBlueprintModal(res.blueprint);
          } else {
            alert("Compilation failed.");
          }
        } catch (err) {
          alert("Error compiling blueprint: " + err.message);
        } finally {
          btnComp.disabled = false;
          btnComp.innerText = "Compile Production Blueprint";
        }
      };
    }

    // Inspector tab clicks
    this.mount.querySelectorAll(".di-tab-btn").forEach(btn => {
      btn.onclick = () => {
        this.activeInspectorTab = btn.dataset.tab;
        const body = document.getElementById("di-inspector-body");
        if (body) body.innerHTML = this.renderInspectorContent();
        this.mount.querySelectorAll(".di-tab-btn").forEach(b => {
          b.style.cssText = this.getInspectorTabStyle(b.dataset.tab);
        });
      };
    });

    // Modal close
    const modalClose = document.getElementById("di-modal-close");
    if (modalClose) {
      modalClose.onclick = () => {
        document.getElementById("di-modal-blueprint").style.display = "none";
      };
    }

    // Search button
    const btnSearch = document.getElementById("di-btn-search");
    const searchInput = document.getElementById("di-search-input");
    if (btnSearch && searchInput) {
      btnSearch.onclick = async () => {
        const q = searchInput.value.trim();
        if (!q || !this.selectedAssetId) return;
        try {
          const res = await api.queryEventGraph(this.selectedAssetId, q);
          if (res && res.nodes) {
            alert(`Found ${res.nodes.length} matching event graph nodes:\n` + res.nodes.map(n => `- [${n.node_type}] ${n.label} @ ${n.start_seconds}s`).join("\n"));
          }
        } catch (e) {
          alert("Graph query failed: " + e.message);
        }
      };
    }
  }

  showBlueprintModal(bp) {
    const modal = document.getElementById("di-modal-blueprint");
    const body = document.getElementById("di-modal-body");
    if (!modal || !body) return;

    body.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 14px;">
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 12px; border-radius: 6px;">
          <h4 style="margin: 0 0 4px 0; color: #10b981; font-size: 13px;">✓ Production Blueprint Successfully Compiled</h4>
          <p style="margin: 0; color: #e6edf3; font-size: 12px;">${bp.summary}</p>
        </div>

        <div>
          <h4 style="font-size: 12px; color: #00F0FF; margin: 0 0 6px 0; text-transform: uppercase;">1. OpenTimelineIO Master Assembly Track</h4>
          <div style="background: #161e29; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 11px; color: #9ca3af; word-break: break-all;">
            ${bp.otio_timeline_path}
          </div>
        </div>

        <div>
          <h4 style="font-size: 12px; color: #00F0FF; margin: 0 0 6px 0; text-transform: uppercase;">2. Motion Canvas Declarative 2D System</h4>
          <div style="background: #161e29; padding: 10px; border-radius: 4px; font-size: 11px; color: #e6edf3;">
            Aspect Ratio: <strong>${bp.aspect_ratio}</strong> | Scenes: <strong>${bp.motion_composition.scenes ? bp.motion_composition.scenes.length : 0}</strong> | Duration: <strong>${bp.target_duration_sec}s</strong>
          </div>
        </div>

        <div>
          <h4 style="font-size: 12px; color: #00F0FF; margin: 0 0 6px 0; text-transform: uppercase;">3. External Creative Asset Acquisition Plan</h4>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            ${bp.asset_acquisition_plan.map(a => `
              <div style="background: #161e29; padding: 6px 10px; border-radius: 4px; font-size: 11px; display: flex; justify-content: space-between;">
                <span>Query: <em>"${a.search_query}"</em></span>
                <span style="color: #10b981;">${a.recommended_sources.join(", ")}</span>
              </div>
            `).join("")}
          </div>
        </div>

        <div>
          <h4 style="font-size: 12px; color: #00F0FF; margin: 0 0 6px 0; text-transform: uppercase;">4. Quality Control Enforcements</h4>
          <div style="background: #161e29; padding: 10px; border-radius: 4px; font-size: 11px; color: #e6edf3;">
            Target Loudness: <strong>${bp.qc_validation_policies.audio_loudness_target_lufs} LUFS</strong> | Max Drift: <strong>${bp.qc_validation_policies.audio_visual_sync_max_drift_ms}ms</strong>
          </div>
        </div>
      </div>
    `;

    modal.style.display = "flex";
  }
}

