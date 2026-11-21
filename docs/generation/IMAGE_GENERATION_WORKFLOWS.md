# AI Image Generation & Editing Workflows
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation  
**Document:** IMAGE_GENERATION_WORKFLOWS.md  
**Version:** 1.0.0  

---

## 1. Production Image Roles

Generated imagery serves four critical departments in the studio:
1. **Storyboard & Concept Art**: Department 04 (AI Director).
2. **Motion Graphics Assets & Textures**: Department 09 (Motion Graphics).
3. **VFX Matte Paintings & Clean Plates**: Department 13 (VFX Compositing).
4. **2D Character Sheets & Backgrounds**: Department 10 (2D Animation).

---

## 2. Inpainting, Outpainting & Variation Pipeline

```
Original Image Frame
         │
         ├──> [Inpainting Mask] ──> Masked Region Generation (e.g. object replacement)
         │
         ├──> [Canvas Expansion] ──> Outpainting (extend 16:9 to 2.39:1 anamorphic)
         │
         └──> [Image Variation] ──> Multi-seed stylistic exploration
```

- **Mask Handling**: Inpainting accepts single-channel 8-bit masks where white ($255$) indicates regions to regenerate and black ($0$) indicates preserved pixels.
- **Resolution Preservation**: Generates at native model resolution ($1024\times 1024$ or $2048\times 2048$) with metadata tracking for derivative proxy generation.
