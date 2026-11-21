# 2D ANIMATION STUDIO ARCHITECTURE SPECIFICATION
**Department:** 10_animation_2d & 12_character_production  
**Document Version:** 1.0.0  
**Status:** Approved Technical Architecture  

---

## 1. System Overview

Department 10 (`10_animation_2d`) and Department 12 (`12_character_production`) provide the studio with a production-grade 2D animation, anime, and character pipeline. The architecture seamlessly integrates with AI Director (Department 06), Production Planning (Department 07), NLE Editing (Department 08), Motion Graphics (Department 09), VFX Compositing (Department 13), and Storage (Department 21).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             DEPARTMENTS 10 & 12: 2D ANIMATION & CHARACTER STUDIO            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐         ┌───────────────────────────────────┐  │
│  │ Character Identity Sys  │ ◄─────► │    Canonical Animation Project    │  │
│  │ • Persistent DNA Model  │         │ • Project, Scene, Shot, Layer     │  │
│  │ • Proportions, Palettes │         │ • Exposure sheets (1s, 2s, 3s)    │  │
│  │ • Model sheets (Settei) │         │ • RationalTime exact timebase     │  │
│  └────────────┬────────────┘         └─────────────────┬─────────────────┘  │
│               │                                        │                    │
│  ┌────────────▼────────────┐         ┌─────────────────▼─────────────────┐  │
│  │ 2D Skeletal & Cut-Out   │         │    Dedicated Anime Pipeline       │  │
│  │ • Hierarchical 2D bones │         │ • Layout (Reiauto) framing        │  │
│  │ • Analytical 2-Bone IK  │         │ • Key animation (Genga)           │  │
│  │ • Pivot-point cutouts   │         │ • Cel shading (Base, Shadow, High)│  │
│  │ • Parameterized Visemes │         │ • Multiplane parallax background  │  │
│  └────────────┬────────────┘         └─────────────────┬─────────────────┘  │
│               │                                        │                    │
│  ┌────────────▼────────────┐         ┌─────────────────▼─────────────────┐  │
│  │ Animation Asset Library │         │    Multi-Tier Render Engine       │  │
│  │ • Character Rigs & Poses│         │ • LocalVectorRasterEngine (M4)    │  │
│  │ • Expression Palettes   │ ◄─────► │ • Headless Blender GPencil 3.0    │  │
│  │ • Reusable Backgrounds  │         │ • Transparent ProRes 4444 Export  │  │
│  └─────────────────────────┘         └─────────────────┬─────────────────┘  │
│                                                        │                    │
│                                      ┌─────────────────▼─────────────────┐  │
│                                      │     Studio Pipeline Bridges       │  │
│                                      │ • TimelineBridge (NLE V1/V2/V3)   │  │
│                                      │ • DirectorBridge (Blueprints)     │  │
│                                      │ • AssetRegistry (SHA-256 SQLite)  │  │
│                                      └───────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Canonical Animation Project Schema (`departments/10_animation_2d/core/`)
- Pure Python dataclasses modeling the full hierarchy of a 2D animated production:
  - `AnimationProject`: Root container holding resolution, frame rate, characters, scenes, and asset references.
  - `AnimationScene`: Spatially and temporally bounded scene containing environment backgrounds, multiplane cameras, character instances, and audio guides.
  - `AnimationShot`: Shot breakdown with layout framing, camera moves, and character action tracks.
  - `AnimationTrack`: Linear track containing drawing exposures or keyframed bone transforms.
  - `DrawingExposure`: Traditional exposure element defining drawing index, duration in frames, and hold count (animating on 1s, 2s, or 3s).
  - `Camera2D`: Multiplane 2D camera with position $(x, y)$, depth $(z)$, zoom/scale, and rotation.

### 2.2 Character Creation & Identity System (`departments/10_animation_2d/characters/`)
- Persistent character DNA capturing facial structure, eye geometry, hairstyle, body proportions (head ratio), color palette, and costume layers.
- Model sheet generation (Settei): Front, 3/4, Profile (Side), Back turnarounds, and facial close-ups.
- Expression catalog (Neutral, Happy, Sad, Angry, Surprised, Confused, Smiling, Talking).
- Pose catalog (Standing, Walking, Running, Sitting, Jumping, Action).
- Automated identity consistency validation engine scoring deviations in proportions, colors, and line features.

### 2.3 2D Rigging & Puppet Animation (`departments/10_animation_2d/rigging/`)
- 2D bone tree with parent-child hierarchical coordinate transformations:
  $$T_{world} = T_{parent} \times T_{local}$$
- Analytical 2-Bone Inverse Kinematics (IK) with pole vector constraints for realistic elbow and knee bending.
- Cut-out body part hierarchy: Head, Torso, Upper Arm, Lower Arm, Hand, Thigh, Shin, Foot.
- Lip-sync facial viseme controller: `REST`, `AI_A`, `E_EE`, `O_OH`, `U_OO`, `M_B_P`, `F_V`, `L_TH`.

### 2.4 Traditional Frame-by-Frame & Anime Engine (`departments/10_animation_2d/anime_pipeline/`)
- Traditional Exposure Sheet (X-Sheet) timeline modeling key animation (Genga) and in-betweens (Doga).
- Cel Shading Color Engine: Three-tier shading (Flat Base Color, Cast/Core Shadow Layer, Specular Rim Highlight) conforming to anime production standards.
- Multiplane Parallax Backgrounds: Foreground, Midground, and Background plates scrolling at depth-scaled velocities:
  $$V_{layer} = \frac{V_{camera}}{1.0 + Z_{depth}}$$

### 2.5 Multi-Tier Rendering & Export Engine (`departments/10_animation_2d/rendering/`)
- Vector SVG XML generator for resolution-independent web and motion graphics integration.
- 32-bit RGBA raster renderer utilizing Pillow with FFmpeg pipe encoding directly to Apple ProRes 4444 (`yuva444p10le`) and WebM (`yuva420p`) with full alpha transparency.
- Sprite sheet packager with frame bounding metadata JSON.

### 2.6 Studio Pipeline Integration (`departments/10_animation_2d/integrations/`)
- **`TimelineAnimationAdapter`:** Automatically inserts rendered character animations onto NLE timeline track `V1` (as full scenes) or track `V3` (as transparent overlays over live-action/motion graphics).
- **`DirectorAnimationBridge`:** Ingests Department 04 `PlannedShot` records, translates storyboard sketches into keyframe tracks, and auto-schedules character animation tasks.
