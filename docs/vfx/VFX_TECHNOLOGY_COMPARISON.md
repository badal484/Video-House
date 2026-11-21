# VFX & COMPOSITING TECHNOLOGY COMPARISON MATRIX
**Department:** 13_vfx_compositing  
**Scope:** Evaluation of tools, libraries, engines, and algorithms for programmatic studio deployment  

---

## 1. Engine & Compositing Framework Comparison

| Framework / Engine | Type | Strengths | Weaknesses | License | Studio Role |
|---|---|---|---|---|---|
| **Local OpenCV / NumPy / PIL** | In-process Python | 100% deterministic, zero network dependency, instant startup, sub-millisecond per frame on M4 | Limited to 2D nodes, no built-in 3D raytracing | Apache 2.0 / BSD | **Primary Local Compositing Engine** |
| **Headless Blender (Cycles/EEVEE)** | Headless binary / script | Complete node compositor, OpenEXR 32-bit float, Cryptomatte, 3D passes, ACEScg support | Requires Blender installed or remote worker; slower cold start | GPL-3.0 (Script orchestration is isolated process) | **Primary 3D & Deep Compositing Engine** |
| **Natron** | Standalone Node Compositor | OpenFX standard, Nuke-compatible node graph | Stagnant development, heavy GUI dependency, complex headless API | GPL-2.0 | Reference architecture for DAG schema |
| **FFmpeg libavfilter** | CLI / C Library | Ultra-fast stream filtering, extensive codecs | Limited node graph flexibility, awkward multi-branch graphs | LGPL-2.1+ / GPL-2.0+ | Final export & format encoding |
| **Nuke / Flame** | Commercial Proprietary | Gold standard Hollywood VFX | Closed source, heavy per-seat licensing cost ($3k-$10k) | Proprietary Commercial | Benchmark for node schema design |

---

## 2. Tracking & Matchmoving Tool Comparison

| Solution | Algorithm / Model | Local M4 Feasibility | 4-Point Homography | 3D Camera Solve | Studio Recommendation |
|---|---|---|---|---|---|
| **OpenCV Lucas-Kanade + Shi-Tomasi** | Optical Flow pyramid LK | Instant (< 5ms/frame) | Built-in via RANSAC | Essential Matrix solve | **Integrated Local Tracker** |
| **Mocha Pro** | Planar Shear/Translation | Proprietary | Yes | Yes | Commercial benchmark |
| **Blender Motion Tracker** | Hybrid KLT + planar | Excellent (headless) | Yes | Full 3D bundle adjustment | Headless 3D Matchmove Engine |
| **CoTracker3 / TAPIR** | Transformer Point Tracking | Requires PyTorch GPU | Indirect | No | Remote GPU dispatch |

---

## 3. Matting & Keying Tool Comparison

| Technique | Approach | Quality | Performance | Edge Handling | Recommendation |
|---|---|---|---|---|---|
| **Color Difference Despill + HSV Keyer** | Deterministic Euclidean / Chroma distance | High on clean backdrops | Sub-millisecond | Gaussian feather + Erosion | **Default Local Keyer** |
| **OpenCV GrabCut** | Graph Cuts Energy Minimization | High on complex boundaries | 50–150ms/frame | Soft boundary alpha | **Interactive/Box Roto** |
| **Segment Anything 2 (SAM 2.1)** | Vision Transformer + Video Memory | State of the art | Heavy (requires 8GB+ GPU for video) | Crisp segmentation | **Remote AI Roto Worker** |
| **RobustVideoMatting (RVM)** | Recurrent Neural Network | Production ready for humans | 30-60 FPS on CUDA | Soft hair/transparency | **Cloud Human Matting** |

---

## 4. Inpainting & Cleanup Tool Comparison

| Tool / Method | Class | Speed | Texture Fidelity | Temporal Stability | Studio Role |
|---|---|---|---|---|---|
| **OpenCV Telea (Fast Marching)** | Deterministic Differential | 2ms/frame | Good for thin scratches, wires, small spots | Deterministic per-frame | **Default Local Inpainter** |
| **OpenCV Navier-Stokes** | Fluid Dynamics PDE | 4ms/frame | Smooth gradients, water/sky | Deterministic | **Local Texture Inpainter** |
| **ProPainter / E2FGVI** | Optical Flow Guided Video AI | 2-5 sec/frame (GPU) | Photorealistic, handles large moving objects | Excellent | **Remote GPU Cleanup Pass** |
| **LaMa (Large Mask Inpainting)** | Fourier Convolution Network | 500ms/frame | High static fidelity | Moderate temporal jitter | **Single Frame Patch Inpainter** |
