/**
 * AI Director & Creative Planning Workspace.
 * Direct interface to Department 06 (Creative Direction) & Department 07 (Production Planning).
 */

import { store } from "../state.js";
import { api } from "../api_client.js";

export class AIDirectorWorkspace {
  constructor(container) {
    this.container = container;
  }

  async mount() {
    this.container.innerHTML = `
      <div style="display: flex; flex-direction: column; height: 100%; width: 100%; padding: var(--space-4); gap: var(--space-4); overflow-y: auto;">
        <!-- Header -->
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--studio-border-subtle); padding-bottom: var(--space-2);">
          <div>
            <h2 style="font-size: var(--font-size-xl); font-weight: 700; color: var(--studio-text-primary);">AI Director & Production Planning</h2>
            <p style="font-size: var(--font-size-xs); color: var(--studio-text-muted);">Transform natural language prompts and reference footage into structured screenplay and storyboards.</p>
          </div>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-primary btn-sm" id="btn-generate-concepts">Generate Concepts</button>
            <button class="btn btn-secondary btn-sm" id="btn-create-script">Breakdown Script</button>
            <button class="btn btn-secondary btn-sm" id="btn-plan-shots">Plan Shots & Storyboard</button>
          </div>
        </div>

        <!-- Creative Brief Input Drawer -->
        <div style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2);">
          <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--studio-text-secondary);">Creative Vision & Directive</div>
          <textarea class="textarea" id="director-prompt-input" placeholder="Describe the video narrative, tone, visual style, character dynamics, and intended platform...">Cinematic tech commercial for a quantum workstation: Opening with low-angle macro shot of glowing photon processor, building tension with rhythmic electronic score, transitioning to high-speed visual graphics and ending with a dramatic brand reveal.</textarea>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 11px; color: var(--studio-text-muted);">Platform: YouTube / 4K Cinema • Visual Style: Cinematic Realism</div>
            <button class="btn btn-primary btn-xs" id="btn-save-brief">Save Brief</button>
          </div>
        </div>

        <!-- Concept Selection Carousel -->
        <div>
          <h3 style="font-size: var(--font-size-md); font-weight: 600; color: var(--studio-text-secondary); margin-bottom: var(--space-2);">Ideation Concepts</h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--space-3);" id="director-concepts-list">
            <div class="card" style="background-color: var(--studio-bg-panel); border: 2px solid var(--studio-accent-primary); border-radius: var(--radius-md); padding: var(--space-3);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-weight: 700; color: var(--studio-accent-primary);">Concept A: Quantum Ignition</span>
                <span class="badge badge-success">SELECTED</span>
              </div>
              <p style="font-size: 12px; color: var(--studio-text-secondary);">High-contrast cinematic realism focusing on microscopic optical circuitry and dramatic anamorphic lens flares.</p>
            </div>
            <div class="card" style="background-color: var(--studio-bg-panel); border: 1px solid var(--studio-border-default); border-radius: var(--radius-md); padding: var(--space-3);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-weight: 700;">Concept B: Human Potential</span>
                <button class="btn btn-secondary btn-xs">Select</button>
              </div>
              <p style="font-size: 12px; color: var(--studio-text-secondary);">Character-driven emotional journey of an engineer unlocking breakthrough scientific discoveries.</p>
            </div>
          </div>
        </div>

        <!-- Visual Storyboard Deck -->
        <div>
          <h3 style="font-size: var(--font-size-md); font-weight: 600; color: var(--studio-text-secondary); margin-bottom: var(--space-2);">Visual Storyboard & Shot Deck</h3>
          <div class="storyboard-grid" id="storyboard-deck">
            <div class="storyboard-card">
              <div class="storyboard-thumb" style="display: flex; align-items: center; justify-content: center; font-size: 24px;">🔬</div>
              <div class="storyboard-meta">
                <div style="font-weight: 600; color: var(--studio-text-primary);">Shot 01: Macro Optical Lens</div>
                <div style="color: var(--studio-text-muted);">Angle: ECU • Motion: Slow Push-In</div>
                <div style="font-size: 10px; color: var(--studio-text-secondary);">Glowing photon processor with anamorphic rim lighting.</div>
              </div>
            </div>
            <div class="storyboard-card">
              <div class="storyboard-thumb" style="display: flex; align-items: center; justify-content: center; font-size: 24px;">⚡</div>
              <div class="storyboard-meta">
                <div style="font-weight: 600; color: var(--studio-text-primary);">Shot 02: Particle Accelerator</div>
                <div style="color: var(--studio-text-muted);">Angle: Low Angle • Motion: Orbit</div>
                <div style="font-size: 10px; color: var(--studio-text-secondary);">High-speed energy streams pulsing across cleanroom chamber.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  bindEvents() {
    this.container.querySelector("#btn-save-brief").addEventListener("click", () => {
      store.addNotification("Saved creative brief to project memory", "success");
    });
    this.container.querySelector("#btn-generate-concepts").addEventListener("click", () => {
      store.addNotification("AI Director drafted 3 production concepts", "info");
    });
    this.container.querySelector("#btn-create-script").addEventListener("click", () => {
      store.addNotification("Generated 3-act screenplay breakdown", "info");
    });
    this.container.querySelector("#btn-plan-shots").addEventListener("click", () => {
      store.addNotification("Compiled visual storyboard cards", "success");
    });
  }
}
