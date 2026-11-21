/**
 * Central Reactive State Store for the Studio Application.
 * Implements an observable state pattern with fine-grained subscription channels.
 */

export class StudioStore {
  constructor() {
    this.state = {
      // Navigation & Layout
      activeWorkspace: "home",
      layoutGeometry: {
        left_panel_width: 300,
        right_panel_width: 360,
        bottom_panel_height: 280
      },

      // Project Context
      projects: [],
      activeProjectId: null,
      activeProject: null,
      hasUnsavedChanges: false,
      saveStatus: "saved", // "saved" | "unsaved" | "saving"

      // Media Assets
      assets: [],
      selectedAssetId: null,
      assetFilterRole: "ALL",
      assetSearchQuery: "",

      // Editorial Timeline & Transport
      timeline: null,
      tracks: [
        { id: "v1", type: "VIDEO", name: "V1 Video", clips: [] },
        { id: "v2", type: "GRAPHICS", name: "V2 Graphics", clips: [] },
        { id: "a1", type: "AUDIO", name: "A1 Dialogue", clips: [] },
        { id: "a2", type: "AUDIO", name: "A2 Music", clips: [] }
      ],
      selectedClipId: null,
      playheadSeconds: 0.0,
      timelineDuration: 60.0,
      timelineFps: 24.0,
      isPlaying: false,
      playbackRate: 1.0,
      zoomLevel: 1.0,

      // AI Director State
      brief: null,
      concepts: [],
      selectedConceptId: null,
      script: null,
      shots: [],
      storyboard: [],
      approvals: [],

      // 12 Departmental Agents
      agents: [
        { id: "agent_director", name: "AI Director", dept: "06_creative_direction", status: "IDLE", task: "Awaiting brief", cost: 0.0 },
        { id: "agent_ingestion", name: "Media Ingestion", dept: "03_media_ingestion", status: "IDLE", task: "Demux & proxy ready", cost: 0.0 },
        { id: "agent_intelligence", name: "Media Intelligence", dept: "04_media_intelligence", status: "IDLE", task: "Scene detection standby", cost: 0.0 },
        { id: "agent_editor", name: "Editorial Assembly", dept: "08_video_editing", status: "IDLE", task: "Timeline conform active", cost: 0.0 },
        { id: "agent_motion", name: "Motion Graphics", dept: "09_motion_graphics", status: "IDLE", task: "SVG typography idle", cost: 0.0 },
        { id: "agent_vfx", name: "VFX Compositing", dept: "13_vfx_compositing", status: "IDLE", task: "Chroma keyer standing by", cost: 0.0 },
        { id: "agent_animation", name: "2D Animation", dept: "10_animation_2d", status: "IDLE", task: "Settei generator idle", cost: 0.0 },
        { id: "agent_3d", name: "3D Animation", dept: "11_animation_3d", status: "IDLE", task: "Blender integration online", cost: 0.0 },
        { id: "agent_audio", name: "Audio Production", dept: "14_audio_production", status: "IDLE", task: "DSP mixer ready (-14 LUFS)", cost: 0.0 },
        { id: "agent_generation", name: "Generative Router", dept: "15_ai_generation", status: "IDLE", task: "Capability router active", cost: 0.0 },
        { id: "agent_color", name: "Colorist Assistant", dept: "16_color_restoration", status: "IDLE", task: "ACEScg IDT ready", cost: 0.0 },
        { id: "agent_qc", name: "QC & Delivery", dept: "18_quality_control", status: "IDLE", task: "Preflight validator ready", cost: 0.0 }
      ],

      // Background Jobs & Telemetry
      jobs: [],
      telemetry: {
        storage: { free_gb: 38.0, percent_used: 92.0 },
        videotoolbox_acceleration: true,
        status: "HEALTHY"
      },
      notifications: []
    };

    this.listeners = new Map();
    this.autosaveTimeout = null;
  }

  getState() {
    return this.state;
  }

  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }
    this.listeners.get(key).add(callback);
    return () => this.listeners.get(key).delete(callback);
  }

  notify(key) {
    if (this.listeners.has(key)) {
      for (const callback of this.listeners.get(key)) {
        try {
          callback(this.state);
        } catch (e) {
          console.error(`Error in store listener for ${key}:`, e);
        }
      }
    }
    // Also notify global wildcard listeners
    if (this.listeners.has("*")) {
      for (const callback of this.listeners.get("*")) {
        callback(this.state);
      }
    }
  }

  setState(partialState, markUnsaved = false) {
    this.state = { ...this.state, ...partialState };
    if (markUnsaved && !this.state.hasUnsavedChanges) {
      this.state.hasUnsavedChanges = true;
      this.state.saveStatus = "unsaved";
      this.scheduleAutosave();
    }
    for (const key of Object.keys(partialState)) {
      this.notify(key);
    }
  }

  scheduleAutosave() {
    if (this.autosaveTimeout) clearTimeout(this.autosaveTimeout);
    this.autosaveTimeout = setTimeout(() => {
      this.triggerAutosave();
    }, 3000);
  }

  async triggerAutosave() {
    if (!this.state.activeProjectId || !this.state.hasUnsavedChanges) return;
    this.setState({ saveStatus: "saving" });
    try {
      // Simulate/trigger non-blocking state sync
      await new Promise(r => setTimeout(r, 600));
      this.setState({ hasUnsavedChanges: false, saveStatus: "saved" });
    } catch (_) {
      this.setState({ saveStatus: "unsaved" });
    }
  }

  // Helper Mutators
  setWorkspace(workspaceId) {
    this.setState({ activeWorkspace: workspaceId });
  }

  setPlayhead(seconds) {
    const clamped = Math.max(0, Math.min(seconds, this.state.timelineDuration));
    this.setState({ playheadSeconds: clamped });
  }

  togglePlayback() {
    this.setState({ isPlaying: !this.state.isPlaying });
  }

  addNotification(message, type = "info") {
    const notification = {
      id: Math.random().toString(36).substring(2, 9),
      message,
      type,
      timestamp: new Date().toLocaleTimeString()
    };
    const notifications = [notification, ...this.state.notifications.slice(0, 9)];
    this.setState({ notifications });
    return notification;
  }
}

export const store = new StudioStore();

