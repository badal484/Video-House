# Render Engine Architecture Specification

## 1. Modular Architecture Overview
The Rendering Engine separates procedural creative evaluation from distribution encoding. It interfaces with host hardware through abstract worker adapters.

```
                  ┌──────────────────────────────┐
                  │    Render Plan Execution     │
                  └──────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [Timeline Render Adapter]      [DCC Render Bridges]
       (OpenTimelineIO Compositing)    (VFX, Motion Canvas, Blender)
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                     [Intermediate Master Buffer]
                     (ProRes 422 HQ / Uncompressed)
                                 │
                                 ▼
                    [Encoding Engine Adapter]
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
[Apple VideoToolbox Hardware]                [Software Reference CPU]
(h264_videotoolbox, hevc_videotoolbox)       (libx264, libx265, libsvtav1)
           │                                           │
           └─────────────────────┬─────────────────────┘
                                 ▼
                      [Target Encoded Master]
```

## 2. Timeline Render Adapter (`TimelineRenderAdapter`)
The timeline adapter interfaces with Department 05:
- Ingests the OpenTimelineIO `Timeline`.
- Samples timecodes at rational frame boundaries (`RationalTime(frame, fps)`).
- Resolves video clip overlaps, cross-dissolves, wipe transitions, and color grade transforms.
- Streams uncompressed frame buffers (RGB24 / YUV422p10le) to the encoding pipeline.

## 3. Encoding Engine Adapter (`EncodingEngineAdapter`)
The encoding engine configures FFmpeg parameters matching the active `RenderProfile`:
- **Rate Control:** Two-pass VBR, single-pass CRF (Constant Rate Factor), or CBR for broadcast.
- **GOP Architecture:** Closed GOPs with keyframe intervals fixed to exactly 2 seconds for web streaming (`-g 48` at 24fps).
- **FastStart Atom:** Relocates the ISO `moov` atom to the beginning of the MP4 container (`-movflags +faststart`) enabling instant progressive web playback.
- **Color Tagging:** Writes explicit NCLX color metadata: color primaries, transfer characteristics, and matrix coefficients (e.g. `bt709` or `bt2020-10 / smpte2084`).

