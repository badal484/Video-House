/**
 * Global Command Palette (Cmd+K) Modal Component.
 * Enables instant fuzzy search across workspaces, assets, projects, and actions.
 */

import { store } from "../state.js";

export class CommandPaletteComponent {
  constructor() {
    this.isOpen = false;
    this.selectedIndex = 0;
    this.filteredItems = [];
    this.initDOM();
    this.bindEvents();
  }

  initDOM() {
    this.el = document.createElement("div");
    this.el.className = "modal-backdrop command-palette-modal";
    this.el.style.display = "none";
    this.el.innerHTML = `
      <div class="command-palette" role="dialog" aria-modal="true" aria-label="Command Palette">
        <div class="command-input-wrapper">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--studio-text-muted);">
            <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" class="command-input" placeholder="Type a command or search (e.g. 'Color', 'Render', 'Import')..." />
          <kbd style="font-size: 10px; padding: 2px 5px; border-radius: 3px; background: var(--studio-bg-hover); color: var(--studio-text-muted);">ESC</kbd>
        </div>
        <div class="command-results" role="listbox"></div>
      </div>
    `;
    document.body.appendChild(this.el);

    this.input = this.el.querySelector(".command-input");
    this.resultsContainer = this.el.querySelector(".command-results");
  }

  bindEvents() {
    window.addEventListener("toggle-command-palette", () => this.toggle());

    this.el.addEventListener("click", (e) => {
      if (e.target === this.el) this.close();
    });

    this.input.addEventListener("input", () => this.handleFilter());

    this.input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredItems.length - 1);
        this.renderResults();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
        this.renderResults();
      } else if (e.key === "Enter") {
        e.preventDefault();
        this.executeSelected();
      } else if (e.key === "Escape") {
        this.close();
      }
    });
  }

  getAvailableCommands() {
    return [
      { id: "ws-home", label: "Go to: Home & Projects Dashboard", category: "Workspace", action: () => store.setWorkspace("home") },
      { id: "ws-creative", label: "Go to: Creative NLE Workspace", category: "Workspace", action: () => store.setWorkspace("creative") },
      { id: "ws-director", label: "Go to: AI Director & Scripting", category: "Workspace", action: () => store.setWorkspace("director") },
      { id: "ws-agents", label: "Go to: Agent Control Center", category: "Workspace", action: () => store.setWorkspace("agents") },
      { id: "ws-generation", label: "Go to: AI Generation Studio", category: "Workspace", action: () => store.setWorkspace("generation") },
      { id: "ws-motion", label: "Go to: Motion Graphics Studio", category: "Workspace", action: () => store.setWorkspace("motion") },
      { id: "ws-vfx", label: "Go to: VFX & Compositing", category: "Workspace", action: () => store.setWorkspace("vfx") },
      { id: "ws-animation", label: "Go to: 2D Animation & Characters", category: "Workspace", action: () => store.setWorkspace("animation") },
      { id: "ws-audio", label: "Go to: Audio Post-Production DAW", category: "Workspace", action: () => store.setWorkspace("audio") },
      { id: "ws-color", label: "Go to: Color Grading & Restoration", category: "Workspace", action: () => store.setWorkspace("color") },
      { id: "ws-localization", label: "Go to: Subtitles & Localization", category: "Workspace", action: () => store.setWorkspace("localization") },
      { id: "ws-rendering", label: "Go to: Rendering, QC & Delivery", category: "Workspace", action: () => store.setWorkspace("rendering") },
      { id: "act-save", label: "Action: Save Project Now (Cmd+S)", category: "Project", action: () => store.triggerAutosave() },
      { id: "act-import", label: "Action: Import Media File", category: "Media", action: () => store.setWorkspace("assets") },
      { id: "act-render", label: "Action: Compile Render Plan", category: "Rendering", action: () => store.setWorkspace("rendering") }
    ];
  }

  handleFilter() {
    const q = this.input.value.toLowerCase().trim();
    const commands = this.getAvailableCommands();
    if (!q) {
      this.filteredItems = commands;
    } else {
      this.filteredItems = commands.filter(c =>
        c.label.toLowerCase().includes(q) || c.category.toLowerCase().includes(q)
      );
    }
    this.selectedIndex = 0;
    this.renderResults();
  }

  renderResults() {
    if (this.filteredItems.length === 0) {
      this.resultsContainer.innerHTML = `<div style="padding: 12px; color: var(--studio-text-muted); text-align: center;">No matching commands found</div>`;
      return;
    }

    this.resultsContainer.innerHTML = this.filteredItems.map((item, idx) => `
      <div class="command-item ${idx === this.selectedIndex ? "selected" : ""}" data-idx="${idx}" role="option" aria-selected="${idx === this.selectedIndex}">
        <span>${item.label}</span>
        <span class="badge" style="font-size: 9px;">${item.category}</span>
      </div>
    `).join("");

    const items = this.resultsContainer.querySelectorAll(".command-item");
    items.forEach(el => {
      el.addEventListener("click", () => {
        this.selectedIndex = parseInt(el.getAttribute("data-idx"), 10);
        this.executeSelected();
      });
    });
  }

  executeSelected() {
    const item = this.filteredItems[this.selectedIndex];
    if (item && item.action) {
      item.action();
      this.close();
    }
  }

  toggle() {
    if (this.isOpen) this.close();
    else this.open();
  }

  open() {
    this.isOpen = true;
    this.el.style.display = "flex";
    this.input.value = "";
    this.handleFilter();
    setTimeout(() => this.input.focus(), 50);
  }

  close() {
    this.isOpen = false;
    this.el.style.display = "none";
  }
}

