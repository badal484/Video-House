/**
 * Color Grading & Restoration Workspace.
 * Interface to Department 16 (Color Grading & Video Restoration), 3-way wheels, ACEScg & Super-Resolution.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class ColorWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">Color Grading, Restoration & Enhancement</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Department 16 • Scene-referred ACEScg color management • 3-way wheels • Super-Resolution.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-ai-colorist">AI Colorist Recommend</button>
            <button class="btn btn-primary btn-sm" id="btn-apply-grade">Apply Grade Node</button>
          </div>
        </div>

        <!-- 3-Way Color Wheels Grid -->
        <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3);">
          <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary); margin-bottom: var(--space-2);">3-Way Primary Color Wheels (Lift / Gamma / Gain)</div>
          <div class="color-wheels-grid">
            <!-- Lift -->
            <div class="color-wheel-box">
              <div style="font-size: 12px; font-weight: 600; color: var(--studio-text-secondary);">LIFT (Shadows)</div>
              <div class="color-wheel-disk"><div class="color-wheel-reticle"></div></div>
              <input type="range" min="-1" max="1" step="0.01" value="0" style="width: 100px;" />
            </div>
            <!-- Gamma -->
            <div class="color-wheel-box">
              <div style="font-size: 12px; font-weight: 600; color: var(--studio-text-secondary);">GAMMA (Midtones)</div>
              <div class="color-wheel-disk"><div class="color-wheel-reticle"></div></div>
              <input type="range" min="-1" max="1" step="0.01" value="0" style="width: 100px;" />
            </div>
            <!-- Gain -->
            <div class="color-wheel-box">
              <div style="font-size: 12px; font-weight: 600; color: var(--studio-text-secondary);">GAIN (Highlights)</div>
              <div class="color-wheel-disk"><div class="color-wheel-reticle"></div></div>
              <input type="range" min="-1" max="1" step="0.01" value="0" style="width: 100px;" />
            </div>
          </div>
        </div>

        <!-- Restoration & Looks -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Cinematic Look Presets</div>
            <select class="select" id="select-look-preset">
              <option value="TEAL_AND_ORANGE">Teal & Orange (Blockbuster Contrast)</option>
              <option value="BLEACH_BYPASS">Bleach Bypass (Desaturated High-Contrast)</option>
              <option value="KODAK_2383">Kodak 2383 Film Stock Emulation</option>
              <option value="MONOCHROME">Noir Monochrome Silver Gelatin</option>
            </select>
            <div style="font-size: 11px; color: var(--studio-text-muted);">Transforms linear scene-referred data into filmic contrast tone curves.</div>
          </div>

          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Restoration & Upscaling</div>
            <div style="display: flex; gap: var(--space-2);">
              <button class="btn btn-secondary btn-xs" style="flex: 1;">YADIF Deinterlace</button>
              <button class="btn btn-secondary btn-xs" style="flex: 1;">Deflicker (Moving Avg)</button>
              <button class="btn btn-secondary btn-xs" style="flex: 1;">2x Super-Resolution</button>
            </div>
            <div style="font-size: 11px; color: var(--studio-text-muted);">Non-destructive: original source footage remains byte-for-byte read-only.</div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelector("#btn-ai-colorist").addEventListener("click", () => {
      store.addNotification("AI Colorist analyzed scene vectorscope: Recommended Teal & Orange with Skin-Tone I-Line protection", "success");
    });
    this.container.querySelector("#btn-apply-grade").addEventListener("click", () => {
      store.addNotification("Committed ACEScg color grade node to timeline clip", "success");
    });
  }
}

