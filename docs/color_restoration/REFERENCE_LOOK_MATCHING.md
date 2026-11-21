# Reference Look & Shot Matching Engine
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

The `ReferenceMatcher` provides automated color matching between a target clip and an aesthetic reference (still image or reference video). It ensures visual continuity across multi-camera setups, aligns lighting variations between shots in the same scene, and adopts creative reference grades while protecting human skin tones.

---

## 2. Core Matching Algorithms

1. **Reinhard Color Transfer in CIE $L\alpha\beta$:**
   Decorrelates luminance from chromatic axes, scaling channel means and standard deviations:
   $$L'_{S} = \frac{\sigma_{T,L}}{\sigma_{S,L}} (L_S - \mu_{S,L}) + \mu_{T,L}$$
   $$\alpha'_{S} = \frac{\sigma_{T,\alpha}}{\sigma_{S,\alpha}} (\alpha_S - \mu_{S,\alpha}) + \mu_{T,\alpha}$$
   $$\beta'_{S} = \frac{\sigma_{T,\beta}}{\sigma_{S,\beta}} (\beta_S - \mu_{S,\beta}) + \mu_{T,\beta}$$
2. **Skin-Tone Protection Masking:**
   Detects facial skin clusters and smoothly blends the original skin chrominance with the matched background using soft Gaussian feathering, preventing faces from adopting unintended color casts.
3. **Parametric Grading Graph Synthesis:**
   In addition to returning direct pixel transfers, `ReferenceMatcher` synthesizes an equivalent `GradingGraph` with exposure EV offsets, contrast slope, and creative look nodes for non-destructive reuse across entire scenes.
