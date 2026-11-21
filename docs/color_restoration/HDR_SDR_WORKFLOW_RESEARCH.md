# High Dynamic Range (HDR) & Standard Dynamic Range (SDR) Delivery Workflows
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

Modern video production requires simultaneous mastering for High Dynamic Range (HDR) television/theatrical displays and Standard Dynamic Range (SDR) mobile/web platforms. Delivering inconsistent or poorly mapped HDR causes dark, muddy video on SDR devices, washed-out colors, or blown-out highlight clipping.

This document formalizes the colorimetric transforms, gamut compression techniques, and tone-mapping operators used in Department 16 to ensure flawless bidirectional delivery.

---

## 2. HDR Delivery Standards

| Specification | Peak Luminance | Dynamic Range | Transfer Function | Color Gamut | Metadata Required |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SDR (Rec.709)** | $100\text{ nits}$ | $\sim 6\text{ stops}$ | BT.1886 (Gamma 2.4) / sRGB | Rec.709 | None |
| **HDR10 (SMPTE ST 2084)** | $1,000 - 4,000\text{ nits}$ | $\sim 14-17\text{ stops}$| Perceptual Quantizer (PQ) | Rec.2020 | Static (SMPTE ST 2086, MaxCLL, MaxFALL) |
| **HLG (ITU-R BT.2100)** | $1,000\text{ nits}$ | $\sim 12\text{ stops}$ | Hybrid Log-Gamma | Rec.2020 | None (Backward-compatible with SDR) |
| **Dolby Vision** | $1,000 - 10,000\text{ nits}$| $\sim 17+\text{ stops}$ | ST 2084 (PQ) | Rec.2020 / P3 | Dynamic frame-by-frame XML metadata |

---

## 3. Mathematical Tone Mapping Operators

When converting scene-referred linear or HDR PQ signals to display-referred SDR ($0-100\text{ nits}$), tone mapping compresses highlights smoothly into display limits without posterization or hue shifts:

### 3.1 Reinhard Tone Mapping
$$L_{d}(x) = \frac{L_{w}(x)}{1 + L_{w}(x)}$$
Extended with white point burn:
$$L_{d}(x) = \frac{L_{w}(x) \left(1 + \frac{L_{w}(x)}{L_{white}^2}\right)}{1 + L_{w}(x)}$$

### 3.2 ACES Reference Rendering Transform (RRT) Tone Curve
ACES uses a piecewise cubic spline with a defined shoulder, midtone slope, and toe to mimic photochemical film response, preventing skin tones from shifting yellow/orange under high exposure.

### 3.3 Hable (Uncharted 2) Film Tone Curve
$$f(x) = \frac{x(Ax + CB) + DE}{x(Ax + B) + DF} - \frac{E}{F}$$
where $A=0.15, B=0.50, C=0.10, D=0.20, E=0.02, F=0.30$. Provides smooth toe rolloff and pleasing highlight desaturation.

---

## 4. Gamut Compression
Displaying wide-gamut colors (Rec.2020 or ACEScg) on narrower displays (Rec.709) causes out-of-gamut clipping where saturated highlights lose all texture.
- **Department 16 Gamut Compression:** Applies a directional 3D radial compression vector towards the achromatic axis, retaining chromatic gradient information while bringing all coordinates within the Rec.709 boundary.
