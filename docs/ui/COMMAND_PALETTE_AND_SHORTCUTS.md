# Command Palette & Keyboard Shortcuts Specification

## 1. Unified Command Palette (`Cmd+K` / `Ctrl+K`)

The studio implements a high-speed modal command palette accessible anywhere in the application via `Cmd+K` (macOS) or `Ctrl+K` (Linux/Windows):
- **Instant Fuzzy Search:** Searches across:
  - Workspaces (e.g. `Switch to Color Workspace`, `Open Audio Mixer`).
  - Actions (e.g. `Import Media`, `Split Clip at Playhead`, `Compile Render Plan`).
  - Projects (e.g. `Open Project: Cyberpunk Short`).
  - Assets (e.g. `Find: dialogue_take_03.wav`).
  - Department Agents (e.g. `Assign AI Director Task`).
- **Keyboard Navigation:** `Up` / `Down` arrows select items; `Enter` executes the command; `Escape` closes the palette.

---

## 2. Standard Creative NLE Keyboard Shortcuts

| Shortcut | Action | Scope |
| :--- | :--- | :--- |
| `Space` | Play / Pause Playhead | Global Viewport |
| `J` | Reverse Playback (1x, 2x, 4x) | Timeline & Monitor |
| `K` | Stop / Pause Playback | Timeline & Monitor |
| `L` | Forward Playback (1x, 2x, 4x) | Timeline & Monitor |
| `Left Arrow` | Step Backward 1 Frame | Timeline & Monitor |
| `Right Arrow` | Step Forward 1 Frame | Timeline & Monitor |
| `Shift + Left` | Step Backward 10 Frames | Timeline & Monitor |
| `Shift + Right` | Step Forward 10 Frames | Timeline & Monitor |
| `B` | Blade / Split Selected Clip at Playhead | Editing Workspace |
| `Delete` / `Backspace` | Ripple Delete Selected Clip | Editing Workspace |
| `Cmd + S` | Force Manual Save | Global |
| `Cmd + Z` | Undo Last Edit Operation | Global |
| `Cmd + Shift + Z` | Redo Last Edit Operation | Global |
| `Cmd + K` | Open Command Palette | Global |
| `1` through `9`, `0`, `-`, `=` | Switch to Workspace Presets 1–12 | Global |
| `Escape` | Dismiss Open Modals & Drawers | Global |
