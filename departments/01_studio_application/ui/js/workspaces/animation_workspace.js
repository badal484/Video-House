/**
 * 2D Animation & Character Production Workspace.
 * Interface to Department 10 (2D Animation) & Department 12 (Character Production).
 */

import { store } from "../state.js";

export class AnimationWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">2D Animation & Character Studio</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Departments 10 & 12 • 5-angle Settei model sheets • 2D bone rigging • Exposure sheets (X-sheets).</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-primary btn-sm" id="btn-generate-settei">Generate Settei Turnaround</button>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 320px 1fr; gap: var(--space-4); flex: 1;">
          <!-- Character Card -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-weight: 700; font-size: 14px; color: var(--studio-accent-primary);">Character DNA Profile: Kenji Sato</div>
            <div style="font-size: 11px; color: var(--studio-text-muted);">Style: Modern Shonen Anime • Proportion Delta: ≤ 2.4%</div>
            <div style="width: 100%; aspect-ratio: 1; background: #07080A; border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; font-size: 48px;">
              🥋
            </div>
            <div style="font-size: 11px; color: var(--studio-text-secondary); line-height: 1.5;">
              Spiky charcoal hair, cyan cybernetic iris (Right), dark indigo tactical kimono with high collar.
            </div>
          </div>

          <!-- 5-Angle Settei Grid -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">5-Angle Settei Turnaround Sheet</div>
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: var(--space-2); flex: 1; align-items: center;">
              <div style="background: #000; border-radius: 4px; padding: 12px; text-align: center; font-size: 11px;">Front (0°)</div>
              <div style="background: #000; border-radius: 4px; padding: 12px; text-align: center; font-size: 11px;">Three-Quarter (45°)</div>
              <div style="background: #000; border-radius: 4px; padding: 12px; text-align: center; font-size: 11px;">Profile (90°)</div>
              <div style="background: #000; border-radius: 4px; padding: 12px; text-align: center; font-size: 11px;">Back 3/4 (135°)</div>
              <div style="background: #000; border-radius: 4px; padding: 12px; text-align: center; font-size: 11px;">Back (180°)</div>
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelector("#btn-generate-settei").addEventListener("click", () => {
      store.addNotification("Generated 5-angle Settei turnaround model sheet with eye-line guides", "success");
    });
  }
}

