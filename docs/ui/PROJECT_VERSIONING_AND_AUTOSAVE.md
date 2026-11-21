# Project Versioning & Autosave Specification

## 1. Zero-Loss Persistence Architecture

Professional creative workflows require bulletproof state preservation to safeguard hours of complex editing, audio mixing, and color grading.

### 1. Continuous Non-Blocking Autosave
- **Trigger Cadence:** State changes (clip moves, split cuts, color slider adjustments) trigger an autosave queue debounced at 3,000ms.
- **Visual Status Pill:** The top application bar displays real-time state:
  - `Saved` (Subtle green checkmark).
  - `Unsaved Changes` (Amber dot).
  - `Autosaving...` (Pulsing cyan indicator).
- **Crash Recovery:** Project state is synchronized to the central SQLite database (`projects/studio_asset_registry.db`). In the event of a sudden browser tab crash or machine restart, reopening the project restores the exact playhead position, timeline tracks, and open panel layout.

### 2. Version Snapshots & Rollback
- Creators can capture explicit named version milestones (e.g. `Rough Cut v1`, `Client Review Cut v2`, `Color Locked Master`).
- Version browser modal lists past versions with creation timestamp, author notes, and snapshot metadata.
- "Restore Version" creates an automatic safety snapshot of current work before executing a non-destructive rollback.
- Unsaved change guard: Attempting to close or switch projects with pending edits triggers an explicit confirmation dialog.
