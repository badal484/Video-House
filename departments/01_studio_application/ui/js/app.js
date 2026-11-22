/**
 * Master Application Orchestrator & Router.
 * Initializes the studio shell, binds specialized workspaces, and coordinates state.
 */

import { store } from "./state.js";
import { shortcutManager } from "./shortcuts.js";
import { CommandPaletteComponent } from "./components/command_palette.js";
import { NotificationsComponent } from "./components/notifications.js";

// Import Workspaces
import { HomeDashboardWorkspace } from "./workspaces/home_dashboard.js";
import { CreativeWorkspace } from "./workspaces/creative_workspace.js";
import { EditingWorkspace } from "./workspaces/editing_workspace.js";
import { AIDirectorWorkspace } from "./workspaces/ai_director_workspace.js";
import { AgentCenterWorkspace } from "./workspaces/agent_center_workspace.js";
import { GenerationWorkspace } from "./workspaces/generation_workspace.js";
import { MotionGraphicsWorkspace } from "./workspaces/motion_graphics_workspace.js";
import { VFXWorkspace } from "./workspaces/vfx_workspace.js";
import { AnimationWorkspace } from "./workspaces/animation_workspace.js";
import { AudioWorkspace } from "./workspaces/audio_workspace.js";
import { ColorWorkspace } from "./workspaces/color_workspace.js";
import { LocalizationWorkspace } from "./workspaces/localization_workspace.js";
import { RenderingWorkspace } from "./workspaces/rendering_workspace.js";
import { ProjectSettingsWorkspace } from "./workspaces/project_settings.js";
import { OnlineMediaWorkspace } from "./workspaces/online_media_workspace.js";
import { DeepIntelligenceWorkspace } from "./workspaces/deep_intelligence_workspace.js";

export class StudioApplication {
  constructor() {
    this.mainMount = document.querySelector("#main-viewport-mount");
    this.workspaceTabs = document.querySelectorAll(".ws-tab");
    this.currentWorkspaceInstance = null;

    this.initGlobalComponents();
    this.bindGlobalEvents();
    this.loadInitialContext();
    this.routeWorkspace(store.getState().activeWorkspace);
  }

  async loadInitialContext() {
    try {
      const { api } = await import("./api_client.js");
      const projectsRes = await api.listProjects();
      if (projectsRes && projectsRes.projects && projectsRes.projects.length > 0) {
        store.setState({ projects: projectsRes.projects });
        const activeProj = projectsRes.projects.find(p => p.project_id === "88e54cd2-6a21-4e8a-a751-35f177c0964d") || projectsRes.projects[0];
        store.setState({
          activeProjectId: activeProj.project_id,
          activeProject: activeProj
        });
        const assetsRes = await api.listAssets(activeProj.project_id);
        if (assetsRes && assetsRes.assets) {
          store.setState({ assets: assetsRes.assets });
          const master = assetsRes.assets.find(a => (a.display_name && a.display_name.includes("Master")) || (a.original_filename && a.original_filename.includes("master")));
          if (master) {
            store.setState({ selectedAssetId: master.asset_id });
          } else if (assetsRes.assets.length > 0) {
            store.setState({ selectedAssetId: assetsRes.assets[0].asset_id });
          }
        }
      }
    } catch (err) {
      console.log("Initial context load error:", err);
    }
  }

  initGlobalComponents() {
    new CommandPaletteComponent();
    new NotificationsComponent();
  }

  bindGlobalEvents() {
    // Top Bar Workspace Tabs
    this.workspaceTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        const targetWs = tab.getAttribute("data-ws");
        store.setWorkspace(targetWs);
      });
    });

    // Subscribe to workspace changes in store
    store.subscribe("activeWorkspace", (state) => {
      this.updateActiveTabHighlight(state.activeWorkspace);
      this.routeWorkspace(state.activeWorkspace);
    });

    // Subscribe to project title updates
    store.subscribe("activeProject", (state) => {
      const titleBadge = document.querySelector("#topbar-project-title");
      if (titleBadge) {
        titleBadge.textContent = state.activeProject ? state.activeProject.name : "No Project Active";
      }
    });

    // Subscribe to save status indicator
    store.subscribe("saveStatus", (state) => {
      const savePill = document.querySelector("#topbar-save-status");
      if (savePill) {
        savePill.className = `save-indicator ${state.saveStatus}`;
        savePill.textContent = state.saveStatus === "saving" ? "Autosaving..." : state.saveStatus === "unsaved" ? "● Unsaved" : "✓ Saved";
      }
    });

    // Logo click returns home
    const logo = document.querySelector("#studio-logo-btn");
    if (logo) {
      logo.addEventListener("click", () => store.setWorkspace("home"));
    }
  }

  updateActiveTabHighlight(activeWs) {
    this.workspaceTabs.forEach(tab => {
      if (tab.getAttribute("data-ws") === activeWs) {
        tab.classList.add("active");
      } else {
        tab.classList.remove("active");
      }
    });
  }

  routeWorkspace(workspaceId) {
    this.mainMount.innerHTML = "";
    switch (workspaceId) {
      case "home":
        this.currentWorkspaceInstance = new HomeDashboardWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "creative":
        this.currentWorkspaceInstance = new CreativeWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "editing":
        this.currentWorkspaceInstance = new EditingWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "director":
        this.currentWorkspaceInstance = new AIDirectorWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "agents":
        this.currentWorkspaceInstance = new AgentCenterWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "generation":
        this.currentWorkspaceInstance = new GenerationWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "motion":
        this.currentWorkspaceInstance = new MotionGraphicsWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "vfx":
        this.currentWorkspaceInstance = new VFXWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "animation":
        this.currentWorkspaceInstance = new AnimationWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "audio":
        this.currentWorkspaceInstance = new AudioWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "color":
        this.currentWorkspaceInstance = new ColorWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "localization":
        this.currentWorkspaceInstance = new LocalizationWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "rendering":
        this.currentWorkspaceInstance = new RenderingWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "online_media":
        this.currentWorkspaceInstance = new OnlineMediaWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "deep_intelligence":
        this.currentWorkspaceInstance = new DeepIntelligenceWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      case "settings":
        this.currentWorkspaceInstance = new ProjectSettingsWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
        break;
      default:
        this.currentWorkspaceInstance = new HomeDashboardWorkspace(this.mainMount);
        this.currentWorkspaceInstance.mount();
    }
  }
}

// Bootstrap Application on DOMContentLoaded
window.addEventListener("DOMContentLoaded", () => {
  window.studioApp = new StudioApplication();
});

