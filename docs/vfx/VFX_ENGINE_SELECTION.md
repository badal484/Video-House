# VFX ENGINE SELECTION & HYBRID ARCHITECTURE
**Department:** 13_vfx_compositing  
**Architecture:** Dual-Engine Hybrid Routing (Deterministic Local + Headless Remote)  

---

## 1. Engine Selection Strategy

To satisfy the studio's operational constraints (Apple M4 local hardware, 16GB RAM, ~41GB free disk, zero cloud lock-in, and instant testability), Department 13 adopts a **Hybrid Two-Tier Engine Architecture**:

```
                              [ CompositingGraph ]
                                       │
                                       ▼
                              [ VFXEngineRouter ]
                                       │
                  ┌────────────────────┴────────────────────┐
                  ▼                                         ▼
      [ LocalCompositorEngine ]                 [ BlenderCompositorEngine ]
      • Pure Python + OpenCV + NumPy            • Headless Blender 4.x (.py)
      • Sub-millisecond node evaluation         • 3D Scene / USD / Cycles Passes
      • 2D Tracking, Keying, Inpaint            • Multi-pass OpenEXR & Cryptomatte
      • Instant local M4 execution              • Remote GPU or local subprocess
```

---

## 2. Engine Responsibilities

### Tier 1: `LocalCompositorEngine` (Primary Local Workhorse)
- **Execution Mechanism:** Executes node graphs in Python using vectorized NumPy array operations and OpenCV 5.0.
- **Node Capabilities:**
  - `MediaInputNode`: Loads video frames, PNG-with-alpha, ProRes 4444, or generated image assets.
  - `ChromaKeyNode`: Advanced green/blue screen extraction with color difference despill, matte erode/dilate, and edge feathering.
  - `PlanarWarpNode`: 4-point homography perspective warping for screen/billboard replacements.
  - `FeatureTrackNode`: Shi-Tomasi + Lucas-Kanade optical flow point tracking.
  - `InpaintNode`: Navier-Stokes & Telea fast marching wire/object removal.
  - `TransformNode`: Scale, rotate, translate, anchor offset, and aspect fit.
  - `ColorGradeNode`: Exposure, contrast, saturation, lift/gamma/gain, and color tinting.
  - `BlurNode` / `GlowNode`: Gaussian filtering, light wrap, bloom, and atmospheric diffusion.
  - `MergeNode`: Over, Add, Multiply, Screen, Difference, and Mask blend modes with premultiplied alpha math.
  - `MediaOutputNode`: Writes master RGBA frames or pipes directly to FFmpeg.

### Tier 2: `BlenderCompositorEngine` (3D & Deep Multi-Pass)
- **Execution Mechanism:** Generates standalone Blender Python scripts (`vfx_composite_script.py`) containing Blender Compositor node trees.
- **Node Capabilities:**
  - Multi-pass OpenEXR AOVs (Diffuse, Specular, Transmission, Shadow, Cryptomatte, Z-Depth).
  - OpenColorIO ACEScg pipeline conversions.
  - 3D camera reconstruction and spatial object placement.
  - Dispatches as a headless background subprocess when Blender is installed, or packages as a portable ZIP/container job for remote GPU clusters.

---

## 3. Dynamic Engine Router Rules

The `VFXEngineRouter` inspects the node types in any incoming `CompositingGraph`:
1. If all nodes belong to the 2D standard library (`INPUT`, `KEYER`, `MERGE`, `TRANSFORM`, `WARP`, `INPAINT`, `BLUR`, `COLOR`, `OUTPUT`), route directly to `LocalCompositorEngine`.
2. If any node requires 3D camera projections, OpenUSD scene integration, or multi-layer EXR Cryptomattes, generate a Blender script package and dispatch to `BlenderCompositorEngine`.
3. If an AI video model pass (SAM 2.1 video tracking or ProPainter inpainting) is specified, the router generates an AI task manifest for Department 15/20 remote dispatch with a local fallback using OpenCV GrabCut/Telea.
