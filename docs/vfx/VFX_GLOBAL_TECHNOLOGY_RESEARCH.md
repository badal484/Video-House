# GLOBAL TECHNOLOGY RESEARCH: VFX & COMPOSITING SYSTEMS
**Department:** 13_vfx_compositing  
**Scope:** Global state of the art in visual effects, compositing node graphs, tracking, and AI matting  

---

## 1. Industry Standard Compositing Architectures

In high-end visual effects and post-production, compositing systems fall into three primary archetypes:

### 1.1 Node-Based Compositing (The Industry Standard)
- **Foundry Nuke / Natron / Blackmagic Fusion / Blender Compositor:**
  - Operates on a Directed Acyclic Graph (DAG) of image manipulation nodes.
  - Image data flows downstream from generator/reader nodes to viewer/writer nodes.
  - Channels (RGBA + arbitrary AOVs like Z-depth, World Normal, Cryptomatte) flow through unified pipelines.
  - Spatial, temporal, and mathematical operations are decoupled from track/timeline constraints.

### 1.2 Layer-Based Compositing
- **Adobe After Effects:**
  - 2D/2.5D layer stacking with transfer modes, masks, and effect stacks.
  - Well suited for motion graphics and short graphic shots, but brittle for complex multi-pass 3D integration, deep compositing, and branchable pipeline automation.

### 1.3 Programmatic & Headless Compositing
- **OpenCV / OpenImageIO / FFmpeg libavfilter / VapourSynth / Blender Python:**
  - Scriptable batch execution of image transformations, filtering, and blending.
  - Critical for headless production servers, automated pipeline workflows, and reproducible cloud rendering.

---

## 2. Core VFX Problem Domains & Global Technology Solutions

### 2.1 Keying and Matting (Green / Blue Screen)
- **Primatte / Keylight / IBK Color (Foundry Nuke):** High-end production keyers using 3D color cube separation, screen color subtraction, and edge erosion/dilation.
- **Fast Local & Open Implementations:**
  - HSV/Lab color space chroma distance segmentation with soft thresholding.
  - Color difference despill algorithms (e.g. Green despill: `G = min(G, (R + B) / 2)`).
  - Alpha matte post-processing: erosion, dilation, Gaussian edge feathering, and edge blur.
- **Deep Learning Matting:**
  - RobustVideoMatting (RVM), MODNet, Matting Anything (MAM), BackgroundMattingV2.

### 2.2 Rotoscoping and Segmentation
- **Traditional Roto:** Bezier/B-Spline curve tracking with sub-pixel feathering.
- **AI-Assisted Segmentation:**
  - Segment Anything Model (SAM / SAM 2 / SAM 2.1): Prompt-based mask generation using positive/negative point clicks and bounding boxes with temporal optical flow memory for cross-frame propagation.
  - Fast local Fallback: GrabCut (iterative Graph Cuts energy minimization) and adaptive thresholding for instant local execution.

### 2.3 Motion Tracking & Matchmoving
- **Feature Point Tracking:** Shi-Tomasi corner detection with Lucas-Kanade optical flow (`cv2.calcOpticalFlowPyrLK`).
- **Planar Tracking (Mocha style):** 4-point homography estimation (`cv2.findHomography` / `cv2.warpPerspective`) tracking coplanar surfaces (screens, billboards, signs, walls) over time.
- **3D Camera Solving:** Structure from Motion (SfM), 8-point algorithm / Essential matrix decomposition (`cv2.findEssentialMat`, `cv2.recoverPose`) to reconstruct 3D camera trajectory and focal length.

### 2.4 Video Cleanup and Inpainting
- **Traditional Video Inpainting:** Navier-Stokes fluid-dynamics propagation and Telea fast marching method (`cv2.inpaint`).
- **Deep Learning Temporal Inpainting:** E2FGVI (End-to-End Flow-Guided Video Inpainting), ProPainter, Repaint.

### 2.5 Light Wrapping, Atmospherics & Optical Effects
- **Light Wrap:** Bleeding background light luminance across the foreground matte edges to seat subjects realistically into bright backgrounds.
- **Atmospherics & Particles:** Procedural fog noise, smoke plumes, floating dust motes, and volumetric glows.
- **Optical Simulation:** Lens flares, chromatic aberration (radial RGB channel displacement), anamorphic bokeh, and camera shake.

---

## 3. Color Management & Mathematical Foundations

### 3.1 Premultiplied vs. Straight Alpha
- **Straight (Unpremultiplied) Alpha:** Color channels $(R, G, B)$ and Alpha $(A)$ are stored independently:
  $$C_{straight} = (R, G, B, A)$$
- **Premultiplied Alpha:** Color values have already been scaled by alpha:
  $$C_{premul} = (R \cdot A, G \cdot A, B \cdot A, A)$$
- In professional compositing, **all merge/over blending operations must be calculated in premultiplied space**:
  $$C_{out} = C_A + C_B \cdot (1 - \alpha_A)$$
  This avoids black halo fringes along high-contrast antialiased boundaries.

### 3.2 Linear vs. Non-linear Color
All optical and light-summation math (blurring, glows, motion blur, layering) must be executed in **linear radiance space**. Calculating glows or blurs in gamma-encoded Rec.709 sRGB yields unnaturally dark boundaries and clipped highlight physics.

