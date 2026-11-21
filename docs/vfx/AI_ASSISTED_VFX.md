# AI-ASSISTED VFX SPECIFICATION
**Department:** 13_vfx_compositing  
**Topic:** Multimodal Prompt Interpretation, Automated Node Graph Synthesis, and AI Inpainting  

---

## 1. Role of AI in Department 13

AI serves two distinct, high-leverage roles in the VFX studio:
1. **The Creative VFX Supervisor (High-Level Planning):**
   Interprets director notes (e.g. *"Insert high-tech holographic UI over the tablet and add an ethereal blue rim light"*) and synthesizes a complete, valid `CompositingGraph` with appropriate node parameters and layer hierarchy.
2. **Deep Learning Vision Tasks (Heavy Processing):**
   Executes tasks where deterministic heuristics fall short:
   - Zero-shot segmentation (SAM 2.1).
   - High-fidelity temporal video inpainting (ProPainter / E2FGVI).
   - Deep neural color transfer and plate harmonization.

---

## 2. AI VFX Supervisor Decision Engine

```
[ Creative Director Note / PlannedShot ]
                 │
                 ▼
      [ Multimodal Plate Analysis ]
      • Aspect ratio, lighting direction, dominant colors
      • Object presence (screens, actors, backgrounds)
                 │
                 ▼
      [ Graph Recipe Selection ]
      • Recipe: Screen Replacement
      • Recipe: Green Screen Extraction & BG Swap
      • Recipe: Clean Plate / Wire Removal
      • Recipe: Atmospheric Light Wrap & Glow
                 │
                 ▼
      [ Parameter Synthesis & Validation ]
      • Corner pinning coordinates
      • Color balance matching
      • Cycle-free DAG verification
                 │
                 ▼
      [ Executable CompositingGraph ]
```

---

## 3. Inpainting & Video Cleanup

When objects (wires, microphones, logos, blemishes, unwanted pedestrians) must be removed:
- **Local Fallback (Deterministic):**
  - OpenCV Fast Marching (Telea): propagates boundary colors inward along the gradient vectors.
  - OpenCV Navier-Stokes: models fluid equations to continue isophotes (lines of equal luminance) into the inpainting zone.
- **Remote GPU Dispatch:**
  - Generates optical flow across consecutive frames to borrow missing pixels from unoccluded past/future frames before synthesizing residual missing textures.
