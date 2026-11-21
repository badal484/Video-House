# 2D ANIMATION ENGINE SELECTION & MULTI-TIER ARCHITECTURE
**Department:** 10_animation_2d & 12_character_production  
**Architecture:** Application-Owned Multi-Tier Animation Architecture  

---

## 1. Design Strategy: The Application-Owned Animation Model

No single animation tool satisfies all production styles:
- Traditional hand-drawn anime requires exposure sheets, timing charts, and palette-linked vector/raster levels (OpenToonz).
- Digital cut-out puppetry and skeletal animation require bone hierarchies, pivot transformations, and analytical IK solvers.
- Stylized anime expressions require multi-parameter deformers and facial viseme mouth replacement.
- Procedural explainer sequences benefit from declarative vector SVG timelines (Motion Canvas).
- 2D/3D hybrid scenes require true multiplane camera depth and 3D light interactions (Blender Grease Pencil).

To prevent proprietary software lock-in, Department 10 adopts an **Application-Owned Canonical Animation Model** (`AnimationProject`, `AnimationScene`, `CharacterRig`, `DrawingExposure`) with specialized adapters for execution engines:

```
                          [ AnimationScene / Shot ]
                                      │
                                      ▼
                        [ AnimationEngineRouter ]
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
[ LocalVectorRasterEngine ]   [ SkeletalPuppetEngine ]    [ HeadlessBlenderGPencil ]
• In-process Python/NumPy     • Hierarchical 2D bones     • Standalone Python (.py)
• Vector SVG & Raster Cel     • Forward / Inverse Kin     • 2D/3D multiplane depth
• Sub-millisecond on M4       • Cut-out body segmentation • Grease Pencil 3.0
• Zero network dependency     • Parameterized expressions • Remote GPU or local CLI
```

---

## 2. Engine Tier Responsibilities

### Tier 1: `LocalVectorRasterEngine` (In-Process Default)
- **Role:** Instant, deterministic 2D rendering on local Apple Silicon M4.
- **Capabilities:**
  - Frame-by-frame cel animation with exposure holds (1s, 2s, 3s).
  - Line art drawing with configurable stroke weights.
  - Multi-layer cel painting (flat base, core shadow, specular highlight).
  - Multiplane background parallax (foreground, midground, background depth layers).
  - Direct export to transparent PNG sequences, SVG vector XML, and ProRes 4444.

### Tier 2: `SkeletalPuppetEngine` (2D Rigging & Puppet System)
- **Role:** Cut-out character animation and skeletal bone deformation.
- **Capabilities:**
  - 2D bone tree with parent-child hierarchical coordinate spaces.
  - Analytical 2-Bone Inverse Kinematics (IK) for arms and legs.
  - Segmented body part sprite attachment with localized pivot points.
  - Viseme-driven mouth replacement and parameter-driven eye blinking.

### Tier 3: `HeadlessBlenderGPencilEngine` (2D/3D Hybrid)
- **Role:** Complex multiplane camera moves and 3D scene integration.
- **Capabilities:**
  - Generates standalone Blender Python scripts for Grease Pencil 3.0 stroke geometry.
  - Renders multiplane camera moves with spatial perspective and depth of field.
  - Dispatched via headless CLI (`blender -b -P script.py`) or packaged for remote cloud workers.

### Tier 4: `AIAnimationRouter` (Neural Motion & In-Betweening)
- **Role:** Pluggable AI generation for motion transfer, pose sequences, and AI in-betweens.
- **Capabilities:**
  - Ingests reference motion vectors and character identity embeddings.
  - Dispatches tasks to remote GPU workers (LivePortrait, ControlNet OpenPose, RIFE).
  - Provides deterministic local fallback using skeletal retargeting.
