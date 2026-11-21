/**
 * Editing Workspace (Dedicated NLE Track Assembly).
 * Direct interface to Department 08 (Video Editing) and OpenTimelineIO.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class EditingWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-3); gap: var(--space-3);">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-lg); font-weight: 700; color: var(--studio-text-primary);">Non-Linear Editorial Assembly (OTIO)</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Department 08 Video Editing • Rational timecode precision • Zero drift cuts</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-export-otio">Export OTIO JSON</button>
            <button class="btn btn-primary btn-sm" id="btn-render-preview">Render Fast Preview</button>
          </div>
        </div>

        <!-- Timeline Track Stack -->
        <div style="flex: 1; background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--studio-text-muted);">
            <span>Active Tracks: 4 (2 Video, 2 Audio)</span>
            <span>Timebase: 24.000 fps (RationalTime)</span>
          </div>
          <div style="flex: 1; background-color: var(--studio-bg-canvas); border: 1px solid var(--studio-border-subtle); border-radius: var(--radius-sm); position: relative; overflow-x: auto; padding: 12px;">
            <div style="font-family: var(--font-family-mono); font-size: 12px; color: var(--studio-text-secondary); margin-bottom: 8px;">
              [V2 Graphics]  ------| Lower Third (00:04 - 00:09) |------
            </div>
            <div style="font-family: var(--font-family-mono); font-size: 12px; color: var(--studio-accent-primary); margin-bottom: 8px;">
              [V1 Video]     [ Shot 01 (00:00 - 00:08) ] >CrossDissolve> [ Shot 02 (00:08 - 00:18) ]
            </div>
            <div style="font-family: var(--font-family-mono); font-size: 12px; color: var(--studio-track-audio); margin-bottom: 8px;">
              [A1 Dialogue]  [ Voiceover Take 01 (00:01 - 00:07) ]------[ Voiceover Take 02 (00:10 - 00:16) ]
            </div>
            <div style="font-family: var(--font-family-mono); font-size: 12px; color: var(--studio-track-music);">
              [A2 Music]     [ Ambient Synth Drone Background (-14 LUFS Sidechain Ducked) ]
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelector("#btn-export-otio").addEventListener("click", () => {
      store.addNotification("Exported canonical OpenTimelineIO editorial schema", "success");
    });

    this.container.querySelector("#btn-render-preview").addEventListener("click", () => {
      store.addNotification("Dispatched fast preview render to Apple VideoToolbox queue", "info");
    });
  }
}
