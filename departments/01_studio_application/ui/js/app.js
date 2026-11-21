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

export class StudioApplication {
  constructor() {
    this.mainMount = document.querySelector("#main-viewport-mount");
    this.workspaceTabs = document.querySelectorAll(".ws-tab");
    this.currentWorkspaceInstance = null;

    this.initGlobalComponents();
    this.bindGlobalEvents();
    this.routeWorkspace(store.getState().activeWorkspace);
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

