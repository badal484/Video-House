# Specialized Workspaces Specification

This document details the interface architecture for each of the 9 specialized department workspaces.

---

## 1. Editing Workspace (Part 05)
- **Features:** Full-width multi-track OpenTimelineIO timeline view, ripple editing tools, transition palette (Cross Dissolve, Dip to Black, Wipe), split clip, slip/slide, keyframe curves, and OTIO export button.
- **Backend Bridge:** `/api/v1/editing/timelines/{id}/*`

## 2. Motion Graphics Workspace (Part 06)
- **Features:** Declarative typography preset drawer (Kinetic Typography, Cinematic Titles, Lower Thirds, HUD Overlays), live SVG rendering canvas, property sliders (font family, font size, tracking, fill color, animation duration), and "Insert to Timeline" button.
- **Backend Bridge:** `/api/v1/motion-graphics/*`

## 3. VFX & Compositing Workspace (Part 07)
- **Features:** Visual node DAG canvas showing image inputs, chroma keyer, planar tracker, blur, inpainting, and merge Over nodes. Node parameter inspector and live composite output viewer.
- **Backend Bridge:** `/api/v1/vfx/*`

## 4. 2D Animation & Character Workspace (Part 08)
- **Features:** Character concept selector, 5-angle Settei turnaround model sheet viewer, 2D bone hierarchy tree, 8-frame walk cycle preview, exposure sheet (X-sheet) timing, and background parallax layers.
- **Backend Bridge:** `/api/v1/animation/*`

## 5. 3D Animation & Scene Workspace (Part 09)
- **Features:** OpenUSD scene browser, camera selector, lighting presets, Blender integration status monitor, and test render preview.

## 6. Audio Post-Production Workspace (Part 10)
- **Features:** Multitrack DAW mixer fader console, 5-band parametric biquad EQ curves, real-time ITU-R BS.1770-4 / EBU R128 integrated LUFS loudness bar (-23 LUFS / -14 LUFS target lines), true peak meter, dialogue de-noiser, sidechain ducking toggles, and procedural sound design synthesizer.
- **Backend Bridge:** `/api/v1/audio/*`

## 7. Color Grading & Restoration Workspace (Part 12)
- **Features:** 3-way Lift/Gamma/Gain color wheels, master luminance sliders, RGB curves graph, 3D LUT selector (`.cube`), ACEScg input transform dropdown, YADIF deinterlacer, and Super-Resolution 2x/4x upscaling controls.
- **Backend Bridge:** `/api/v1/color/*` and `/api/v1/restoration/*`

## 8. Subtitles & Localization Workspace (Part 13)
- **Features:** Word-level timed transcript editor with manual edit audit tracking, multi-language translation selector (Spanish, French, German, Japanese, Hindi, Tamil), subtitle cue table (CPL and CPS indicators), voice talent casting cards with biometric consent status, and Sync Labs lip-sync dispatcher.
- **Backend Bridge:** `/api/v1/localization/*`

## 9. Rendering, QC & Delivery Workspace (Part 14)
- **Features:** Preflight checklist (offline media, missing fonts, licenses), render plan DAG viewer, profile presets (ProRes 422 HQ, YouTube 1080p, Shorts 9:16, Broadcast MXF, FFV1), real-time priority queue monitor, delivery package manifest viewer, and automated QC defect report cards.
- **Backend Bridge:** `/api/v1/rendering/*` and `/api/v1/qc/*`

