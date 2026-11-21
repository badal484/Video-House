# Product UX Implementation: Architecture & Integration Blueprint

## 1. System Integration Overview

The Universal AI Video Production Studio User Interface (`departments/01_studio_application/ui/`) is the single glass pane uniting all 14 previously implemented production departments:
- **Part 02 (Media Ingestion):** Asset uploads, local file import, technical metadata extraction, 720p H.264 web proxies, 500-point waveform visualization.
- **Part 03 (Media Intelligence):** Semantic multi-modal search, PySceneDetect shot cuts, faster-whisper transcripts, optical flow camera classification, OCR text recognition, and style comparison.
- **Part 04 (AI Director):** Natural-language creative briefs, 3-tier concept selection, script breakdown, storyboard generation, and editing blueprints.
- **Part 05 (Video Editing):** Multi-track OpenTimelineIO non-linear editing, clip trimming, splitting, ripple delete, crossfades, and render previews.
- **Part 06 (Motion Graphics):** Motion Canvas / SVG declarative presets, typography styling, lower-thirds, and timeline track insertion.
- **Part 07 (VFX Compositing):** Node-based compositing DAGs, chroma keying, planar tracking, inpainting, and matte auditing.
- **Part 08 (2D Animation):** Settei character turnarounds, 2D bone rigging, IK solvers, exposure sheets (X-sheets), and anime cel shading.
- **Part 09 (3D Animation):** OpenUSD / Blender asset inspection and scene preview.
- **Part 10 (Audio Post-Production):** Spotify Pedalboard DSP multitrack mixing, 5-band parametric EQ, ITU-R BS.1770-4 / EBU R128 loudness normalization, and procedural SFX synthesis.
- **Part 11 (AI Generation):** Multi-provider router (Runway, Kling, Wan2.1, Flux.1, ElevenLabs), multi-dimensional prompt compiler, and budget ceiling firewalls.
- **Part 12 (Color Grading & Restoration):** Scene-referred ACEScg color management, 3-way Lift/Gamma/Gain wheels, Adobe `.cube` 3D LUTs, YADIF deinterlacing, and Super-Resolution upscaling.
- **Part 13 (Subtitles & Localization):** WhisperX word timestamps, Indic language code-switching, broadcast subtitle generation (SRT, VTT, ASS, TTML), isochronic dubbing, and Sync Labs lip-sync.
- **Part 14 (Quality Control & Delivery):** Preflight project validation, render plan DAG compiler, Apple VideoToolbox hardware acceleration, multi-profile export, and automated QC defect reporting.

---

## 2. Directory & Component Architecture

```
departments/01_studio_application/ui/
├── index.html                   # Semantic HTML5 Application Shell
├── css/
│   ├── tokens.css               # Design tokens (colors, typography, spacing, shadows)
│   ├── layout.css               # 4-quadrant grid, resizable panels, splitters
│   ├── components.css           # Reusable UI controls (buttons, inputs, tabs, modals)
│   └── workspaces.css           # Specialized panel styling (timeline, wheels, node DAG)
└── js/
    ├── tokens.js                # Theme & token definitions
    ├── api_client.js            # Strongly-typed asynchronous backend REST client
    ├── state.js                 # Central reactive state store & undo/redo manager
    ├── shortcuts.js             # Global keyboard shortcut manager
    ├── components/
    │   ├── command_palette.js   # Cmd+K quick launcher & fuzzy search
    │   ├── media_preview.js     # HTML5 Video/Audio/Canvas preview engine
    │   ├── asset_browser.js     # Media grid/list with filter & upload
    │   └── notifications.js     # Toast system & background job center
    ├── workspaces/
    │   ├── home_dashboard.js    # Project cards, active jobs, storage telemetry
    │   ├── creative_workspace.js# Primary 4-quadrant NLE workspace
    │   ├── editing_workspace.js # Multi-track timeline & clip operations
    │   ├── ai_director_workspace.js # Brief, concept, script, storyboard
    │   ├── agent_center_workspace.js# 12 departmental agents & execution logs
    │   ├── generation_workspace.js # Text/Image-to-video prompt studio
    │   ├── motion_graphics_workspace.js # SVG typography & animated lower-thirds
    │   ├── vfx_workspace.js     # Visual node graph & chroma keying
    │   ├── animation_workspace.js # 2D characters, turnarounds & X-sheets
    │   ├── audio_workspace.js   # DAW mixer, faders, EBU R128 meters, SFX
    │   ├── color_workspace.js   # 3-way color wheels, curves & LUTs
    │   ├── localization_workspace.js # Subtitles, transcripts & dubbing
    │   ├── rendering_workspace.js # Render plans, profile presets & QC reports
    │   └── project_settings.js  # Resolution, framerate & storage configuration
    └── app.js                   # Main application entry point & router
```

