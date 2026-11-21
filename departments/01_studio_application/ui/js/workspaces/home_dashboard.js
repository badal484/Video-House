/**
 * Home & Projects Dashboard Workspace.
 * Displays recent projects, template creation shortcuts, storage telemetry, and active renders.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class HomeDashboardWorkspace {
  constructor(container) {
    this.container = container;
  }

  async mount() {
    this.container.innerHTML = `
      <div style="padding: var(--space-6); overflow-y: auto; height: 100%; display: flex; flex-direction: column; gap: var(--space-6);">
        <!-- Dashboard Header -->
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div>
            <h1 style="font-size: var(--font-size-2xl); font-weight: 700; color: var(--studio-text-primary); letter-spacing: -0.02em;">Studio Projects</h1>
            <p style="font-size: var(--font-size-sm); color: var(--studio-text-muted);">Manage creative video productions, open timelines, and monitor background tasks.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-primary btn-md" id="btn-quick-create">+ New Project</button>
          </div>
        </div>

        <!-- Telemetry Summary Cards -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--space-3);" id="telemetry-cards">
          <div class="card" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3);">
            <div style="font-size: 11px; color: var(--studio-text-muted); text-transform: uppercase;">Active Projects</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--studio-text-primary); margin-top: 4px;" id="stat-project-count">-</div>
          </div>
          <div class="card" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3);">
            <div style="font-size: 11px; color: var(--studio-text-muted); text-transform: uppercase;">Storage Available</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--studio-accent-primary); margin-top: 4px;" id="stat-storage">-</div>
          </div>
          <div class="card" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3);">
            <div style="font-size: 11px; color: var(--studio-text-muted); text-transform: uppercase;">Hardware Encoding</div>
            <div style="font-size: 24px; font-weight: 700; color: var(--studio-status-success); margin-top: 4px;" id="stat-hw">Apple M4 ASIC</div>
          </div>
        </div>

        <!-- Quick Start Production Templates -->
        <div>
          <h2 style="font-size: var(--font-size-md); font-weight: 600; color: var(--studio-text-secondary); margin-bottom: var(--space-2);">Quick Start Templates</h2>
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--space-3);" id="template-cards-list">
            <div class="template-card" data-template="YOUTUBE_16_9" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); cursor: pointer;">
              <div style="font-size: 18px; margin-bottom: 6px;">📺</div>
              <div style="font-weight: 600; font-size: 13px;">YouTube Long-Form</div>
              <div style="font-size: 11px; color: var(--studio-text-muted); margin-top: 2px;">1080p 24fps | -14 LUFS</div>
            </div>
            <div class="template-card" data-template="SOCIAL_VERTICAL_9_16" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); cursor: pointer;">
              <div style="font-size: 18px; margin-bottom: 6px;">📱</div>
              <div style="font-weight: 600; font-size: 13px;">Shorts & Reels 9:16</div>
              <div style="font-size: 11px; color: var(--studio-text-muted); margin-top: 2px;">1080x1920 30fps | FastStart</div>
            </div>
            <div class="template-card" data-template="CINEMATIC_2_39" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); cursor: pointer;">
              <div style="font-size: 18px; margin-bottom: 6px;">🎬</div>
              <div style="font-weight: 600; font-size: 13px;">Cinematic Film 2.39:1</div>
              <div style="font-size: 11px; color: var(--studio-text-muted); margin-top: 2px;">4K Scope | ACEScg Color</div>
            </div>
            <div class="template-card" data-template="ANIME_2D" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); cursor: pointer;">
              <div style="font-size: 18px; margin-bottom: 6px;">🎨</div>
              <div style="font-weight: 600; font-size: 13px;">2D Anime Pipeline</div>
              <div style="font-size: 11px; color: var(--studio-text-muted); margin-top: 2px;">12fps on 2s | Cel Shading</div>
            </div>
          </div>
        </div>

        <!-- Recent Projects Grid -->
        <div style="flex: 1;">
          <h2 style="font-size: var(--font-size-md); font-weight: 600; color: var(--studio-text-secondary); margin-bottom: var(--space-2);">All Projects</h2>
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-4);" id="projects-grid-list">
            <div style="padding: 32px; text-align: center; color: var(--studio-text-muted);">Loading projects...</div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
    await this.loadData();
  }

  bindEvents() {
    this.container.querySelector("#btn-quick-create").addEventListener("click", () => this.showCreateModal());

    this.container.querySelectorAll(".template-card").forEach(el => {
      el.addEventListener("click", () => {
        const tmpl = el.getAttribute("data-template");
        this.showCreateModal(tmpl);
      });
    });
  }

  async loadData() {
    try {
      const [projData, telemData] = await Promise.all([
        api.listProjects(),
        api.getSystemTelemetry()
      ]);

      const projects = projData.projects || [];
      store.setState({ projects });

      this.container.querySelector("#stat-project-count").textContent = projects.length;
      if (telemData && telemData.storage) {
        this.container.querySelector("#stat-storage").textContent = `${telemData.storage.free_gb} GB Free`;
      }

      this.renderProjects(projects);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    }
  }

  renderProjects(projects) {
    const list = this.container.querySelector("#projects-grid-list");
    if (!projects || projects.length === 0) {
      list.innerHTML = `<div style="padding: 32px; text-align: center; color: var(--studio-text-muted); grid-column: 1 / -1;">No projects created yet. Start a new project above!</div>`;
      return;
    }

    list.innerHTML = projects.map(p => `
      <div class="project-card" data-id="${p.project_id}" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); overflow: hidden; cursor: pointer; transition: all 0.15s ease;">
        <div style="width: 100%; aspect-ratio: 16/9; background-color: #07080A; display: flex; align-items: center; justify-content: center; font-size: 28px; border-bottom: 1px solid var(--studio-border-subtle);">
          🎬
        </div>
        <div style="padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-1);">
          <div style="font-weight: 600; font-size: 14px; color: var(--studio-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${p.name}</div>
          <div style="font-size: 11px; color: var(--studio-text-muted); display: flex; justify-content: space-between;">
            <span>${p.settings.aspect_ratio || "16:9"} • ${p.settings.fps || 24}fps</span>
            <span>${p.asset_count || 0} Assets</span>
          </div>
          <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
            <span class="badge badge-info" style="font-size: 9px;">${p.settings.current_stage || "PLANNING"}</span>
            <button class="btn btn-danger btn-xs btn-del-proj" data-id="${p.project_id}" title="Delete Project">🗑️</button>
          </div>
        </div>
      </div>
    `).join("");

    list.querySelectorAll(".project-card").forEach(card => {
      card.addEventListener("click", (e) => {
        if (e.target.closest(".btn-del-proj")) return;
        const id = card.getAttribute("data-id");
        this.openProject(id);
      });
    });

    list.querySelectorAll(".btn-del-proj").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-id");
        if (confirm("Are you sure you want to delete this project? This action is permanent.")) {
          try {
            await api.deleteProject(id);
            store.addNotification("Project deleted successfully", "success");
            await this.loadData();
          } catch (err) {
            store.addNotification(`Failed to delete project: ${err.message}`, "error");
          }
        }
      });
    });
  }

  async openProject(projectId) {
    try {
      const proj = await api.getProject(projectId);
      store.setState({
        activeProjectId: projectId,
        activeProject: proj,
        hasUnsavedChanges: false
      });

      // Load project assets and timeline
      const assets = await api.listAssets(projectId);
      store.setState({ assets: assets.assets || [] });

      store.addNotification(`Opened project: ${proj.name}`, "success");
      // Switch to creative workspace
      store.setWorkspace("creative");
    } catch (err) {
      store.addNotification(`Error opening project: ${err.message}`, "error");
    }
  }

  showCreateModal(defaultTemplate = "BLANK") {
    const modal = document.createElement("div");
    modal.className = "modal-backdrop";
    modal.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-header">
          <div class="modal-title">Create New Production Project</div>
          <button class="btn btn-ghost btn-xs close-modal">✕</button>
        </div>
        <div class="modal-body" style="display: flex; flex-direction: column; gap: var(--space-3);">
          <div>
            <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Project Name:</label>
            <input type="text" class="input" id="new-proj-name" placeholder="e.g. Cyberpunk Cinematic Short" autofocus />
          </div>
          <div>
            <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Production Preset Template:</label>
            <select class="select" id="new-proj-template">
              <option value="BLANK" ${defaultTemplate === "BLANK" ? "selected" : ""}>Blank Project (1080p 24fps)</option>
              <option value="YOUTUBE_16_9" ${defaultTemplate === "YOUTUBE_16_9" ? "selected" : ""}>YouTube Long-Form (16:9, -14 LUFS)</option>
              <option value="SOCIAL_VERTICAL_9_16" ${defaultTemplate === "SOCIAL_VERTICAL_9_16" ? "selected" : ""}>Social Vertical Reel (9:16 30fps)</option>
              <option value="CINEMATIC_2_39" ${defaultTemplate === "CINEMATIC_2_39" ? "selected" : ""}>Cinematic Widescreen (2.39:1, 4K ACEScg)</option>
              <option value="ANIME_2D" ${defaultTemplate === "ANIME_2D" ? "selected" : ""}>2D Anime Production (12fps on 2s)</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm close-modal">Cancel</button>
          <button class="btn btn-primary btn-sm" id="btn-submit-create">Create Project</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    const close = () => document.body.removeChild(modal);
    modal.querySelectorAll(".close-modal").forEach(b => b.addEventListener("click", close));

    modal.querySelector("#btn-submit-create").addEventListener("click", async () => {
      const name = modal.querySelector("#new-proj-name").value.trim() || "Untitled Production";
      const tmpl = modal.querySelector("#new-proj-template").value;

      try {
        const res = await api.createProject(name, { template: tmpl, current_stage: "PLANNING" });
        store.addNotification(`Created project: ${name}`, "success");
        close();
        await this.loadData();
        await this.openProject(res.project_id);
      } catch (err) {
        store.addNotification(`Failed to create project: ${err.message}`, "error");
      }
    });
  }
}

