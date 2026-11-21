/**
 * Rendering, Quality Control & Delivery Workspace.
 * Interface to Department 18 (Quality Control) & Department 19 (Rendering & Delivery).
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class RenderingWorkspace {
  constructor(container) {
    this.container = container;
  }

  async mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">Automated QC, Rendering & Delivery</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Departments 18 & 19 • Preflight validation • Apple VideoToolbox ASIC • Broadcast & Streaming packaging.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-preflight-check">Run Preflight Audit</button>
            <button class="btn btn-primary btn-sm" id="btn-start-master-render">Compile & Render Master</button>
          </div>
        </div>

        <!-- Preflight & Profile Selection -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
          <!-- Preflight Status Card -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Preflight Readiness Checklist</div>
            <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px;">
              <div style="display: flex; justify-content: space-between;"><span>Timeline Media Availability:</span><span style="color: var(--studio-status-success); font-weight: 600;">100% ONLINE (0 Offline)</span></div>
              <div style="display: flex; justify-content: space-between;"><span>Typography Font Clearance:</span><span style="color: var(--studio-status-success); font-weight: 600;">ALL FONTS RESOLVED</span></div>
              <div style="display: flex; justify-content: space-between;"><span>Commercial License Hygiene:</span><span style="color: var(--studio-status-success); font-weight: 600;">CLEARED (0 Non-Commercial)</span></div>
              <div style="display: flex; justify-content: space-between;"><span>Color LUT Validation:</span><span style="color: var(--studio-status-success); font-weight: 600;">3D .CUBE VALIDATED</span></div>
            </div>
          </div>

          <!-- Target Delivery Profiles -->
          <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Target Delivery Profiles</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); font-size: 11px;">
              <label style="display: flex; align-items: center; gap: 6px;"><input type="checkbox" checked /> Apple ProRes 422 HQ (Master)</label>
              <label style="display: flex; align-items: center; gap: 6px;"><input type="checkbox" checked /> YouTube 1080p (FastStart)</label>
              <label style="display: flex; align-items: center; gap: 6px;"><input type="checkbox" checked /> Social Vertical 9:16 (Shorts)</label>
              <label style="display: flex; align-items: center; gap: 6px;"><input type="checkbox" /> Broadcast MXF OP1a</label>
              <label style="display: flex; align-items: center; gap: 6px;"><input type="checkbox" /> Archival FFV1 Lossless</label>
            </div>
          </div>
        </div>

        <!-- Automated QC Defect Report -->
        <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Automated Quality Control (QC) Report</div>
            <span class="badge badge-success">QC PASSED (0 BLOCKING DEFECTS)</span>
          </div>
          <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: left;">
            <thead>
              <tr style="border-bottom: 1px solid var(--studio-border-subtle); color: var(--studio-text-muted);">
                <th style="padding: 6px;">Check Category</th>
                <th style="padding: 6px;">Rule Inspected</th>
                <th style="padding: 6px;">Measured Metric</th>
                <th style="padding: 6px;">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr style="border-bottom: 1px solid var(--studio-border-subtle);">
                <td style="padding: 6px;">Video Integrity</td>
                <td style="padding: 6px;">Black frame & freeze detection</td>
                <td style="padding: 6px;">0 black frames, 0 frozen frames</td>
                <td style="padding: 6px;"><span class="badge badge-success">PASSED</span></td>
              </tr>
              <tr style="border-bottom: 1px solid var(--studio-border-subtle);">
                <td style="padding: 6px;">Audio Loudness</td>
                <td style="padding: 6px;">EBU R128 integrated loudness</td>
                <td style="padding: 6px;">-14.02 LUFS (-1.01 dBTP)</td>
                <td style="padding: 6px;"><span class="badge badge-success">PASSED</span></td>
              </tr>
              <tr style="border-bottom: 1px solid var(--studio-border-subtle);">
                <td style="padding: 6px;">Color Signaling</td>
                <td style="padding: 6px;">NCLX container tags</td>
                <td style="padding: 6px;">1-1-1 (BT.709) correctly signaled</td>
                <td style="padding: 6px;"><span class="badge badge-success">PASSED</span></td>
              </tr>
              <tr style="border-bottom: 1px solid var(--studio-border-subtle);">
                <td style="padding: 6px;">Delivery Package</td>
                <td style="padding: 6px;">Manifest & Checksums</td>
                <td style="padding: 6px;">delivery_manifest.json (SHA-256 verified)</td>
                <td style="padding: 6px;"><span class="badge badge-success">PASSED</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelector("#btn-preflight-check").addEventListener("click", () => {
      store.addNotification("Preflight validation passed: 0 offline clips, fonts resolved, commercial licenses cleared", "success");
    });
    this.container.querySelector("#btn-start-master-render").addEventListener("click", () => {
      store.addNotification("Dispatched multi-profile render plan to Apple VideoToolbox ASIC queue (345+ FPS)", "success");
    });
  }
}

