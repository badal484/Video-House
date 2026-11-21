/**
 * Motion Graphics & Typography Workspace.
 * Interface to Department 09 (Motion Graphics) & Motion Canvas SVG Presets.
 */

import { store } from "../state.js";

export class MotionGraphicsWorkspace {
  constructor(container) {
    this.container = container;
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
            <button class="btn btn-primary btn-sm" id="btn-insert-motion-timeline">Insert to Timeline (V2)</button>
          </div>
        </div>

        <!-- Presets and Live Vector Canvas Preview -->
        <div style="display: grid; grid-template-columns: 280px 1fr 300px; gap: var(--space-4); flex: 1;">
          <!-- Presets Column -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Motion Presets</div>
            <div class="preset-card active" style="background: var(--studio-bg-hover); border: 1px solid var(--studio-accent-primary); border-radius: var(--radius-sm); padding: 8px; cursor: pointer;">
              <div style="font-weight: 600; font-size: 12px; color: var(--studio-accent-primary);">Kinetic Typography</div>
              <div style="font-size: 10px; color: var(--studio-text-muted);">Word-by-word tracking reveal</div>
            </div>
            <div class="preset-card" style="background: var(--studio-bg-panel-elevated); border: 1px solid var(--studio-border-default); border-radius: var(--radius-sm); padding: 8px; cursor: pointer;">
              <div style="font-weight: 600; font-size: 12px;">Documentary Lower Third</div>
              <div style="font-size: 10px; color: var(--studio-text-muted);">Clean horizontal line wipe</div>
            </div>
            <div class="preset-card" style="background: var(--studio-bg-panel-elevated); border: 1px solid var(--studio-border-default); border-radius: var(--radius-sm); padding: 8px; cursor: pointer;">
              <div style="font-weight: 600; font-size: 12px;">Technical HUD Overlay</div>
              <div style="font-size: 10px; color: var(--studio-text-muted);">Futuristic telemetry reticle</div>
            </div>
          </div>

          <!-- Live SVG Canvas -->
          <div style="background-color: #07080A; border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative;">
            <svg id="live-motion-svg" width="640" height="360" viewBox="0 0 1920 1080" style="background: transparent;">
              <g id="lyr_title" transform="translate(960, 500)">
                <text x="0" y="0" font-family="'JetBrains Mono', monospace" font-size="64" font-weight="bold" fill="#00F0FF" text-anchor="middle">UNIVERSAL AI VIDEO STUDIO</text>
              </g>
              <g id="lyr_subtitle" transform="translate(960, 580)">
                <text x="0" y="0" font-family="sans-serif" font-size="32" fill="#F3F4F6" text-anchor="middle">Next-Gen Autonomous Creative Production</text>
              </g>
            </svg>
          </div>

          <!-- Controls -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Typography Settings</div>
            <div>
              <label style="font-size: 10px; color: var(--studio-text-muted);">Title Text</label>
              <input type="text" class="input" id="motion-title-input" value="UNIVERSAL AI VIDEO STUDIO" />
            </div>
            <div>
              <label style="font-size: 10px; color: var(--studio-text-muted);">Subtitle Text</label>
              <input type="text" class="input" id="motion-sub-input" value="Next-Gen Autonomous Creative Production" />
            </div>
            <div>
              <label style="font-size: 10px; color: var(--studio-text-muted);">Accent Fill Color</label>
              <input type="color" value="#00F0FF" id="motion-color-input" style="width: 100%; height: 28px; background: transparent; border: none; cursor: pointer;" />
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    const titleInput = this.container.querySelector("#motion-title-input");
    const subInput = this.container.querySelector("#motion-sub-input");
    const colorInput = this.container.querySelector("#motion-color-input");
    const svg = this.container.querySelector("#live-motion-svg");

    const updateSVG = () => {
      svg.querySelector("#lyr_title text").textContent = titleInput.value;
      svg.querySelector("#lyr_title text").setAttribute("fill", colorInput.value);
      svg.querySelector("#lyr_subtitle text").textContent = subInput.value;
    };

    titleInput.addEventListener("input", updateSVG);
    subInput.addEventListener("input", updateSVG);
    colorInput.addEventListener("input", updateSVG);

    this.container.querySelector("#btn-insert-motion-timeline").addEventListener("click", () => {
      store.addNotification("Inserted Motion Canvas composition to timeline track V2", "success");
    });
  }
}
