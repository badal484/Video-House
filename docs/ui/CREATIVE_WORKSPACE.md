# Creative Workspace Specification: The Unified 4-Quadrant Canvas

## 1. Quadrant Roles & Interaction Model

The **Creative Workspace** is the core operational cockpit of the studio, implementing the classic 4-quadrant NLE layout:

### Quadrant 1 (Top Left): Asset Browser & Production Library
- Displays project assets, uploaded footage, AI generated clips, audio stems, and graphics.
- Features dual view modes: Compact List View and Visual Grid View (with 16:9 thumbnail previews).
- Search input with instantaneous client-side filtering and backend semantic search trigger.
- Role filtering chips (`SOURCE_FOOTAGE`, `GENERATED`, `MUSIC`, `VOICEOVER`, `VFX_PLATE`, `LUT`).
- Drag-and-drop support: dragging an asset directly onto a timeline track creates a clip at the drop timecode.

### Quadrant 2 (Top Center): Program Preview Monitor & Viewport
- HTML5 / Canvas playback viewport displaying the active composition or selected asset.
- Overlay controls:
  - Exact rational timecode display (`HH:MM:SS:FF`).
  - Transport buttons: Step Backward (1 frame), Play/Pause (Space), Step Forward (1 frame), Loop Toggle.
  - Zoom controls (Fit, 50%, 100%, 200%).
  - Safe Area guides toggle (Action Safe 90%, Title Safe 80%).
  - Before/After split comparison slider for color grades and VFX composites.

### Quadrant 3 (Top Right): Context-Sensitive Properties Inspector
- Adapts dynamically based on what is selected:
  - **Clip Selected:** Start timecode, duration, video scale/position, opacity, audio gain, applied transitions.
  - **Track Selected:** Track name, mute/solo, lock state, volume fader, routing.
  - **Asset Selected:** Codec, dimensions, bitrate, framerate, color space, SHA-256 checksum.
  - **AI Director Tab:** In-context chat drawer with director proposals, blueprint actions, and approval buttons.

### Quadrant 4 (Bottom): Multi-Track Non-Linear Editorial Timeline
- Tracks organized vertically: Video Tracks (`V3`, `V2`, `V1`) on top, Audio Tracks (`A1 Dialogue`, `A2 Music`, `A3 SFX`) below.
- Time ruler with frame ticks and snap indicators.
- Draggable cyan playhead needle synchronized with Program Monitor.
- Clip manipulation: Click to select, drag to reposition, `B` to blade/split at playhead, `Delete` / `Backspace` to delete, handles to trim in/out points.

