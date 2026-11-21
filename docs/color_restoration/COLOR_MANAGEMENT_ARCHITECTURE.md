# Color Management Architecture & Scene-Referred Pipeline
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Color Management Architecture

The studio implements a **scene-referred color-managed architecture** based on the Academy Color Encoding System (ACES) and OpenColorIO (OCIO) standards.

```
[Camera Log / Raw / Rec.709 / AI Media]
                 |
                 v   (Input Device Transform - IDT)
        [Linear ACEScg / AP1]  <---- Physical Scene Radiance [0.0, 100.0+]
                 |
                 +---> Grading Operations (EV Exposure, White Balance, Contrast)
                 +---> VFX Compositing (Additive blending, Light wraps)
                 +---> Super-Resolution & Neural Restoration
                 |
                 v   (Output Device Transform - ODT / ACES RRT Tone Curve)
[Target Display: Rec.709 (SDR) / Display P3 / Rec.2100 PQ/HLG (HDR)]
```

---

## 2. Ingest & Color Space Detection

When an asset is ingested:
1. `ColorManager.detect_color_space_from_metadata()` inspects FFprobe primaries (`color_primaries`) and transfer characteristics (`color_transfer`).
2. Known cinema camera profiles (ARRI LogC3, Sony S-Log3, Canon C-Log3, RED Log3G10) are mapped to their respective IDTs.
3. HDR broadcast formats (`smpte2084`, `arib-std-b67`) are mapped to `REC2100_PQ` or `REC2100_HLG`.
4. Ambiguous or missing tags safely default to `REC709` BT.1886 with a warning flag, ensuring footage is never silently misinterpreted.

---

## 3. Precision & Internal Representation

- **Bit Depth:** All internal color transforms and node graph operations execute in **IEEE 754 32-bit floating point (`float32`)**.
- **Quantization Protection:** Processing in 32-bit float prevents banding, posterization, and rounding drift across chained grading nodes.
- **Display Output:** Final renderers convert float32 to 8-bit, 10-bit (`yuv422p10le`), or 12-bit integer formats during encoding.
