# Media Preview Architecture: HTML5 Video, Audio & Canvas Engine

## 1. Multi-Format Viewport Pipeline

The **Media Preview Engine** provides sub-frame accurate playback and comparison across original footage, generated clips, color grades, and timeline compositions:

### 1. Unified Player Surface
- Employs an HTML5 `<video>` element with hardware decoding enabled, overlaid with an HTML5 `<canvas>` rendering surface.
- Native Apple Silicon M4 hardware decoding supports H.264, HEVC, ProRes, and WebM seamlessly with zero dropped frames at 1080p and 4K.
- Synchronized Web Audio API context for stereo waveform metering and audio playback.

### 2. Timecode & Frame Stepping Math
- Video current time is tied directly to rational timeline frames:
  $$\text{Current Frame} = \lfloor \text{currentTime} \times \text{FPS} \rfloor$$
- Frame stepping calculates:
  $$\text{Next Time} = \frac{\text{Current Frame} \pm 1}{\text{FPS}}$$
- Prevents floating-point drift over multi-hour timelines.

### 3. Split Comparison (Before / After A-B Slider)
- The preview monitor includes an interactive split slider dividing the canvas into Left (Original Camera Master) and Right (Color Graded / VFX Composite / Restored Output).
- Dragging the divider allows instant visual verification of skin tones, chroma key despill, and super-resolution sharpness.
