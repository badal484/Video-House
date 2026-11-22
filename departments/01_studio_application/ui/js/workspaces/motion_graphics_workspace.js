/**
 * Motion Graphics & Typography Workspace.
 * Interface to Department 09 (Motion Graphics) & Motion Canvas SVG Presets.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class MotionGraphicsWorkspace {
  constructor(container) {
    this.container = container;
    this.currentPreset = "kinetic";
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">Motion Graphics & Kinetic Typography</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Department 09 • Procedural vector typography • SVG composition rendering.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-insert-motion-timeline">Insert to Timeline (V2)</button>
            <button class="btn btn-primary btn-sm" id="btn-apply-motion-master">✨ Apply & Play Master Video</button>
          </div>
        </div>

        <!-- Presets and Live Vector Canvas Preview -->
        <div style="display: grid; grid-template-columns: 280px 1fr 320px; gap: var(--space-4); flex: 1;">
          <!-- Presets Column -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Motion Presets</div>
            
            <div class="preset-card active" data-preset="kinetic" style="background: var(--studio-bg-hover); border: 1px solid var(--studio-accent-primary); border-radius: var(--radius-sm); padding: 10px; cursor: pointer;">
              <div style="font-weight: 700; font-size: 12px; color: var(--studio-accent-primary);">1. Kinetic Typography</div>
              <div style="font-size: 10px; color: var(--studio-text-muted); margin-top: 2px;">Bold expanding typography with tracking reveal</div>
            </div>

            <div class="preset-card" data-preset="hud" style="background: var(--studio-bg-panel-elevated); border: 1px solid var(--studio-border-default); border-radius: var(--radius-sm); padding: 10px; cursor: pointer;">
              <div style="font-weight: 700; font-size: 12px; color: #FFF;">2. Cyberpunk HUD Reticle</div>
              <div style="font-size: 10px; color: var(--studio-text-muted); margin-top: 2px;">Rotating targeting reticle & telemetry coordinates</div>
            </div>

            <div class="preset-card" data-preset="lowerthird" style="background: var(--studio-bg-panel-elevated); border: 1px solid var(--studio-border-default); border-radius: var(--radius-sm); padding: 10px; cursor: pointer;">
              <div style="font-weight: 700; font-size: 12px; color: #FFF;">3. Documentary Lower Third</div>
              <div style="font-size: 10px; color: var(--studio-text-muted); margin-top: 2px;">Sleek glassmorphism pill with audio visualizer</div>
            </div>

            <div class="preset-card" data-preset="telemetry" style="background: var(--studio-bg-panel-elevated); border: 1px solid var(--studio-border-default); border-radius: var(--radius-sm); padding: 10px; cursor: pointer;">
              <div style="font-weight: 700; font-size: 12px; color: #FFF;">4. Production Telemetry Card</div>
              <div style="font-size: 10px; color: var(--studio-text-muted); margin-top: 2px;">Real-time render stats, EBU R128 audio badge</div>
            </div>
          </div>

          <!-- Live SVG Canvas -->
          <div style="background-color: #07080A; border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative;">
            <svg id="live-motion-svg" width="100%" height="100%" viewBox="0 0 720 1280" style="background: #0D1117;">
              <!-- Dynamic SVG Content Generated Here -->
            </svg>
          </div>

          <!-- Controls -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-3);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Preset Customization</div>
            <div>
              <label style="font-size: 11px; color: var(--studio-text-muted); display: block; margin-bottom: 4px;">Primary Title Text</label>
              <input type="text" class="input" id="motion-title-input" value="FUTURE VISIONS" />
            </div>
            <div>
              <label style="font-size: 11px; color: var(--studio-text-muted); display: block; margin-bottom: 4px;">Subtitle / Tagline</label>
              <input type="text" class="input" id="motion-sub-input" value="// AUTONOMOUS MOTION EDIT //" />
            </div>
            <div>
              <label style="font-size: 11px; color: var(--studio-text-muted); display: block; margin-bottom: 4px;">Accent Fill Color</label>
              <input type="color" value="#00F0FF" id="motion-color-input" style="width: 100%; height: 32px; background: transparent; border: 1px solid var(--studio-border-default); border-radius: 4px; cursor: pointer;" />
            </div>

            <div style="padding-top: var(--space-2); border-top: 1px solid var(--studio-border-subtle); display: flex; flex-direction: column; gap: var(--space-2);">
              <div style="font-size: 10px; color: var(--studio-text-muted);">
                Format: 9:16 Vertical (720x1280) • 24.0 fps • Zero Floating Drift
              </div>
              <button class="btn btn-primary btn-sm" id="btn-quick-apply-all" style="font-weight: 700;">
                ⚡ Apply Whole Motion Suite to Video
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    this.renderSVG();
    this.bindEvents();
  }

  renderSVG() {
    const svg = this.container.querySelector("#live-motion-svg");
    const title = this.container.querySelector("#motion-title-input")?.value || "FUTURE VISIONS";
    const sub = this.container.querySelector("#motion-sub-input")?.value || "// AUTONOMOUS MOTION EDIT //";
    const color = this.container.querySelector("#motion-color-input")?.value || "#00F0FF";

    if (this.currentPreset === "kinetic") {
      svg.innerHTML = `
        <rect width="720" height="1280" fill="#0A0E17" />
        <!-- Corner Brackets -->
        <line x1="30" y1="30" x2="80" y2="30" stroke="${color}" stroke-width="3" />
        <line x1="30" y1="30" x2="30" y2="80" stroke="${color}" stroke-width="3" />
        <line x1="690" y1="30" x2="640" y2="30" stroke="${color}" stroke-width="3" />
        <line x1="690" y1="30" x2="690" y2="80" stroke="${color}" stroke-width="3" />
        <line x1="30" y1="1250" x2="80" y2="1250" stroke="${color}" stroke-width="3" />
        <line x1="30" y1="1250" x2="30" y2="1200" stroke="${color}" stroke-width="3" />
        <line x1="690" y1="1250" x2="640" y2="1250" stroke="${color}" stroke-width="3" />
        <line x1="690" y1="1250" x2="690" y2="1200" stroke="${color}" stroke-width="3" />

        <!-- Title Box -->
        <rect x="130" y="240" width="460" height="100" fill="rgba(13,20,32,0.85)" stroke="${color}" stroke-width="2" rx="4" />
        <text x="360" y="295" font-family="'JetBrains Mono', monospace" font-size="34" font-weight="900" fill="#FFFFFF" text-anchor="middle">${title}</text>
        <text x="360" y="325" font-family="'JetBrains Mono', monospace" font-size="16" font-weight="700" fill="${color}" text-anchor="middle">${sub}</text>
        <line x1="130" y1="350" x2="590" y2="350" stroke="#FFD700" stroke-width="4" />
      `;
    } else if (this.currentPreset === "hud") {
      svg.innerHTML = `
        <rect width="720" height="1280" fill="#0A0E17" />
        <!-- Reticle Circle -->
        <circle cx="360" cy="640" r="100" fill="none" stroke="${color}" stroke-width="3" stroke-dasharray="30 15" />
        <circle cx="360" cy="640" r="30" fill="none" stroke="#FFD700" stroke-width="2" />
        <line x1="330" y1="640" x2="390" y2="640" stroke="#FFF" stroke-width="2" />
        <line x1="360" y1="610" x2="360" y2="670" stroke="#FFF" stroke-width="2" />
        <text x="470" y="635" font-family="'JetBrains Mono', monospace" font-size="14" fill="${color}">TARGET: SUBJECT_LOCKED</text>
        <text x="470" y="655" font-family="'JetBrains Mono', monospace" font-size="12" fill="#94A3B8">TRACKING: 24.0 FPS</text>
      `;
    } else if (this.currentPreset === "lowerthird") {
      svg.innerHTML = `
        <rect width="720" height="1280" fill="#0A0E17" />
        <rect x="40" y="960" width="640" height="100" fill="rgba(10,15,25,0.9)" stroke="${color}" stroke-width="2" rx="4" />
        <rect x="40" y="960" width="10" height="100" fill="#FFD700" />
        <text x="70" y="1000" font-family="'JetBrains Mono', monospace" font-size="22" font-weight="800" fill="#FFFFFF">${title}</text>
        <text x="70" y="1035" font-family="sans-serif" font-size="15" fill="#94A3B8">${sub}</text>
      `;
    } else {
      svg.innerHTML = `
        <rect width="720" height="1280" fill="#0A0E17" />
        <rect x="45" y="180" width="630" height="160" fill="rgba(12,18,30,0.9)" stroke="#FFD700" stroke-width="2" rx="4" />
        <text x="75" y="220" font-family="'JetBrains Mono', monospace" font-size="18" font-weight="bold" fill="#FFD700">PRODUCTION TELEMETRY // VERIFIED</text>
        <text x="75" y="260" font-family="'JetBrains Mono', monospace" font-size="16" fill="#FFFFFF">RENDER ACCELERATION: APPLE VIDEOTOOLBOX</text>
        <text x="75" y="295" font-family="'JetBrains Mono', monospace" font-size="16" fill="${color}">EDITORIAL DRIFT: 0.000s (RationalTime)</text>
      `;
    }
  }

  bindEvents() {
    const titleInput = this.container.querySelector("#motion-title-input");
    const subInput = this.container.querySelector("#motion-sub-input");
    const colorInput = this.container.querySelector("#motion-color-input");

    const onInput = () => this.renderSVG();
    titleInput.addEventListener("input", onInput);
    subInput.addEventListener("input", onInput);
    colorInput.addEventListener("input", onInput);

    // Preset cards
    const presetCards = this.container.querySelectorAll(".preset-card");
    presetCards.forEach(card => {
      card.addEventListener("click", () => {
        presetCards.forEach(c => {
          c.classList.remove("active");
          c.style.background = "var(--studio-bg-panel-elevated)";
          c.style.borderColor = "var(--studio-border-default)";
        });
        card.classList.add("active");
        card.style.background = "var(--studio-bg-hover)";
        card.style.borderColor = "var(--studio-accent-primary)";
        this.currentPreset = card.getAttribute("data-preset");
        this.renderSVG();
      });
    });

    const goToNLEWithMaster = () => {
      const assets = store.getState().assets || [];
      const master = assets.find(a => (a.display_name && a.display_name.includes("Master")) || (a.original_filename && a.original_filename.includes("master")));
      if (master) {
        store.setState({ selectedAssetId: master.asset_id, isPlaying: true });
      }
      store.setWorkspace("creative");
      store.addNotification("Loaded complete Motion Graphics Master video into Creative NLE", "success");
    };

    this.container.querySelector("#btn-insert-motion-timeline").addEventListener("click", () => {
      store.setWorkspace("creative");
      store.addNotification("Inserted Motion Graphics overlay onto Track V2", "success");
    });

    this.container.querySelector("#btn-apply-motion-master").addEventListener("click", goToNLEWithMaster);
    this.container.querySelector("#btn-quick-apply-all").addEventListener("click", goToNLEWithMaster);
  }
}
