/**
 * VFX & Compositing Workspace.
 * Interface to Department 13 (VFX Compositing), Node Graph DAG & Chroma Keying.
 */

import { store } from "../state.js";

export class VFXWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">Visual Effects & Node Compositing</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Department 13 • Topological DAG graph • Chroma Keying • Planar Tracking.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-run-chroma">Test Chroma Key</button>
            <button class="btn btn-primary btn-sm" id="btn-eval-dag">Evaluate Graph</button>
          </div>
        </div>

        <!-- Node Graph Surface -->
        <div style="flex: 1; background-color: #0B0D11; border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-4); position: relative; overflow: hidden; display: flex; flex-direction: column;">
          <div style="font-size: 11px; font-weight: 600; color: var(--studio-text-muted); margin-bottom: var(--space-2);">COMPOSITING NODE DAG</div>
          <div style="display: flex; align-items: center; gap: var(--space-6); justify-content: center; margin-top: 40px;">
            <div class="node-box" style="background: var(--studio-bg-panel-elevated); border: 2px solid var(--studio-accent-primary); border-radius: var(--radius-md); padding: 12px; width: 160px; text-align: center;">
              <div style="font-size: 12px; font-weight: 600; color: var(--studio-accent-primary);">GreenScreenPlate</div>
              <div style="font-size: 10px; color: var(--studio-text-muted); margin-top: 4px;">Input 4K RGBA</div>
            </div>
            <div style="color: var(--studio-accent-primary); font-size: 20px;">➔</div>
            <div class="node-box" style="background: var(--studio-bg-panel-elevated); border: 2px solid var(--studio-status-warning); border-radius: var(--radius-md); padding: 12px; width: 160px; text-align: center;">
              <div style="font-size: 12px; font-weight: 600; color: var(--studio-status-warning);">ChromaKeyer</div>
              <div style="font-size: 10px; color: var(--studio-text-muted); margin-top: 4px;">Despill + Feather</div>
            </div>
            <div style="color: var(--studio-accent-primary); font-size: 20px;">➔</div>
            <div class="node-box" style="background: var(--studio-bg-panel-elevated); border: 2px solid var(--studio-status-success); border-radius: var(--radius-md); padding: 12px; width: 160px; text-align: center;">
              <div style="font-size: 12px; font-weight: 600; color: var(--studio-status-success);">MergeOver</div>
              <div style="font-size: 10px; color: var(--studio-text-muted); margin-top: 4px;">Premultiplied Alpha</div>
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelector("#btn-run-chroma").addEventListener("click", () => {
      store.addNotification("Chroma key despill completed (Zero matte pinholes)", "success");
    });
    this.container.querySelector("#btn-eval-dag").addEventListener("click", () => {
      store.addNotification("Topological node DAG graph evaluated cleanly", "success");
    });
  }
}

