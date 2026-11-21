# VFX & COMPOSITING STUDIO ARCHITECTURE SPECIFICATION
**Department:** 13_vfx_compositing  
**Document Version:** 1.0.0  
**Status:** Approved Technical Architecture  

---

## 1. System Overview

Department 13 (`13_vfx_compositing`) provides the studio with a production-grade visual effects and compositing pipeline. It bridges creative direction (Department 06), editorial assembly (Department 08), motion graphics (Department 09), 3D animation (Department 11), and quality control (Department 18).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DEPARTMENT 13: VFX & COMPOSITING                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────┐         ┌─────────────────────────────────────┐  │
│  │   AI VFX Supervisor   │ ◄─────► │     Compositing Graph Engine        │  │
│  │ • Analyzes plate      │         │ • Directed Acyclic Graph (DAG)      │  │
│  │ • Designs node plans  │         │ • Topological node evaluation       │  │
│  │ • Proposes parameters │         │ • Straight vs Premultiplied Alpha   │  │
│  └──────────┬────────────┘         └──────────────────┬──────────────────┘  │
│             │                                         │                     │
│  ┌──────────▼────────────┐         ┌──────────────────▼──────────────────┐  │
│  │  CV & Tracking Suite  │         │      VFX Execution Engines          │  │
│  │ • Lucas-Kanade points │         │ • LocalCompositorEngine (NumPy/CV2) │  │
│  │ • 4-Point Homography  │         │ • BlenderCompositorEngine (3D/EXR)  │  │
│  │ • Chroma Key & Despill│         │ • VFXEngineRouter (auto-dispatch)   │  │
│  │ • Inpainting (Telea)  │         │                                     │  │
│  └───────────────────────┘         └──────────────────┬──────────────────┘  │
│                                                       │                     │
│  ┌───────────────────────┐         ┌──────────────────▼──────────────────┐  │
│  │   VFX Quality Checker │ ◄─────► │     Studio Pipeline Bridges         │  │
│  │ • Matte hole analysis │         │ • TimelineBridge (NLE V1/V2 embed)  │  │
│  │ • Edge halo detector  │         │ • DirectorBridge (Blueprint reader) │  │
│  │ • Spill leakage check │         │ • AssetRegistry (SQLite persistence)│  │
│  └───────────────────────┘         └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 The Compositing Node Graph (`departments/13_vfx_compositing/core/`)
- A rigorous, JSON-serializable Directed Acyclic Graph (DAG).
- Nodes possess typed input and output ports (`IMAGE_RGBA`, `IMAGE_RGB`, `MASK_ALPHA`, `TRANSFORM_MATRIX`, `TRACK_DATA`).
- Cycle detection guarantees topological sort execution without infinite recursion.

### 2.2 Computer Vision, Tracking & Keying (`departments/13_vfx_compositing/`)
- **Keying (`keying/`):** Chroma distance thresholding, despill color suppression (`green_despill` / `blue_despill`), morphological alpha cleanup.
- **Tracking (`tracking/`):** 4-point planar corner pinning for replacement, point feature tracking for callout/graphic attachment, 3D camera matrix estimation.
- **Rotoscoping (`rotoscoping/`):** Interactive bounding box segmentation, GrabCut energy minimization, edge feathering, and temporal mask smoothing.
- **Cleanup (`cleanup/`):** Video inpainting and rig/wire/logo removal using Telea fast marching and Navier-Stokes equations.
- **Effects (`effects/`):** Cinematic light wraps, atmospheric dust/particles, lens glow, camera shake, and chromatic aberration.

### 2.3 The AI VFX Supervisor (`supervisor/`)
- Translates unstructured creative briefs (e.g. *"Replace the smartphone screen with the product dashboard and remove the microphone boom"*) into an executable `CompositingGraph`.
- Inspects plate characteristics (resolution, color distribution, motion blur level) to configure node parameters.

### 2.4 VFX Quality Control Checker (`supervisor/quality_checker.py`)
- Automatically audits rendered composites for common artifacts:
  - Alpha matte pinholes or background bleed.
  - Green/blue color spill on subject edges.
  - High-frequency tracking jitter.
  - Luminance clipping in light wraps.

### 2.5 Pipeline Integration Bridges (`integration/`)
- **TimelineBridge:** Exports rendered VFX shot sequences and seamlessly integrates them back into the Department 08 OpenTimelineIO NLE timeline as replacement clips on track `V1` or composited overlays on track `V2`.
- **DirectorBridge:** Ingests Department 04 `PlannedShot` records, identifies `vfx_notes` or `required_vfx`, and schedules corresponding `VFXShotTask` items in the database.
