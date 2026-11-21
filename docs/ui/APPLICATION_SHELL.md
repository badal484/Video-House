# Application Shell Specification

## 1. Shell Components

The Global Application Shell encapsulates the entire creative experience:
1. **Top Application Bar (`<header>`):**
   - **Branding & Project Identity:** Studio logo, active project name, save indicator (`Saved`, `Unsaved Changes`, `Autosaving...`).
   - **Specialized Workspace Tabs:** 12 workspace tabs with numeric shortcut hints.
   - **Global Search Button:** Triggers `Cmd+K` command palette.
   - **Job Center Pill:** Real-time counter of active background jobs (renders, generations, QC audits).
   - **Storage Telemetry:** Displays available local workstation storage (e.g. `38GB Free`).
   - **User / Help Menu:** Access to documentation, keyboard shortcuts guide, and global settings.

2. **Left Navigation Drawer / Sidebar (`<nav>`):**
   - Quick-toggle navigation icons for rapid switching when the top bar is hidden or in compact mode.
   - Collapsible to a 48px slim rail to maximize creative canvas space.

3. **Center Main Canvas (`<main>`):**
   - Dynamic viewport rendering the currently active workspace.

4. **Bottom Status Bar (`<footer>`):**
   - Active project UUID, framerate (24.00 fps), timeline timebase, VideoToolbox hardware acceleration status, backend API health, and system clock.
