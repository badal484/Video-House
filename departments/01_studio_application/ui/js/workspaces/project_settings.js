/**
 * Project Settings & Global Configuration Workspace.
 */

import { store } from "../state.js";
import { themeManager } from "../tokens.js";

export class ProjectSettingsWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-6); gap: var(--space-4); max-width: 800px; overflow-y: auto;">
        <div>
          <h2 style="font-size: var(--font-size-2xl); font-weight: 700; color: var(--studio-text-primary);">Project & Studio Settings</h2>
          <p style="font-size: var(--font-size-sm); color: var(--studio-text-muted);">Configure canvas dimensions, color spaces, hardware acceleration, and UI theme.</p>
        </div>

        <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-3);">
          <div style="font-size: 13px; font-weight: 600; color: var(--studio-text-primary);">Theme & Accent Color</div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-toggle-dark-light">Toggle Dark / Light Theme</button>
          </div>
        </div>

        <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-3);">
          <div style="font-size: 13px; font-weight: 600; color: var(--studio-text-primary);">Workstation Telemetry & Hardware</div>
          <div style="display: flex; flex-direction: column; gap: 8px; font-size: 12px; color: var(--studio-text-secondary);">
            <div><strong>Machine:</strong> Apple MacBook Pro (Apple M4, 16GB Unified RAM)</div>
            <div><strong>Storage:</strong> ~38GB Free Disk Space Available</div>
            <div><strong>Hardware Video Encoders:</strong> VideoToolbox (h264_videotoolbox, hevc_videotoolbox, prores_videotoolbox) Active</div>
            <div><strong>DSP Processing:</strong> In-process JUCE C++ accelerated audio engine</div>
          </div>
        </div>
      </div>
    `;

    this.container.querySelector("#btn-toggle-dark-light").addEventListener("click", () => {
      const newTheme = themeManager.toggleTheme();
      store.addNotification(`Switched interface theme to ${newTheme}`, "info");
    });
  }
}
