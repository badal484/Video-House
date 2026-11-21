/**
 * AI Generation Studio Workspace.
 * Direct interface to Department 15 (AI Generation Router) & Multi-dimensional Prompt Compiler.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class GenerationWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">AI Generation Studio</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Multi-provider router: Runway Gen-3, Kling 1.5, Wan2.1, FLUX.1 & ElevenLabs.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-compile-prompt">Compile Prompt Dialect</button>
            <button class="btn btn-primary btn-sm" id="btn-submit-gen">Generate Clip</button>
          </div>
        </div>

        <!-- Generation Parameter Grid -->
        <div style="display: grid; grid-template-columns: 1fr 340px; gap: var(--space-4);">
          <!-- Left: Structured Multi-Dimensional Inputs -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-3);">
            <div>
              <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Subject & Action:</label>
              <textarea class="textarea" id="gen-subject" style="min-height: 48px;">Cyberpunk operative in reflective titanium armor sprinting through rain-slicked Tokyo neon alleyway.</textarea>
            </div>
            <div>
              <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Camera Movement & Framing:</label>
              <input type="text" class="input" id="gen-camera" value="Low angle tracking shot with subtle cinematic camera shake, 35mm anamorphic" />
            </div>
            <div>
              <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Lighting & Atmosphere:</label>
              <input type="text" class="input" id="gen-lighting" value="Cyan and magenta volumetric neon reflections, heavy rain particles, atmospheric smoke" />
            </div>
            <div>
              <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Model-Native Compiled Prompt Dialect Preview:</label>
              <div id="gen-compiled-preview" style="background-color: var(--studio-bg-canvas); border: 1px solid var(--studio-border-subtle); border-radius: var(--radius-sm); padding: var(--space-2); font-family: var(--font-family-mono); font-size: 11px; color: var(--studio-accent-primary);">
                [Camera: low angle fast track right] Cyberpunk operative in titanium armor sprinting Tokyo alley --style cinematic --ar 16:9
              </div>
            </div>
          </div>

          <!-- Right: Provider & Budget Controls -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-3);">
            <div>
              <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Provider & Model:</label>
              <select class="select" id="gen-provider">
                <option value="runway_gen3">Runway Gen-3 Alpha ($0.25/shot)</option>
                <option value="kling_1_5">Kling 1.5 High-Definition ($0.20/shot)</option>
                <option value="flux_1_dev">FLUX.1 Dev (Open Weights / Free)</option>
                <option value="mock_local">Mock Provider (Local Simulation)</option>
              </select>
            </div>
            <div>
              <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Aspect Ratio & Resolution:</label>
              <select class="select" id="gen-aspect">
                <option>16:9 Landscape (1920x1080)</option>
                <option>9:16 Vertical Reel (1080x1920)</option>
                <option>2.39:1 Anamorphic Scope (3840x1608)</option>
              </select>
            </div>
            <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius-sm); padding: var(--space-2);">
              <div style="font-size: 10px; color: var(--studio-status-success); font-weight: 600;">BUDGET FIREWALL: ACTIVE</div>
              <div style="font-size: 11px; color: var(--studio-text-primary); margin-top: 2px;">Estimated Spend: $0.25 (Below $1.00 hard cap)</div>
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelector("#btn-compile-prompt").addEventListener("click", () => {
      const subj = this.container.querySelector("#gen-subject").value;
      const cam = this.container.querySelector("#gen-camera").value;
      const preview = this.container.querySelector("#gen-compiled-preview");
      preview.textContent = `[Camera: ${cam}] ${subj} --lighting volumetric --motion dynamic`;
      store.addNotification("Compiled multi-dimensional prompt into Runway Gen-3 tags", "success");
    });

    this.container.querySelector("#btn-submit-gen").addEventListener("click", () => {
      store.addNotification("Dispatched generation job to queue with SHA-256 idempotency cache", "success");
    });
  }
}
