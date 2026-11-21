/**
 * Agent Control Center Workspace.
 * Real-time monitoring and orchestration of the 12 specialist departmental agents.
 */

import { store } from "../state.js";

export class AgentCenterWorkspace {
  constructor(container) {
    this.container = container;
  }

  mount() {
    const agents = store.getState().agents;
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">Agent Control Center</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Autonomous specialist agents coordinating creative direction, generation, audio, color, and QC.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm" id="btn-pause-all">Pause Agents</button>
            <button class="btn btn-primary btn-sm" id="btn-refresh-telemetry">Refresh Status</button>
          </div>
        </div>

        <!-- 12 Agent Cards Grid -->
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-3);" id="agent-cards-grid">
          ${agents.map(a => `
            <div class="agent-card" data-id="${a.id}" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 600; font-size: 13px; color: var(--studio-text-primary);">${a.name}</div>
                <span class="badge ${a.status === "RUNNING" ? "badge-info" : "badge-success"}">${a.status}</span>
              </div>
              <div style="font-size: 11px; color: var(--studio-text-secondary); background: var(--studio-bg-canvas); padding: 6px; border-radius: var(--radius-sm); border: 1px solid var(--studio-border-subtle);">
                <strong>Task:</strong> ${a.task}
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px; color: var(--studio-text-muted);">
                <span>Dept: ${a.dept}</span>
                <span>Spend: $${a.cost.toFixed(2)}</span>
              </div>
              <div style="display: flex; gap: var(--space-1); margin-top: 4px;">
                <button class="btn btn-secondary btn-xs btn-assign" data-id="${a.id}" style="flex: 1;">Assign</button>
                <button class="btn btn-ghost btn-xs btn-logs" data-id="${a.id}">Logs</button>
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelectorAll(".btn-assign").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        store.addNotification(`Assigned high-priority directive to ${id}`, "info");
      });
    });

    this.container.querySelector("#btn-refresh-telemetry").addEventListener("click", () => {
      store.addNotification("Agent telemetry refreshed", "success");
    });
  }
}
