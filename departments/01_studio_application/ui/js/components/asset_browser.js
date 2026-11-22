/**
 * Media Asset Browser Component.
 * Supports visual grid and list views, search, role filtering, direct file upload,
 * local path import, instant monitor playback, and timeline placement.
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class AssetBrowserComponent {
  constructor(container) {
    this.container = container;
    this.viewMode = "GRID"; // "GRID" | "LIST"
    this.render();
    this.bindEvents();
    this.loadProjectAssets();
  }

  async loadProjectAssets() {
    const activeProjId = store.getState().activeProjectId;
    if (activeProjId) {
      try {
        const res = await api.listAssets(activeProjId);
        if (res && res.assets) {
          store.setState({ assets: res.assets });
        }
      } catch (err) {
        console.log("Error loading assets:", err);
      }
    }
  }

  render() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%;">
        <!-- Hidden Real File Input -->
        <input type="file" id="asset-file-picker" style="display: none;" accept="video/*,audio/*,image/*" />

        <!-- Toolbar -->
        <div style="display: flex; align-items: center; justify-content: space-between; padding: var(--space-2); border-bottom: 1px solid var(--studio-border-subtle); gap: var(--space-2);">
          <input type="text" class="input" id="asset-search-input" placeholder="Search footage..." style="flex: 1;" />
          <button class="btn btn-secondary btn-xs" id="btn-toggle-view" title="Toggle Grid/List View">GRID</button>
          <button class="btn btn-primary btn-xs" id="btn-upload-direct" title="Upload Video File from Computer">↑ UPLOAD</button>
          <button class="btn btn-secondary btn-xs" id="btn-import-modal" title="Import Local Path">+ PATH</button>
        </div>

        <!-- Quick Demo Footage Bar -->
        <div style="display: flex; gap: var(--space-1); padding: 4px 8px; background: rgba(0, 240, 255, 0.05); border-bottom: 1px solid var(--studio-border-subtle); align-items: center; overflow-x: auto;">
          <span style="font-size: 10px; color: var(--studio-text-muted); font-weight: 600;">QUICK CLIPS:</span>
          <button class="btn btn-ghost btn-xs" id="btn-quick-octopus" style="color: #FFD700; font-size: 10px; border: 1px solid rgba(255,215,0,0.4); padding: 1px 6px;">
            🐙 3-Hearts Hindi Video
          </button>
          <button class="btn btn-ghost btn-xs" id="btn-quick-master" style="color: var(--studio-accent-primary); font-size: 10px; border: 1px solid rgba(0,240,255,0.3); padding: 1px 6px;">
            ✨ Motion Master
          </button>
          <button class="btn btn-ghost btn-xs" id="btn-quick-raw" style="color: #94A3B8; font-size: 10px; border: 1px solid rgba(148,163,184,0.3); padding: 1px 6px;">
            🎬 Raw Source
          </button>
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
        <div class="panel-body" id="asset-items-list" style="flex: 1; overflow-y: auto; padding: var(--space-2);">
          <div style="padding: 24px; text-align: center; color: var(--studio-text-muted);">
            Loading media assets...
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

    // Upload Direct button
    const filePicker = this.container.querySelector("#asset-file-picker");
    const uploadBtn = this.container.querySelector("#btn-upload-direct");
    uploadBtn.addEventListener("click", () => filePicker.click());

    filePicker.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const activeProjId = store.getState().activeProjectId;
      if (!activeProjId) {
        store.addNotification("Please open or select a project first", "warning");
        return;
      }
      try {
        store.addNotification(`Uploading '${file.name}' (${(file.size/1024/1024).toFixed(1)}MB)...`, "info");
        const res = await api.uploadAsset(activeProjId, file, file.name, "SOURCE_FOOTAGE");
        store.addNotification(`Successfully uploaded ${file.name}`, "success");
        // Reload assets
        const assets = await api.listAssets(activeProjId);
        store.setState({ assets: assets.assets || [] });
        if (res.asset_id) {
          store.setState({ selectedAssetId: res.asset_id });
        }
      } catch (err) {
        store.addNotification(`Upload failed: ${err.message}`, "error");
      }
    });

    // Quick Octopus Hindi Doc shortcut
    this.container.querySelector("#btn-quick-octopus").addEventListener("click", () => {
      const assets = store.getState().assets || [];
      const octo = assets.find(a => (a.display_name && a.display_name.includes("ऑक्टोपस")) || (a.original_filename && a.original_filename.includes("octopus")));
      if (octo) {
        store.setState({ selectedAssetId: octo.asset_id, isPlaying: true });
        window.dispatchEvent(new CustomEvent("add-asset-to-timeline", { detail: { assetId: octo.asset_id, asset: octo } }));
        store.addNotification("Loaded 50-Second Hindi Octopus Documentary into Program Monitor & Timeline!", "success");
      }
    });

    // Quick Master & Raw clip shortcuts
    this.container.querySelector("#btn-quick-master").addEventListener("click", () => {
      const assets = store.getState().assets || [];
      const master = assets.find(a => (a.display_name && a.display_name.includes("Master")) || (a.original_filename && a.original_filename.includes("master")));
      if (master) {
        store.setState({ selectedAssetId: master.asset_id });
        store.addNotification(`Loaded Motion Graphics Master into monitor & timeline`, "success");
      } else if (assets.length > 0) {
        store.setState({ selectedAssetId: assets[0].asset_id });
      }
    });

    this.container.querySelector("#btn-quick-raw").addEventListener("click", () => {
      const assets = store.getState().assets || [];
      const raw = assets.find(a => (a.display_name && a.display_name.includes("Source")) || (a.display_name && a.display_name.includes("hhhh")));
      if (raw) {
        store.setState({ selectedAssetId: raw.asset_id });
        store.addNotification(`Loaded Raw Source video into monitor & timeline`, "info");
      } else if (assets.length > 0) {
        store.setState({ selectedAssetId: assets[assets.length - 1].asset_id });
      }
    });

    const importBtn = this.container.querySelector("#btn-import-modal");
    importBtn.addEventListener("click", () => this.showImportDialog());

    // Subscribe to asset list updates in store
    store.subscribe("assets", () => this.refreshAssetDisplay());
    this.refreshAssetDisplay();
  }

  showImportDialog() {
    const modal = document.createElement("div");
    modal.className = "modal-backdrop";
    modal.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-header">
          <div class="modal-title">Import Media by Local Path</div>
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
          await api.importLocalFile(activeProjId, filePath, displayName, [role]);
          store.addNotification(`Asset imported: ${displayName || filePath}`, "success");
          const assets = await api.listAssets(activeProjId);
          store.setState({ assets: assets.assets || [] });
        } else {
          store.addNotification("No active project selected.", "warning");
        }
        close();
      } catch (err) {
        store.addNotification(`Import failed: ${err.message}`, "error");
      }
    });
  }

  refreshAssetDisplay() {
    const listContainer = this.container.querySelector("#asset-items-list");
    const { assets, assetFilterRole, assetSearchQuery, selectedAssetId } = store.getState();

    let filtered = assets || [];
    if (assetFilterRole && assetFilterRole !== "ALL") {
      filtered = filtered.filter(a => a.roles && a.roles.includes(assetFilterRole));
    }
    if (assetSearchQuery) {
      filtered = filtered.filter(a => (a.display_name || a.original_filename || "").toLowerCase().includes(assetSearchQuery));
    }

    if (filtered.length === 0) {
      listContainer.innerHTML = `
        <div style="padding: 24px; text-align: center; color: var(--studio-text-muted);">
          No media assets loaded. Click <strong>↑ UPLOAD</strong> to select video from your Mac.
        </div>
      `;
      return;
    }

    if (this.viewMode === "GRID") {
      listContainer.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: var(--space-2);">
          ${filtered.map(asset => {
            const isSel = asset.asset_id === selectedAssetId;
            const name = asset.display_name || asset.original_filename || "Video";
            return `
              <div class="asset-card ${isSel ? 'selected' : ''}" data-id="${asset.asset_id}" style="background-color: var(--studio-bg-panel-elevated); border: 1px solid ${isSel ? 'var(--studio-accent-primary)' : 'var(--studio-border-default)'}; border-radius: var(--radius-sm); overflow: hidden; cursor: pointer; display: flex; flex-direction: column; transition: border-color 0.15s ease;">
                <div style="width: 100%; aspect-ratio: 16/9; background-color: #07080A; display: flex; align-items: center; justify-content: center; font-size: 22px; color: var(--studio-text-muted); position: relative;">
                  ${asset.media_type === "AUDIO" ? "🎵" : asset.media_type === "IMAGE" ? "🖼️" : "🎬"}
                  <div style="position: absolute; bottom: 2px; right: 4px; font-size: 9px; background: rgba(0,0,0,0.7); color: #FFF; padding: 1px 4px; border-radius: 2px;">
                    ${asset.detected_format || "MP4"}
                  </div>
                </div>
                <div style="padding: 6px; font-size: 11px; display: flex; flex-direction: column; gap: 4px;">
                  <div style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--studio-text-primary);" title="${name}">${name}</div>
                  <div style="display: flex; gap: 4px;">
                    <button class="btn btn-primary btn-xs btn-card-play" data-id="${asset.asset_id}" style="flex: 1; font-size: 9px; padding: 2px 4px;">▶ Play</button>
                    <button class="btn btn-secondary btn-xs btn-card-timeline" data-id="${asset.asset_id}" style="flex: 1; font-size: 9px; padding: 2px 4px;">＋ NLE</button>
                  </div>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      `;
    } else {
      listContainer.innerHTML = `
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: left;">
          <thead>
            <tr style="border-bottom: 1px solid var(--studio-border-subtle); color: var(--studio-text-muted);">
              <th style="padding: 4px;">Name</th>
              <th style="padding: 4px;">Type</th>
              <th style="padding: 4px;">Action</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map(asset => `
              <tr class="asset-row" data-id="${asset.asset_id}" style="border-bottom: 1px solid var(--studio-border-subtle); cursor: pointer;">
                <td style="padding: 4px; color: var(--studio-text-primary); font-weight: 500;">${asset.display_name || asset.original_filename}</td>
                <td style="padding: 4px; color: var(--studio-text-secondary);">${asset.detected_format || asset.media_type}</td>
                <td style="padding: 4px; display: flex; gap: 4px;">
                  <button class="btn btn-primary btn-xs btn-card-play" data-id="${asset.asset_id}" style="font-size: 9px; padding: 1px 6px;">▶ Play</button>
                  <button class="btn btn-secondary btn-xs btn-card-timeline" data-id="${asset.asset_id}" style="font-size: 9px; padding: 1px 6px;">＋ NLE</button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    // Bind card play button
    listContainer.querySelectorAll(".btn-card-play").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const assetId = btn.getAttribute("data-id");
        store.setState({ selectedAssetId: assetId, isPlaying: true });
      });
    });

    // Bind card timeline button
    listContainer.querySelectorAll(".btn-card-timeline").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const assetId = btn.getAttribute("data-id");
        const asset = (store.getState().assets || []).find(a => a.asset_id === assetId);
        window.dispatchEvent(new CustomEvent("add-asset-to-timeline", { detail: { assetId, asset } }));
      });
    });

    // Bind card selection
    listContainer.querySelectorAll(".asset-card, .asset-row").forEach(el => {
      el.addEventListener("click", () => {
        const assetId = el.getAttribute("data-id");
        store.setState({ selectedAssetId: assetId });
      });
    });
  }
}
