/**
 * Media Asset Browser Component.
 * Supports visual grid and list views, search, role filtering, local import, and drag-and-drop.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class AssetBrowserComponent {
  constructor(container) {
    this.container = container;
    this.viewMode = "GRID"; // "GRID" | "LIST"
    this.render();
    this.bindEvents();
  }

  render() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%;">
        <!-- Toolbar -->
        <div style="display: flex; align-items: center; justify-content: space-between; padding: var(--space-2); border-bottom: 1px solid var(--studio-border-subtle); gap: var(--space-2);">
          <input type="text" class="input" id="asset-search-input" placeholder="Search assets..." style="flex: 1;" />
          <button class="btn btn-secondary btn-xs" id="btn-toggle-view" title="Toggle Grid/List View">GRID</button>
          <button class="btn btn-primary btn-xs" id="btn-import-modal" title="Import Local Media File">+ IMPORT</button>
        </div>

        <!-- Role Filter Bar -->
        <div style="display: flex; gap: var(--space-1); padding: var(--space-1) var(--space-2); overflow-x: auto; background-color: var(--studio-bg-canvas); border-bottom: 1px solid var(--studio-border-subtle);" id="asset-role-filters">
          <button class="btn btn-ghost btn-xs filter-role active" data-role="ALL">All</button>
          <button class="btn btn-ghost btn-xs filter-role" data-role="SOURCE_FOOTAGE">Footage</button>
          <button class="btn btn-ghost btn-xs filter-role" data-role="GENERATED">AI Generated</button>
          <button class="btn btn-ghost btn-xs filter-role" data-role="AUDIO">Audio</button>
          <button class="btn btn-ghost btn-xs filter-role" data-role="GRAPHICS">Graphics</button>
        </div>

        <!-- Asset Items Container -->
        <div class="panel-body" id="asset-items-list" style="flex: 1; overflow-y: auto;">
          <div style="padding: 24px; text-align: center; color: var(--studio-text-muted);">
            No media assets found in project. Click <strong>+ IMPORT</strong> to load footage.
          </div>
        </div>
      </div>
    `;
  }

  bindEvents() {
    const searchInput = this.container.querySelector("#asset-search-input");
    searchInput.addEventListener("input", (e) => {
      store.setState({ assetSearchQuery: e.target.value.toLowerCase().trim() });
      this.refreshAssetDisplay();
    });

    const toggleViewBtn = this.container.querySelector("#btn-toggle-view");
    toggleViewBtn.addEventListener("click", () => {
      this.viewMode = this.viewMode === "GRID" ? "LIST" : "GRID";
      toggleViewBtn.textContent = this.viewMode;
      this.refreshAssetDisplay();
    });

    const roleFilters = this.container.querySelectorAll(".filter-role");
    roleFilters.forEach(btn => {
      btn.addEventListener("click", () => {
        roleFilters.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        store.setState({ assetFilterRole: btn.getAttribute("data-role") });
        this.refreshAssetDisplay();
      });
    });

    const importBtn = this.container.querySelector("#btn-import-modal");
    importBtn.addEventListener("click", () => this.showImportDialog());

    // Subscribe to asset list updates in store
    store.subscribe("assets", () => this.refreshAssetDisplay());
  }

  showImportDialog() {
    const modal = document.createElement("div");
    modal.className = "modal-backdrop";
    modal.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-header">
          <div class="modal-title">Import Media Asset</div>
          <button class="btn btn-ghost btn-xs close-modal">✕</button>
        </div>
        <div class="modal-body" style="display: flex; flex-direction: column; gap: var(--space-3);">
          <div>
            <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Local File Path (Preserves Storage):</label>
            <input type="text" class="input" id="import-path" placeholder="/absolute/path/to/video.mp4" />
          </div>
          <div>
            <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Display Name (Optional):</label>
            <input type="text" class="input" id="import-name" placeholder="e.g. Master_Take_01.mp4" />
          </div>
          <div>
            <label style="font-size: 11px; color: var(--studio-text-secondary); display: block; margin-bottom: 4px;">Asset Role:</label>
            <select class="select" id="import-role">
              <option value="SOURCE_FOOTAGE">Source Footage (Camera Original)</option>
              <option value="REFERENCE_IMAGE">Visual Reference Image</option>
              <option value="VOICEOVER">Voiceover Dialogue</option>
              <option value="BACKGROUND_MUSIC">Background Music Score</option>
              <option value="SFX">Sound Effect</option>
              <option value="LUT">3D Look-Up Table (.cube)</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm close-modal">Cancel</button>
          <button class="btn btn-primary btn-sm" id="btn-submit-import">Import Asset</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    const close = () => document.body.removeChild(modal);
    modal.querySelectorAll(".close-modal").forEach(b => b.addEventListener("click", close));

    modal.querySelector("#btn-submit-import").addEventListener("click", async () => {
      const filePath = modal.querySelector("#import-path").value.trim();
      const displayName = modal.querySelector("#import-name").value.trim() || undefined;
      const role = modal.querySelector("#import-role").value;
      const activeProjId = store.getState().activeProjectId;

      if (!filePath) {
        store.addNotification("Please enter a valid file path.", "error");
        return;
      }

      try {
        if (activeProjId) {
          const res = await api.importLocalFile(activeProjId, filePath, displayName, [role]);
          store.addNotification(`Asset imported: ${displayName || filePath}`, "success");
          // Refresh project assets
          const assets = await api.listAssets(activeProjId);
          store.setState({ assets: assets.assets || [] });
        } else {
          store.addNotification("No active project selected. Create or open a project first.", "warning");
        }
        close();
      } catch (err) {
        store.addNotification(`Import failed: ${err.message}`, "error");
      }
    });
  }

  refreshAssetDisplay() {
    const listContainer = this.container.querySelector("#asset-items-list");
    const { assets, assetFilterRole, assetSearchQuery } = store.getState();

    let filtered = assets || [];
    if (assetFilterRole && assetFilterRole !== "ALL") {
      filtered = filtered.filter(a => a.roles && a.roles.includes(assetFilterRole));
    }
    if (assetSearchQuery) {
      filtered = filtered.filter(a => (a.display_name || a.original_filename || "").toLowerCase().includes(assetSearchQuery));
    }

    if (filtered.length === 0) {
      listContainer.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--studio-text-muted);">No matching assets found</div>`;
      return;
    }

    if (this.viewMode === "GRID") {
      listContainer.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: var(--space-2);">
          ${filtered.map(asset => `
            <div class="asset-card" data-id="${asset.asset_id}" style="background-color: var(--studio-bg-panel-elevated); border: 1px solid var(--studio-border-default); border-radius: var(--radius-sm); overflow: hidden; cursor: pointer; display: flex; flex-direction: column;">
              <div style="width: 100%; aspect-ratio: 16/9; background-color: #07080A; display: flex; align-items: center; justify-content: center; font-size: 20px; color: var(--studio-text-muted);">
                ${asset.media_type === "AUDIO" ? "🎵" : asset.media_type === "IMAGE" ? "🖼️" : "🎬"}
              </div>
              <div style="padding: 4px; font-size: 11px; display: flex; flex-direction: column; gap: 2px;">
                <div style="font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--studio-text-primary);">${asset.display_name || asset.original_filename}</div>
                <div style="color: var(--studio-text-muted); font-size: 10px;">${asset.detected_format || "MEDIA"}</div>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    } else {
      listContainer.innerHTML = `
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--studio-border-subtle); color: var(--studio-text-muted);">
              <th style="padding: 4px;">Name</th>
              <th style="padding: 4px;">Type</th>
              <th style="padding: 4px;">Size</th>
              <th style="padding: 4px;">Status</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map(asset => `
              <tr class="asset-row" data-id="${asset.asset_id}" style="border-bottom: 1px solid var(--studio-border-subtle); cursor: pointer;">
                <td style="padding: 4px; color: var(--studio-text-primary);">${asset.display_name || asset.original_filename}</td>
                <td style="padding: 4px; color: var(--studio-text-secondary);">${asset.detected_format || asset.media_type}</td>
                <td style="padding: 4px; color: var(--studio-text-muted);">${asset.byte_size ? Math.round(asset.byte_size / 1024) + " KB" : "-"}</td>
                <td style="padding: 4px;"><span class="badge badge-success">${asset.processing_status || "READY"}</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    // Add click selection
    listContainer.querySelectorAll(".asset-card, .asset-row").forEach(el => {
      el.addEventListener("click", () => {
        const assetId = el.getAttribute("data-id");
        store.setState({ selectedAssetId: assetId });
        store.addNotification(`Selected asset: ${assetId.substring(0, 8)}...`, "info");
      });
    });
  }
}

