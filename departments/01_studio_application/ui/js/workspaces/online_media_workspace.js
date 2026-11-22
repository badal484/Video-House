/**
 * Online Media & Reference Intelligence Workspace.
 * Provides YouTube research, metadata inspection, authorized imports,
 * audio extraction & waveform display, reference style deconstruction,
 * and a unified permission-tiered media library.
 */
import { api } from "../api_client.js";
import { store } from "../state.js";

export class OnlineMediaWorkspace {
  constructor(mountElement) {
    this.mount = mountElement;
    this.activeSubtab = "research"; // "research", "import", "reference", "library"
    this.inspectedMetadata = null;
    this.searchResults = [];
    this.analysisReport = null;
    this.audioReport = null;
    this.libraryAssets = [];
    this.activeFilter = "ALL";
    this.librarySearch = "";
  }

  mount() {
    this.render();
    this.loadUnifiedLibrary();
  }

  render() {
    this.mount.innerHTML = `
      <div class="workspace-container online-media-workspace" style="display: flex; flex-direction: column; height: 100%; overflow: hidden; background: var(--studio-bg-app, #0a0e14); color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <!-- Workspace Header Toolbar -->
        <header style="display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; background: #121820; border-bottom: 1px solid #1f2937;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00F0FF" stroke-width="2">
              <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"></path>
              <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"></polygon>
            </svg>
            <h2 style="font-size: 15px; font-weight: 600; letter-spacing: 0.5px; margin: 0; color: #fff;">
              ONLINE MEDIA & REFERENCE RESEARCH
            </h2>
          </div>
          <!-- Subtab Navigation -->
          <div style="display: flex; gap: 6px; background: #0a0e14; padding: 3px; border-radius: 6px; border: 1px solid #1f2937;">
            <button class="om-subtab-btn ${this.activeSubtab === 'research' ? 'active' : ''}" data-subtab="research" style="${this.getSubtabStyle('research')}">Research & Inspect</button>
            <button class="om-subtab-btn ${this.activeSubtab === 'import' ? 'active' : ''}" data-subtab="import" style="${this.getSubtabStyle('import')}">Authorized Import</button>
            <button class="om-subtab-btn ${this.activeSubtab === 'reference' ? 'active' : ''}" data-subtab="reference" style="${this.getSubtabStyle('reference')}">Reference Analysis</button>
            <button class="om-subtab-btn ${this.activeSubtab === 'library' ? 'active' : ''}" data-subtab="library" style="${this.getSubtabStyle('library')}">Unified Library</button>
          </div>
        </header>

        <!-- Dynamic Body Area -->
        <div id="om-workspace-body" style="flex: 1; overflow-y: auto; padding: 20px;">
          ${this.renderSubtabContent()}
        </div>
      </div>
    `;

    this.bindEvents();
  }

  getSubtabStyle(name) {
    const isActive = this.activeSubtab === name;
    return `
      padding: 6px 14px;
      font-size: 12px;
      font-weight: 500;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      background: ${isActive ? '#00F0FF' : 'transparent'};
      color: ${isActive ? '#050B14' : '#9ca3af'};
      transition: all 0.15s ease;
    `;
  }

  renderSubtabContent() {
    switch (this.activeSubtab) {
      case "research":
        return this.renderResearchTab();
      case "import":
        return this.renderImportTab();
      case "reference":
        return this.renderReferenceTab();
      case "library":
        return this.renderLibraryTab();
      default:
        return this.renderResearchTab();
    }
  }

  renderResearchTab() {
    return `
      <div style="max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px;">
        <!-- Search & Inspect Input Panel -->
        <div style="background: #121820; border: 1px solid #1f2937; border-radius: 8px; padding: 18px;">
          <h3 style="font-size: 13px; font-weight: 600; color: #00F0FF; margin-top: 0; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
            YouTube URL Inspection & Keyword Discovery
          </h3>
          <div style="display: flex; gap: 10px; margin-bottom: 12px;">
            <input type="text" id="om-inspect-url-input" placeholder="Paste YouTube Video URL (e.g. https://www.youtube.com/watch?v=9ZnbvL8CVyA)..." style="flex: 1; padding: 10px 14px; background: #0a0e14; border: 1px solid #374151; border-radius: 6px; color: #fff; font-size: 13px;">
            <button id="om-btn-inspect" style="padding: 10px 20px; background: #00F0FF; color: #050B14; font-weight: 600; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">Inspect URL</button>
          </div>
          <div style="display: flex; gap: 10px; align-items: center;">
            <input type="text" id="om-search-query-input" placeholder="Or search YouTube by topic/keywords (e.g. octopus three hearts circulation)..." style="flex: 1; padding: 8px 14px; background: #0a0e14; border: 1px solid #374151; border-radius: 6px; color: #fff; font-size: 12px;">
            <button id="om-btn-search" style="padding: 8px 16px; background: #1f2937; color: #e5e7eb; border: 1px solid #374151; border-radius: 6px; cursor: pointer; font-size: 12px;">Search YouTube</button>
          </div>
        </div>

        <!-- Inspected Metadata Result Card -->
        ${this.inspectedMetadata ? this.renderMetadataCard(this.inspectedMetadata) : ''}

        <!-- Search Results Grid -->
        ${this.searchResults.length > 0 ? this.renderSearchResults() : ''}
      </div>
    `;
  }

  renderMetadataCard(meta) {
    return `
      <div style="background: #121820; border: 1px solid #00F0FF44; border-radius: 8px; padding: 20px; display: flex; flex-direction: column; gap: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 20px;">
          <div style="flex: 1;">
            <div style="display: flex; gap: 8px; margin-bottom: 6px; align-items: center;">
              <span style="background: #1e3a8a; color: #93c5fd; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">
                ${meta.permission_tier}
              </span>
              <span style="color: #9ca3af; font-size: 12px;">Channel: <strong style="color: #fff;">${meta.author}</strong></span>
              <span style="color: #9ca3af; font-size: 12px;">• Duration: <strong style="color: #fff;">${meta.duration_seconds}s</strong></span>
              ${meta.view_count ? `<span style="color: #9ca3af; font-size: 12px;">• Views: ${meta.view_count.toLocaleString()}</span>` : ''}
            </div>
            <h2 style="font-size: 18px; font-weight: 600; color: #fff; margin: 0 0 10px 0;">${meta.title}</h2>
            <p style="font-size: 12px; color: #9ca3af; line-height: 1.5; margin: 0; max-height: 80px; overflow-y: auto;">
              ${meta.description || 'No description provided.'}
            </p>
          </div>
          <div style="width: 220px; flex-shrink: 0;">
            <img src="${meta.thumbnail_url}" alt="Thumbnail" style="width: 100%; border-radius: 6px; border: 1px solid #374151; aspect-ratio: 16/9; object-fit: cover;">
          </div>
        </div>

        <!-- Official Compliant Embed Preview -->
        ${meta.embed_html ? `
          <div style="background: #0a0e14; border: 1px solid #1f2937; border-radius: 6px; padding: 12px;">
            <div style="font-size: 11px; color: #6b7280; margin-bottom: 8px; font-weight: 600; text-transform: uppercase;">Official Permitted Embed Preview</div>
            <div style="max-width: 560px; aspect-ratio: 16/9; margin: 0 auto; overflow: hidden; border-radius: 4px;">
              ${meta.embed_html.replace('width="200"', 'width="100%"').replace('height="113"', 'height="100%"')}
            </div>
          </div>
        ` : ''}

        <!-- Chapters & Captions Summary -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <div style="background: #0a0e14; border: 1px solid #1f2937; border-radius: 6px; padding: 12px;">
            <div style="font-size: 11px; color: #00F0FF; font-weight: 600; margin-bottom: 8px; text-transform: uppercase;">
              Timestamped Chapters (${meta.chapters.length})
            </div>
            <div style="max-height: 120px; overflow-y: auto;">
              ${meta.chapters.length > 0 ? meta.chapters.map(ch => `
                <div style="display: flex; justify-content: space-between; font-size: 11px; padding: 3px 0; border-bottom: 1px solid #1f2937;">
                  <span style="color: #e5e7eb;">${ch.title}</span>
                  <span style="color: #9ca3af; font-family: monospace;">${ch.start_time_seconds}s</span>
                </div>
              `).join('') : '<div style="font-size: 11px; color: #6b7280;">No chapter marks embedded.</div>'}
            </div>
          </div>

          <div style="background: #0a0e14; border: 1px solid #1f2937; border-radius: 6px; padding: 12px;">
            <div style="font-size: 11px; color: #00F0FF; font-weight: 600; margin-bottom: 8px; text-transform: uppercase;">
              Subtitles & Captions Available (${meta.subtitles_available.length})
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 4px; max-height: 120px; overflow-y: auto;">
              ${meta.subtitles_available.length > 0 ? meta.subtitles_available.map(sub => `
                <span style="background: #1f2937; color: #e5e7eb; font-size: 10px; padding: 2px 6px; border-radius: 3px;">
                  ${sub.language_name}
                </span>
              `).join('') : '<div style="font-size: 11px; color: #6b7280;">No caption tracks listed.</div>'}
            </div>
          </div>
        </div>

        <!-- Action Row -->
        <div style="display: flex; gap: 12px; justify-content: flex-end; padding-top: 10px; border-top: 1px solid #1f2937;">
          <button id="om-btn-quick-ref-register" data-url="${meta.url}" style="padding: 8px 16px; background: #1e3a8a; color: #93c5fd; border: 1px solid #3b82f6; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600;">
            Register as Reference Asset
          </button>
          <button id="om-btn-goto-import" data-url="${meta.url}" style="padding: 8px 16px; background: #00F0FF; color: #050B14; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600;">
            Proceed to Authorized Import &rarr;
          </button>
        </div>
      </div>
    `;
  }

  renderSearchResults() {
    return `
      <div style="background: #121820; border: 1px solid #1f2937; border-radius: 8px; padding: 18px;">
        <h3 style="font-size: 13px; font-weight: 600; color: #e5e7eb; margin: 0 0 14px 0;">
          Search Results (${this.searchResults.length} videos found)
        </h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px;">
          ${this.searchResults.map(res => `
            <div style="background: #0a0e14; border: 1px solid #1f2937; border-radius: 6px; overflow: hidden; display: flex; flex-direction: column;">
              <img src="${res.thumbnail_url}" style="width: 100%; aspect-ratio: 16/9; object-fit: cover;">
              <div style="padding: 10px; flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                  <div style="font-size: 12px; font-weight: 600; color: #fff; line-height: 1.3; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                    ${res.title}
                  </div>
                  <div style="font-size: 11px; color: #9ca3af; margin-bottom: 6px;">${res.author} • ${res.duration_seconds}s</div>
                </div>
                <button class="om-btn-select-search" data-url="${res.url}" style="padding: 6px 10px; background: #1f2937; color: #00F0FF; border: 1px solid #374151; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: 600; text-align: center;">
                  Inspect & Analyze
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  renderImportTab() {
    return `
      <div style="max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px;">
        <div style="background: #121820; border: 1px solid #1f2937; border-radius: 8px; padding: 22px;">
          <h3 style="font-size: 14px; font-weight: 600; color: #00F0FF; margin-top: 0; margin-bottom: 14px; text-transform: uppercase;">
            Authorized Media Acquisition & Permission Certification
          </h3>

          <!-- Notice on Copyright & Permissions -->
          <div style="background: #1e293b; border-left: 4px solid #00F0FF; padding: 12px 16px; border-radius: 4px; margin-bottom: 18px; font-size: 12px; color: #cbd5e1; line-height: 1.5;">
            <strong>Compliance Policy:</strong> The studio does not bypass DRM or platform access restrictions. Downloading requires declaring valid permissions (user-owned, creator-authorized, CC, or public domain). Material marked <em>Reference-Only</em> is registered for structural analysis without downloading protected streams.
          </div>

          <!-- URL / File Input -->
          <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px;">
            <label style="font-size: 12px; font-weight: 600; color: #e5e7eb;">Media Source URL or Local File Path:</label>
            <input type="text" id="om-import-url" value="${this.inspectedMetadata ? this.inspectedMetadata.url : ''}" placeholder="https://www.youtube.com/watch?v=... or /path/to/local/video.mp4" style="padding: 10px 14px; background: #0a0e14; border: 1px solid #374151; border-radius: 6px; color: #fff; font-size: 13px;">
          </div>

          <!-- Permission Declaration Selector -->
          <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px;">
            <label style="font-size: 12px; font-weight: 600; color: #e5e7eb;">Permission & Rights Declaration:</label>
            <select id="om-permission-select" style="padding: 10px 14px; background: #0a0e14; border: 1px solid #374151; border-radius: 6px; color: #fff; font-size: 13px;">
              <option value="reference_only">REFERENCE ONLY — Research & Structural Analysis (No Production Use)</option>
              <option value="user_owned">USER OWNED — 100% Created or Owned by User</option>
              <option value="creator_authorized">CREATOR AUTHORIZED — Direct License / Written Consent Acquired</option>
              <option value="creative_commons">CREATIVE COMMONS — Published under CC-BY / CC-BY-SA / CC0</option>
              <option value="public_domain">PUBLIC DOMAIN — Media in Public Domain</option>
            </select>
          </div>

          <!-- Media Type & Formats -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
            <div style="display: flex; flex-direction: column; gap: 6px;">
              <label style="font-size: 12px; font-weight: 600; color: #e5e7eb;">Import Target:</label>
              <select id="om-import-type" style="padding: 10px 14px; background: #0a0e14; border: 1px solid #374151; border-radius: 6px; color: #fff; font-size: 13px;">
                <option value="video">Full Video & Audio</option>
                <option value="audio_only">Audio-Only Extraction</option>
              </select>
            </div>

            <div style="display: flex; flex-direction: column; gap: 6px;">
              <label style="font-size: 12px; font-weight: 600; color: #e5e7eb;">Resolution / Audio Format:</label>
              <select id="om-import-format" style="padding: 10px 14px; background: #0a0e14; border: 1px solid #374151; border-radius: 6px; color: #fff; font-size: 13px;">
                <option value="1080p">1080p (Full HD MP4)</option>
                <option value="720p">720p (HD MP4)</option>
                <option value="480p">480p (Standard MP4)</option>
                <option value="wav">WAV (Lossless 48kHz PCM)</option>
                <option value="mp3">MP3 (320kbps High Quality)</option>
                <option value="flac">FLAC (Lossless)</option>
              </select>
            </div>
          </div>

          <!-- Permission Notes -->
          <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px;">
            <label style="font-size: 12px; font-weight: 600; color: #e5e7eb;">Attribution & Permission Notes:</label>
            <input type="text" id="om-permission-notes" placeholder="Author name, license link, or written consent reference..." style="padding: 8px 14px; background: #0a0e14; border: 1px solid #374151; border-radius: 6px; color: #fff; font-size: 12px;">
          </div>

          <!-- Action Button -->
          <button id="om-btn-execute-import" style="width: 100%; padding: 12px; background: #00F0FF; color: #050B14; font-weight: 700; font-size: 14px; border: none; border-radius: 6px; cursor: pointer;">
            Execute Authorized Acquisition & Ingestion
          </button>
        </div>

        <!-- Import Result Box -->
        <div id="om-import-result-box" style="display: none; background: #121820; border: 1px solid #1f2937; border-radius: 8px; padding: 18px;">
          <h4 style="font-size: 13px; font-weight: 600; color: #38bdf8; margin-top: 0;">Ingestion Status</h4>
          <div id="om-import-status-text" style="font-size: 12px; color: #e5e7eb;"></div>
        </div>
      </div>
    `;
  }

  renderReferenceTab() {
    return `
      <div style="max-width: 1000px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px;">
        <div style="background: #121820; border: 1px solid #1f2937; border-radius: 8px; padding: 20px;">
          <h3 style="font-size: 14px; font-weight: 600; color: #00F0FF; margin-top: 0; margin-bottom: 12px; text-transform: uppercase;">
            Reference Video Multimodal Deconstruction & AI Director Bridge
          </h3>
          <p style="font-size: 12px; color: #9ca3af; margin-bottom: 16px;">
            Analyze reference media to extract structural grammar (Average Shot Length, pacing curve, color contrast, camera motions) and formulate an original production plan.
          </p>

          <div style="display: flex; gap: 10px; margin-bottom: 16px;">
            <select id="om-ref-asset-select" style="flex: 1; padding: 10px 14px; background: #0a0e14; border: 1px solid #374151; border-radius: 6px; color: #fff; font-size: 13px;">
              ${this.libraryAssets.map(a => `
                <option value="${a.asset_id}">${a.display_name} (${a.media_type}) [${a.permission_tier}]</option>
              `).join('')}
            </select>
            <button id="om-btn-run-analysis" style="padding: 10px 20px; background: #00F0FF; color: #050B14; font-weight: 600; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
              Deconstruct Reference
            </button>
          </div>
        </div>

        <!-- Analysis Display -->
        <div id="om-analysis-display" style="display: none; background: #121820; border: 1px solid #1f2937; border-radius: 8px; padding: 20px;">
          <div id="om-analysis-content"></div>
        </div>
      </div>
    `;
  }

  renderLibraryTab() {
    const filtered = this.libraryAssets.filter(a => {
      if (this.activeFilter !== "ALL" && a.permission_tier !== this.activeFilter.toLowerCase()) return false;
      if (this.librarySearch && !a.display_name.toLowerCase().includes(this.librarySearch.toLowerCase())) return false;
      return true;
    });

    return `
      <div style="max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px;">
        <!-- Filters & Search Toolbar -->
        <div style="display: flex; justify-content: space-between; align-items: center; background: #121820; border: 1px solid #1f2937; border-radius: 8px; padding: 14px 18px;">
          <div style="display: flex; gap: 8px;">
            <button class="om-lib-filter ${this.activeFilter === 'ALL' ? 'active' : ''}" data-filter="ALL" style="${this.getFilterStyle('ALL')}">All Assets (${this.libraryAssets.length})</button>
            <button class="om-lib-filter ${this.activeFilter === 'reference_only' ? 'active' : ''}" data-filter="reference_only" style="${this.getFilterStyle('reference_only')}">Reference Only</button>
            <button class="om-lib-filter ${this.activeFilter === 'editing_permitted' ? 'active' : ''}" data-filter="editing_permitted" style="${this.getFilterStyle('editing_permitted')}">Editing Permitted</button>
            <button class="om-lib-filter ${this.activeFilter === 'commercial_permitted' ? 'active' : ''}" data-filter="commercial_permitted" style="${this.getFilterStyle('commercial_permitted')}">Commercial Cleared</button>
          </div>
          <div style="display: flex; gap: 10px; width: 280px;">
            <input type="text" id="om-lib-search-input" value="${this.librarySearch}" placeholder="Filter library..." style="width: 100%; padding: 6px 12px; background: #0a0e14; border: 1px solid #374151; border-radius: 4px; color: #fff; font-size: 12px;">
          </div>
        </div>

        <!-- Library Asset Grid -->
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;">
          ${filtered.map(a => this.renderLibraryCard(a)).join('')}
        </div>
      </div>
    `;
  }

  getFilterStyle(f) {
    const isAct = this.activeFilter === f;
    return `
      padding: 5px 12px;
      font-size: 11px;
      font-weight: 600;
      border: 1px solid ${isAct ? '#00F0FF' : '#374151'};
      background: ${isAct ? '#00F0FF22' : '#0a0e14'};
      color: ${isAct ? '#00F0FF' : '#9ca3af'};
      border-radius: 4px;
      cursor: pointer;
    `;
  }

  renderLibraryCard(asset) {
    const isRefOnly = asset.permission_tier === "reference_only";
    const badgeBg = isRefOnly ? "#1e3a8a" : (asset.permission_tier === "commercial_permitted" ? "#065f46" : "#854d0e");
    const badgeColor = isRefOnly ? "#bfdbfe" : (asset.permission_tier === "commercial_permitted" ? "#a7f3d0" : "#fef08a");

    return `
      <div style="background: #121820; border: 1px solid #1f2937; border-radius: 6px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; gap: 10px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="background: ${badgeBg}; color: ${badgeColor}; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 3px; text-transform: uppercase;">
              ${asset.permission_tier}
            </span>
            <span style="font-size: 10px; color: #9ca3af;">${asset.media_type}</span>
          </div>
          <div style="font-size: 13px; font-weight: 600; color: #fff; line-height: 1.3; margin-bottom: 4px;">
            ${asset.display_name}
          </div>
          <div style="font-size: 11px; color: #6b7280;">Author/Source: ${asset.author || 'Unknown'}</div>
        </div>

        <div style="font-size: 10px; color: #4b5563; font-family: monospace; word-break: break-all;">
          ${asset.storage_path.startsWith('http') ? `<a href="${asset.storage_path}" target="_blank" style="color: #38bdf8;">${asset.storage_path.slice(0, 45)}...</a>` : asset.original_filename}
        </div>
      </div>
    `;
  }

  async loadUnifiedLibrary() {
    try {
      const state = store.getState();
      const projId = (state.activeProject && state.activeProject.project_id) || "88e54cd2-6a21-4e8a-a751-35f177c0964d";
      const res = await api.getUnifiedLibrary(projId);
      if (res && res.assets) {
        this.libraryAssets = res.assets;
        if (this.activeSubtab === "library") {
          this.render();
        }
      }
    } catch (e) {
      console.warn("Could not load unified library:", e);
    }
  }

  bindEvents() {
    // Subtab switching
    this.mount.querySelectorAll(".om-subtab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        this.activeSubtab = btn.getAttribute("data-subtab");
        this.render();
      });
    });

    // Inspect URL
    const btnInspect = this.mount.querySelector("#om-btn-inspect");
    if (btnInspect) {
      btnInspect.addEventListener("click", async () => {
        const urlInput = this.mount.querySelector("#om-inspect-url-input");
        const url = urlInput ? urlInput.value.trim() : "";
        if (!url) return alert("Please paste a valid YouTube URL.");
        btnInspect.textContent = "Inspecting...";
        try {
          const res = await api.inspectOnlineMedia(url);
          if (res && res.metadata) {
            this.inspectedMetadata = res.metadata;
            this.render();
          }
        } catch (e) {
          alert(`Inspection error: ${e.message}`);
        } finally {
          btnInspect.textContent = "Inspect URL";
        }
      });
    }

    // Search YouTube
    const btnSearch = this.mount.querySelector("#om-btn-search");
    if (btnSearch) {
      btnSearch.addEventListener("click", async () => {
        const qInput = this.mount.querySelector("#om-search-query-input");
        const query = qInput ? qInput.value.trim() : "";
        if (!query) return alert("Please enter search keywords.");
        btnSearch.textContent = "Searching...";
        try {
          const res = await api.searchOnlineMedia(query, 6);
          if (res && res.results) {
            this.searchResults = res.results;
            this.render();
          }
        } catch (e) {
          alert(`Search error: ${e.message}`);
        } finally {
          btnSearch.textContent = "Search YouTube";
        }
      });
    }

    // Select search result
    this.mount.querySelectorAll(".om-btn-select-search").forEach(btn => {
      btn.addEventListener("click", async () => {
        const url = btn.getAttribute("data-url");
        try {
          const res = await api.inspectOnlineMedia(url);
          if (res && res.metadata) {
            this.inspectedMetadata = res.metadata;
            this.render();
          }
        } catch (e) {
          alert(`Select error: ${e.message}`);
        }
      });
    });

    // Quick Register Reference Asset
    const btnQuickRef = this.mount.querySelector("#om-btn-quick-ref-register");
    if (btnQuickRef) {
      btnQuickRef.addEventListener("click", async () => {
        const url = btnQuickRef.getAttribute("data-url");
        const state = store.getState();
        const projId = (state.activeProject && state.activeProject.project_id) || "88e54cd2-6a21-4e8a-a751-35f177c0964d";
        try {
          btnQuickRef.textContent = "Registering...";
          const res = await api.importOnlineMedia({
            url: url,
            media_type: "video",
            permission_declaration: "reference_only",
            destination_role: "REFERENCE_VIDEO",
            project_id: projId
          });
          alert("Reference Asset registered successfully in Unified Library!");
          this.loadUnifiedLibrary();
        } catch (e) {
          alert(`Registration error: ${e.message}`);
        } finally {
          btnQuickRef.textContent = "Register as Reference Asset";
        }
      });
    }

    // Proceed to Import
    const btnGotoImport = this.mount.querySelector("#om-btn-goto-import");
    if (btnGotoImport) {
      btnGotoImport.addEventListener("click", () => {
        this.activeSubtab = "import";
        this.render();
      });
    }

    // Execute Import
    const btnExecuteImport = this.mount.querySelector("#om-btn-execute-import");
    if (btnExecuteImport) {
      btnExecuteImport.addEventListener("click", async () => {
        const url = this.mount.querySelector("#om-import-url").value.trim();
        const perm = this.mount.querySelector("#om-permission-select").value;
        const mType = this.mount.querySelector("#om-import-type").value;
        const fmt = this.mount.querySelector("#om-import-format").value;
        const notes = this.mount.querySelector("#om-permission-notes").value;
        const state = store.getState();
        const projId = (state.activeProject && state.activeProject.project_id) || "88e54cd2-6a21-4e8a-a751-35f177c0964d";

        if (!url) return alert("Please provide a media URL or path.");

        btnExecuteImport.textContent = "Importing & Verifying...";
        const resBox = this.mount.querySelector("#om-import-result-box");
        const statusText = this.mount.querySelector("#om-import-status-text");

        try {
          const res = await api.importOnlineMedia({
            url: url,
            media_type: mType,
            resolution: fmt.includes("p") ? fmt : "1080p",
            audio_format: fmt.includes("p") ? "wav" : fmt,
            permission_declaration: perm,
            permission_notes: notes,
            destination_role: mType === "audio_only" ? "MUSIC" : "SOURCE_FOOTAGE",
            project_id: projId
          });

          if (resBox && statusText) {
            resBox.style.display = "block";
            statusText.innerHTML = `
              <div style="color: #4ade80; font-weight: 600; margin-bottom: 6px;">✓ Ingestion Successful</div>
              <div>Status: ${res.import_result.status}</div>
              <div>Permission Tier: <strong>${res.import_result.permission_tier}</strong></div>
              <div>Asset ID: <code>${res.import_result.asset_id}</code></div>
              <div>Local Storage: <code>${res.import_result.local_path}</code></div>
            `;
          }
          this.loadUnifiedLibrary();
        } catch (e) {
          alert(`Import failed: ${e.message}`);
        } finally {
          btnExecuteImport.textContent = "Execute Authorized Acquisition & Ingestion";
        }
      });
    }

    // Reference Analysis
    const btnRunAnalysis = this.mount.querySelector("#om-btn-run-analysis");
    if (btnRunAnalysis) {
      btnRunAnalysis.addEventListener("click", async () => {
        const select = this.mount.querySelector("#om-ref-asset-select");
        const assetId = select ? select.value : null;
        if (!assetId) return alert("Please select an asset to deconstruct.");

        btnRunAnalysis.textContent = "Analyzing Frames & Cuts...";
        const disp = this.mount.querySelector("#om-analysis-display");
        const content = this.mount.querySelector("#om-analysis-content");

        try {
          const res = await api.analyzeReference(assetId);
          if (res && res.reference_profile) {
            const p = res.reference_profile;
            disp.style.display = "block";
            content.innerHTML = `
              <h3 style="font-size: 16px; color: #fff; margin-top: 0;">Style Profile: ${p.name}</h3>
              <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px;">
                <div style="background: #0a0e14; padding: 10px; border-radius: 4px;">
                  <div style="font-size: 10px; color: #9ca3af;">AVERAGE SHOT LENGTH</div>
                  <div style="font-size: 18px; font-weight: 700; color: #00F0FF;">${p.editing_style.average_shot_length_sec}s</div>
                </div>
                <div style="background: #0a0e14; padding: 10px; border-radius: 4px;">
                  <div style="font-size: 10px; color: #9ca3af;">CUT FREQUENCY</div>
                  <div style="font-size: 18px; font-weight: 700; color: #00F0FF;">${p.editing_style.cut_frequency_cpm} CPM</div>
                </div>
                <div style="background: #0a0e14; padding: 10px; border-radius: 4px;">
                  <div style="font-size: 10px; color: #9ca3af;">PACING STYLE</div>
                  <div style="font-size: 18px; font-weight: 700; color: #00F0FF;">${p.editing_style.pacing}</div>
                </div>
                <div style="background: #0a0e14; padding: 10px; border-radius: 4px;">
                  <div style="font-size: 10px; color: #9ca3af;">PRIMARY MOTION</div>
                  <div style="font-size: 18px; font-weight: 700; color: #00F0FF;">${p.visual_style.primary_camera_motion}</div>
                </div>
              </div>

              <!-- Color Palette Swatches -->
              <div style="margin-bottom: 16px;">
                <div style="font-size: 11px; color: #9ca3af; margin-bottom: 6px; font-weight: 600;">DOMINANT 5-COLOR PALETTE</div>
                <div style="display: flex; gap: 8px;">
                  ${(p.visual_style.dominant_palette_hex || []).map(hex => `
                    <div style="flex: 1; height: 32px; background: ${hex}; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #000; font-weight: 700; text-shadow: 0 0 2px #fff;">
                      ${hex}
                    </div>
                  `).join('')}
                </div>
              </div>

              <!-- AI Director Bridge Button -->
              <div style="padding-top: 14px; border-top: 1px solid #1f2937; display: flex; justify-content: flex-end;">
                <button id="om-btn-inspire-brief" data-asset-id="${assetId}" style="padding: 10px 18px; background: #00F0FF; color: #050B14; font-weight: 700; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">
                  Generate Inspired Production Plan &rarr;
                </button>
              </div>
              <div id="om-inspire-plan-output" style="margin-top: 14px; display: none;"></div>
            `;

            // Bind Inspire Button
            const btnInspire = content.querySelector("#om-btn-inspire-brief");
            if (btnInspire) {
              btnInspire.addEventListener("click", async () => {
                const topic = prompt("Enter original documentary topic:", "ऑक्टोपस के तीन दिल क्यों होते हैं?");
                if (!topic) return;
                btnInspire.textContent = "Synthesizing Original Plan...";
                try {
                  const planRes = await api.inspireProduction(assetId, topic);
                  const planOut = content.querySelector("#om-inspire-plan-output");
                  planOut.style.display = "block";
                  planOut.innerHTML = `
                    <div style="background: #0a0e14; border: 1px solid #00F0FF; border-radius: 6px; padding: 14px;">
                      <h4 style="color: #00F0FF; margin-top: 0; font-size: 13px;">Inspired Original Production Plan</h4>
                      <p style="font-size: 11px; color: #9ca3af;">${planRes.production_plan.originality_hygiene}</p>
                      <div style="font-size: 11px; color: #e5e7eb; max-height: 200px; overflow-y: auto;">
                        ${planRes.production_plan.planned_scene_structure.map(s => `
                          <div style="padding: 4px 0; border-bottom: 1px solid #1f2937;">
                            <strong>Scene ${s.scene_number} (${s.target_duration_sec}s):</strong> ${s.prompt_direction}
                          </div>
                        `).join('')}
                      </div>
                    </div>
                  `;
                } catch (e) {
                  alert(`Plan generation error: ${e.message}`);
                } finally {
                  btnInspire.textContent = "Generate Inspired Production Plan →";
                }
              });
            }
          }
        } catch (e) {
          alert(`Analysis error: ${e.message}`);
        } finally {
          btnRunAnalysis.textContent = "Deconstruct Reference";
        }
      });
    }

    // Library Filter buttons
    this.mount.querySelectorAll(".om-lib-filter").forEach(btn => {
      btn.addEventListener("click", () => {
        this.activeFilter = btn.getAttribute("data-filter");
        this.render();
      });
    });

    // Library Search input
    const libSearch = this.mount.querySelector("#om-lib-search-input");
    if (libSearch) {
      libSearch.addEventListener("input", (e) => {
        this.librarySearch = e.target.value;
        this.render();
      });
    }
  }
}

