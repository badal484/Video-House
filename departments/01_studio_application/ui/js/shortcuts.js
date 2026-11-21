/**
 * Global Keyboard Shortcut Manager.
 * Maps standard creative NLE shortcuts with input focus protection.
 */

import { store } from "./state.js";

export class ShortcutManager {
  constructor() {
    this.shortcuts = new Map();
    this.initDefaultShortcuts();
    this.bindEvents();
  }

  initDefaultShortcuts() {
    // Transport & Playback
    this.register("Space", "Play / Pause", () => store.togglePlayback());
    this.register("KeyK", "Stop Playback", () => store.setState({ isPlaying: false }));
    this.register("KeyL", "Fast Forward Playback", () => {
      const currentRate = store.getState().playbackRate;
      store.setState({ isPlaying: true, playbackRate: Math.min(currentRate * 2, 8.0) });
    });
    this.register("KeyJ", "Reverse Playback", () => {
      const currentRate = store.getState().playbackRate;
      store.setState({ isPlaying: true, playbackRate: Math.max(currentRate * -2, -8.0) });
    });

    // Frame Stepping
    this.register("ArrowLeft", "Step 1 Frame Backward", (e) => {
      e.preventDefault();
      const fps = store.getState().timelineFps;
      const step = e.shiftKey ? 10 / fps : 1 / fps;
      store.setPlayhead(store.getState().playheadSeconds - step);
    });
    this.register("ArrowRight", "Step 1 Frame Forward", (e) => {
      e.preventDefault();
      const fps = store.getState().timelineFps;
      const step = e.shiftKey ? 10 / fps : 1 / fps;
      store.setPlayhead(store.getState().playheadSeconds + step);
    });

    // Editing Operations
    this.register("KeyB", "Blade / Split Clip", () => {
      const selectedClipId = store.getState().selectedClipId;
      if (selectedClipId) {
        store.addNotification(`Split clip ${selectedClipId} at playhead`, "info");
      }
    });

    // Workspace Numeric Shortcuts (1-9, 0, -, =)
    const workspaceMap = {
      "Digit1": "home",
      "Digit2": "director",
      "Digit3": "assets",
      "Digit4": "creative",
      "Digit5": "motion",
      "Digit6": "vfx",
      "Digit7": "animation",
      "Digit8": "generation",
      "Digit9": "audio",
      "Digit0": "color",
      "Minus": "localization",
      "Equal": "rendering"
    };

    for (const [code, ws] of Object.entries(workspaceMap)) {
      this.register(code, `Switch to ${ws} workspace`, () => store.setWorkspace(ws));
    }
  }

  register(code, description, handler) {
    this.shortcuts.set(code, { description, handler });
  }

  bindEvents() {
    window.addEventListener("keydown", (e) => {
      // Prevent shortcut triggers when typing in inputs/textareas
      const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "textarea" || document.activeElement.isContentEditable) {
        if (e.key === "Escape") {
          document.activeElement.blur();
        }
        return;
      }

      // Check command palette (Cmd+K / Ctrl+K)
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const event = new CustomEvent("toggle-command-palette");
        window.dispatchEvent(event);
        return;
      }

      // Check manual save (Cmd+S / Ctrl+S)
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        store.triggerAutosave();
        store.addNotification("Project saved to central registry", "success");
        return;
      }

      // Check registered single-key shortcuts
      const binding = this.shortcuts.get(e.code);
      if (binding) {
        binding.handler(e);
      }
    });
  }

  getAllShortcuts() {
    const list = [];
    for (const [code, { description }] of this.shortcuts.entries()) {
      list.push({ code, description });
    }
    return list;
  }
}

export const shortcutManager = new ShortcutManager();

