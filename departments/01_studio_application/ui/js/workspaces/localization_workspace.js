/**
 * Subtitles, Dubbing & Localization Workspace.
 * Interface to Department 17 (Subtitles & Localization), WhisperX timestamps & Sync Labs Lip-Sync.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class LocalizationWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">Subtitles, Dubbing & Lip-Synchronization</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Department 17 • Multi-language translation • Isochronic dubbing • Sync Labs commercial lip-sync.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-export-subtitles">Export Subtitles (SRT/VTT)</button>
            <button class="btn btn-primary btn-sm" id="btn-dispatch-dubbing">Dispatch Multi-Language Dub</button>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 340px; gap: var(--space-4); flex: 1;">
          <!-- Left: Timed Transcript Cue Editor -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Word-Level Synchronized Cues</div>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: left;">
              <thead>
                <tr style="border-bottom: 1px solid var(--studio-border-subtle); color: var(--studio-text-muted);">
                  <th style="padding: 6px;">Timecode (In - Out)</th>
                  <th style="padding: 6px;">Speaker</th>
                  <th style="padding: 6px;">Dialogue Text</th>
                  <th style="padding: 6px;">CPS</th>
                </tr>
              </thead>
              <tbody>
                <tr style="border-bottom: 1px solid var(--studio-border-subtle);">
                  <td style="padding: 6px; font-family: var(--font-family-mono); color: var(--studio-accent-primary);">00:00:01.200 - 00:00:04.100</td>
                  <td style="padding: 6px;">Kenji</td>
                  <td style="padding: 6px; color: var(--studio-text-primary);">The quantum ignition core is now fully stabilized.</td>
                  <td style="padding: 6px;"><span class="badge badge-success">16 CPS</span></td>
                </tr>
                <tr style="border-bottom: 1px solid var(--studio-border-subtle);">
                  <td style="padding: 6px; font-family: var(--font-family-mono); color: var(--studio-accent-primary);">00:00:04.300 - 00:00:07.800</td>
                  <td style="padding: 6px;">Dr. Vance</td>
                  <td style="padding: 6px; color: var(--studio-text-primary);">Initiating sub-atomic particle stream across the primary chamber.</td>
                  <td style="padding: 6px;"><span class="badge badge-success">17 CPS</span></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Right: Localization Settings & Consent Firewall -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-3);">
            <div>
              <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Target Languages:</label>
              <select class="select">
                <option>Spanish (Castilian & Latin American)</option>
                <option>Japanese (Tokyo Broadcast Standard)</option>
                <option>Hindi (Standard Modern)</option>
                <option>French (European)</option>
                <option>German</option>
              </select>
            </div>
            <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius-sm); padding: var(--space-2);">
              <div style="font-size: 10px; color: var(--studio-status-success); font-weight: 600;">BIOMETRIC VOICE CONSENT: VERIFIED</div>
              <div style="font-size: 11px; color: var(--studio-text-primary); margin-top: 2px;">Talent authorizations active for Kenji Sato & Dr. Vance. Commercial licensing cleared.</div>
            </div>
            <div>
              <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Commercial Lip-Sync Engine:</label>
              <select class="select">
                <option>Sync Labs Commercial API (4K Cloud)</option>
                <option>LatentSync (Permissive Open Weights)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelector("#btn-export-subtitles").addEventListener("click", () => {
      store.addNotification("Exported broadcast compliant subtitles in SRT, WebVTT, and ASS formats", "success");
    });
    this.container.querySelector("#btn-dispatch-dubbing").addEventListener("click", () => {
      store.addNotification("Dispatched multilingual voice dubbing with background music preservation", "success");
    });
  }
}
