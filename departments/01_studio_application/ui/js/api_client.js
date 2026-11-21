/**
 * Strongly-Typed Asynchronous HTTP API Client.
 * Connects the UI directly to backend endpoints across all 14 departments.
 */

export class APIClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const defaultHeaders = {
      "Content-Type": "application/json",
      "Accept": "application/json"
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers
      }
    };

    if (config.body && typeof config.body === "object" && !(config.body instanceof FormData)) {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        let errDetail = response.statusText;
        try {
          const errJson = await response.json();
          errDetail = errJson.detail || errJson.message || errDetail;
        } catch (_) {}
        const error = new Error(`API Error [${response.status}]: ${errDetail}`);
        error.status = response.status;
        throw error;
      }
      return await response.json();
    } catch (err) {
      console.error(`[APIClient] Request failed for ${endpoint}:`, err);
      throw err;
    }
  }

  // ---------------- Project Management Endpoints (Dept 02) ----------------
  async listProjects() {
    return this.request("/api/v1/projects");
  }

  async getProject(projectId) {
    return this.request(`/api/v1/projects/${projectId}`);
  }

  async createProject(name, settings = {}) {
    return this.request("/api/v1/projects", {
      method: "POST",
      body: { name, settings }
    });
  }

  async updateProject(projectId, name, settings) {
    return this.request(`/api/v1/projects/${projectId}`, {
      method: "PATCH",
      body: { name, settings }
    });
  }

  async deleteProject(projectId) {
    return this.request(`/api/v1/projects/${projectId}`, {
      method: "DELETE"
    });
  }

  async getProjectTemplates() {
    return this.request("/api/v1/projects/templates");
  }

  async saveProjectVersion(projectId, versionName, notes = "") {
    return this.request(`/api/v1/projects/${projectId}/versions`, {
      method: "POST",
      body: { version_name: versionName, notes }
    });
  }

  async listProjectVersions(projectId) {
    return this.request(`/api/v1/projects/${projectId}/versions`);
  }

  async restoreProjectVersion(projectId, versionId) {
    return this.request(`/api/v1/projects/${projectId}/versions/${versionId}/restore`, {
      method: "POST"
    });
  }

  // ---------------- Media Assets Endpoints (Dept 03 & 21) ----------------
  async listAssets(projectId) {
    return this.request(`/api/v1/projects/${projectId}/assets`);
  }

  async getAssetDetail(projectId, assetId) {
    return this.request(`/api/v1/projects/${projectId}/assets/${assetId}`);
  }

  async importLocalFile(projectId, filePath, displayName, roles = ["SOURCE_FOOTAGE"]) {
    return this.request(`/api/v1/projects/${projectId}/assets/import-local`, {
      method: "POST",
      body: { file_path: filePath, display_name: displayName, roles }
    });
  }

  async deleteAsset(projectId, assetId) {
    return this.request(`/api/v1/projects/${projectId}/assets/${assetId}`, {
      method: "DELETE"
    });
  }

  // ---------------- AI Director Endpoints (Dept 06 & 07) ----------------
  async createBrief(projectId, prompt, options = {}) {
    return this.request(`/api/v1/projects/${projectId}/creative/brief`, {
      method: "POST",
      body: { prompt, ...options }
    });
  }

  async getBrief(projectId) {
    return this.request(`/api/v1/projects/${projectId}/creative/brief`);
  }

  async createConcepts(projectId) {
    return this.request(`/api/v1/projects/${projectId}/creative/concepts`, { method: "POST" });
  }

  async getConcepts(projectId) {
    return this.request(`/api/v1/projects/${projectId}/creative/concepts`);
  }

  async selectConcept(projectId, conceptId) {
    return this.request(`/api/v1/projects/${projectId}/creative/concepts/${conceptId}/select`, { method: "POST" });
  }

  async createScript(projectId, selectedConceptId = null, notes = null) {
    return this.request(`/api/v1/projects/${projectId}/creative/script`, {
      method: "POST",
      body: { selected_concept_id: selectedConceptId, notes }
    });
  }

  async getScript(projectId) {
    return this.request(`/api/v1/projects/${projectId}/creative/script`);
  }

  async planShots(projectId) {
    return this.request(`/api/v1/projects/${projectId}/creative/shots`, { method: "POST", body: {} });
  }

  async getShots(projectId) {
    return this.request(`/api/v1/projects/${projectId}/creative/shots`);
  }

  async generateStoryboard(projectId) {
    return this.request(`/api/v1/projects/${projectId}/creative/storyboard`, { method: "POST", body: {} });
  }

  async getStoryboard(projectId) {
    return this.request(`/api/v1/projects/${projectId}/creative/storyboard`);
  }

  async approveEntity(projectId, entityType, entityId, notes = "") {
    return this.request(`/api/v1/projects/${projectId}/creative/approve`, {
      method: "POST",
      body: { entity_type: entityType, entity_id: entityId, status: "APPROVED", notes }
    });
  }

  // ---------------- Video Editing Endpoints (Dept 08 / OTIO) ----------------
  async createTimeline(projectId, name = "Main Timeline", fps = 24.0) {
    return this.request(`/api/v1/editing/projects/${projectId}/timelines`, {
      method: "POST",
      body: { name, fps }
    });
  }

  async getTimeline(timelineId) {
    return this.request(`/api/v1/editing/timelines/${timelineId}`);
  }

  async splitClip(timelineId, clipId, splitSeconds) {
    return this.request(`/api/v1/editing/timelines/${timelineId}/clips/${clipId}/split`, {
      method: "POST",
      body: { split_time: splitSeconds }
    });
  }

  async rippleDeleteClip(timelineId, clipId) {
    return this.request(`/api/v1/editing/timelines/${timelineId}/clips/${clipId}/ripple-delete`, {
      method: "POST"
    });
  }

  async undoTimeline(timelineId) {
    return this.request(`/api/v1/editing/timelines/${timelineId}/undo`, { method: "POST" });
  }

  async redoTimeline(timelineId) {
    return this.request(`/api/v1/editing/timelines/${timelineId}/redo`, { method: "POST" });
  }

  // ---------------- Motion Graphics (Dept 09) ----------------
  async getMotionPresets() {
    return this.request("/api/v1/motion-graphics/presets");
  }

  async instantiateMotionPreset(presetId, titleText = "TITLE", subtitleText = "SUBTITLE") {
    return this.request(`/api/v1/motion-graphics/presets/${presetId}/instantiate`, {
      method: "POST",
      body: { title_text: titleText, subtitle_text: subtitleText }
    });
  }

  // ---------------- AI Media Generation (Dept 15) ----------------
  async getGenerationProviders() {
    return this.request("/api/v1/generation/providers");
  }

  async compilePrompt(dimensions) {
    return this.request("/api/v1/generation/compile-prompt", {
      method: "POST",
      body: dimensions
    });
  }

  async createGenerationJob(payload) {
    return this.request("/api/v1/generation/jobs", {
      method: "POST",
      body: payload
    });
  }

  // ---------------- Audio Post-Production (Dept 14) ----------------
  async generateProceduralSFX(category, name, durationSeconds = 2.0) {
    return this.request("/api/v1/audio/sfx/generate", {
      method: "POST",
      body: { category, name, duration_seconds: durationSeconds }
    });
  }

  // ---------------- Color Grading & Restoration (Dept 16) ----------------
  async listColorGrades(projectId) {
    return this.request(`/api/v1/color/projects/${projectId}/grades`);
  }

  async recommendColorGrade(projectId, assetId, lookStyle = "TEAL_AND_ORANGE") {
    return this.request("/api/v1/color/recommend-grade", {
      method: "POST",
      body: { project_id: projectId, asset_id: assetId, look_style: lookStyle }
    });
  }

  // ---------------- Subtitles & Localization (Dept 17) ----------------
  async generateSubtitles(payload) {
    return this.request("/api/v1/localization/subtitles", {
      method: "POST",
      body: payload
    });
  }

  // ---------------- Rendering & QC (Depts 18 & 19) ----------------
  async getRenderProfiles() {
    return this.request("/api/v1/rendering/profiles");
  }

  async compileRenderPlan(projectId, profileNames) {
    return this.request("/api/v1/rendering/plan", {
      method: "POST",
      body: { project_id: projectId, profile_names: profileNames }
    });
  }

  async runQCAudit(projectId, assetId, policyName = "Strict Broadcast Specification") {
    return this.request("/api/v1/qc/audit", {
      method: "POST",
      body: { project_id: projectId, asset_id: assetId, policy_name: policyName }
    });
  }

  // ---------------- Telemetry & Layout (Dept 01) ----------------
  async getSystemTelemetry() {
    return this.request("/api/v1/system/telemetry");
  }

  async getWorkspaceLayout(workspaceId) {
    return this.request(`/api/v1/system/layout/${workspaceId}`);
  }

  async saveWorkspaceLayout(workspaceId, layout) {
    return this.request(`/api/v1/system/layout/${workspaceId}`, {
      method: "POST",
      body: { layout }
    });
  }
}

export const api = new APIClient();
