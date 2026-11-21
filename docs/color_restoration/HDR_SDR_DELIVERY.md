# High Dynamic Range (HDR) & Standard Dynamic Range (SDR) Delivery
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

Mastering video for diverse display targets requires rigorous colorimetric conversions and tone mapping. Department 16 provides mathematical conversions between:
- **SDR Rec.709** ($100\text{ nits}$, BT.1886 / Gamma 2.4)
- **Web sRGB** ($100\text{ nits}$, sRGB Piecewise)
- **Display P3** ($100-500\text{ nits}$, DCI-P3 Primaries, D65 White Point)
- **Ultra HD Rec.2020** ($100-1000\text{ nits}$, Wide Color Gamut)
- **HDR10 (SMPTE ST 2084 PQ)** ($1,000 - 4,000\text{ nits}$, Absolute Luminance)
- **Hybrid Log-Gamma (HLG / BT.2100)** ($1,000\text{ nits}$, Relative Luminance)

---

## 2. Tone Mapping Operators (`ToneMapper`)

1. **ACES Reference Rendering Transform (RRT) Tone Scale:**
   Mimics traditional photochemical film exposure response, providing pleasing highlight shoulder compression and skin-tone preservation.
2. **Hable (Uncharted 2) Filmic Tone Curve:**
   Generates warm, cinematic highlight roll-off and deep, uncrushed shadow toes.
3. **Reinhard Extended Tone Curve:**
   Allows customizable white-point burn threshold, compressing high-luminance peaks into $[0.0, 1.0]$ without sudden hard clipping.

---

## 3. HDR Metadata Management
- Conformed exports preserve **SMPTE ST 2086** mastering display metadata (`color_primaries`, `white_point`, `min_luminance`, `max_luminance`).
- Calculates and injects **MaxCLL** (Maximum Content Light Level) and **MaxFALL** (Maximum Frame-Average Light Level) into FFmpeg stream headers.
