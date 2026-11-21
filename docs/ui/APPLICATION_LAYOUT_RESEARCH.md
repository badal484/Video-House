# Application Layout Research & Window Management

## 1. Principles of Creative Application Window Management

Creative professionals spend 8–14 hours per day in production software. Interface fatigue, visual distraction, and panel hunting severely reduce productivity. The layout architecture must prioritize:
- **Zero Distraction:** Neutral deep grays (`#121316`, `#18191D`, `#22242A`) that allow video colors, skin tones, and graphics to be judged accurately without optical bias.
- **Predictable Muscle Memory:** Panels maintain predictable functional roles regardless of the active workspace.
- **Immediate Spatial Awareness:** The user always knows:
  1. What project they are working on.
  2. Which workspace is currently active.
  3. Where the media assets are located.
  4. What frame the playhead is parked on.
  5. What jobs are rendering in the background.

---

## 2. The 4-Quadrant Production Layout

```
+----------------------------------------------------------------------------------------------------+
| TOP APPLICATION BAR: Project Title | Workspace Switcher | Cmd+K Search | Job Center | Settings     |
+----------------------------------------------------+-----------------------------------------------+
| LEFT PANEL (Asset Browser / Library / Presets)     | CENTER VIEWPORT (Monitor / Canvas / Preview)  |
| - Project Assets (Videos, Audios, Stems, Images)   | - HTML5 / WebGL / Canvas Viewport             |
| - Scene & Shot Bins                                | - Playhead Timecode (00:01:24:12)             |
| - VFX / Audio / Preset Drawers                     | - Transport Controls (J-K-L, Play, Loop)      |
|                                                    | - Resolution & Aspect Ratio Selectors         |
+----------------------------------------------------+-----------------------------------------------+
| BOTTOM PANEL (Multi-Track Timeline / Node Graph)   | RIGHT PANEL (Inspector / Properties / AI)     |
| - Video Tracks (V1, V2, V3)                        | - Clip Transform & Speed Controls             |
| - Audio Tracks (A1 Dialogue, A2 Music, A3 SFX)     | - AI Director Chat & Proposal Inspector       |
| - Subtitle & Marker Lanes                          | - Color Grading Wheels / Sliders              |
| - Zoom Slider & Time Ruler                         | - Audio Parametric EQ & Loudness Meter        |
+----------------------------------------------------+-----------------------------------------------+
| STATUS BAR: Active Project | Engine Status | VideoToolbox Ready | Storage: 38GB Free | Version v1.0 |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Resizable Panels & Splitter Architecture

To accommodate varying display aspect ratios (16:9, 16:10 MacBook Pro Retina, 21:9 UltraWide, and dual-monitor setups), the studio layout utilizes a CSS Grid and Flexbox splitter architecture:
1. **Horizontal Splitter (Left to Center):** Allows expanding the Asset Browser when organizing hundreds of media files, or collapsing it to a 48px icon strip during color grading or editing.
2. **Vertical Splitter (Center to Bottom):** Allows maximizing the Timeline to display 16+ audio/video tracks during complex editorial assembly, or collapsing it when previewing 4K playback.
3. **Right Inspector Splitter:** Adjusts property panel width for detailed parametric audio EQ graphs or 3-way color wheel adjustments.

---

## 4. Workspace Presets

The application supports 12 standardized workspace presets accessible via numeric shortcuts (`1` through `9`, `0`, `-`, `=`):
- `1`: **Home & Projects Dashboard** (Project management, recent jobs, storage overview)
- `2`: **AI Director & Scripting** (Brief intake, concept cards, script formatting, storyboards)
- `3`: **Media Ingestion & Assets** (Detailed metadata, contact sheets, waveform peaks)
- `4`: **Creative Assembly & NLE** (Standard 4-quadrant timeline editing)
- `5`: **Motion Graphics** (Typography, SVG composition canvas, keyframes)
- `6`: **VFX & Compositing** (Node DAG graph, chroma keyer, planar tracking)
- `7`: **2D Animation & Characters** (Turnaround sheets, bones, exposure sheets)
- `8`: **AI Generation Studio** (Multimodal prompt compiler, provider controls, cost firewall)
- `9`: **Audio Post-Production** (Multitrack DAW mixer, EQ, EBU R128 loudness)
- `0`: **Color Grading & Restoration** (Lift/Gamma/Gain wheels, curves, LUTs)
- `-`: **Subtitles & Localization** (Transcript editor, translation, dubbing, lip-sync)
- `=`: **Rendering, QC & Delivery** (Render plan DAG, QC report cards, delivery manifests)

