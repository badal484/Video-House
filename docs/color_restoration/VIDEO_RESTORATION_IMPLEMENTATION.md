# Video Restoration Implementation & Modular Filter Pipeline
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

The restoration pipeline in Department 16 (`RestorationPipeline`) executes a modular chain of non-destructive signal processing algorithms and neural models. Original source media is strictly preserved, and restored masters are registered as independent derivatives in the Central Asset Database.

---

## 2. Restoration Modules & Operations

1. **`VideoDeinterlacer`:**
   Converts 1080i/480i field-based video to progressive scan using motion-adaptive line interpolation (YADIF algorithm equivalent) with field-order auto-detection (`tff` / `bff`).
2. **`VideoDeflickerer`:**
   Stabilizes frame-to-frame exposure flutter caused by vintage mechanical shutters, archive film decay, or time-lapse steps via rolling temporal moving-average luminance tracking.
3. **`VideoStabilizer`:**
   Extracts Shi-Tomasi corner features across consecutive frames, estimates 2D affine partial transforms via Lucas-Kanade pyramidal optical flow, and applies moving-window trajectory smoothing.
4. **`ScratchDustRemover`:**
   Isolates vertical physical film scratches and dust specs using median-difference thresholding, inpainting damaged pixels via Alexandru Telea's Fast Marching Method.
5. **`VideoDenoiser`:**
   Applies spatial bilateral filtering and temporal windowed Non-Local Means (NLM) to remove CMOS sensor grain and high-ISO noise while preserving sharp object contours.
6. **`VideoDeblurrer`:**
   Restores edge sharpness and removes motion blur using point spread function (PSF) estimation and Wiener deconvolution.
7. **`LowLightEnhancer`:**
   Reveals shadow information in underexposed clips using Multi-Scale Retinex (MSR) and adaptive Contrast Limited Adaptive Histogram Equalization (CLAHE).
