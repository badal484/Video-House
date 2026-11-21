# Color & Restoration Quality Control (QC) Specification
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

Quality control in Department 16 is enforced by two specialized auditors:
1. **`ColorQualityController`:** Inspects pixel gamut limits, clipping thresholds, and HDR metadata.
2. **`RestorationQualityController`:** Verifies duration, frame rate, audio synchronization, and calculates objective fidelity metrics (PSNR, SSIM).

---

## 2. Review States & Automated Decision Matrix

Every job evaluates to one of six formal review states:
- **`PASSED`:** Zero out-of-range pixels, clipping $<5\%$, duration matches source within $50\text{ms}$, audio fully synchronized.
- **`WARNING`:** Minor clipping ($5-10\%$), frame rate interpolation rounding flag, or soft gamut roll-off.
- **`NEEDS_HUMAN_REVIEW`:** Highlight clipping $>10\%$, significant skin-tone hue deviation, or HDR MaxCLL warning.
- **`FAILED`:** Corrupt frames, duration delta $>0.05\text{s}$, audio synchronization lost, or HDR MaxFALL exceeding MaxCLL.
- **`PROCESSING`:** Job currently executing in background worker pool.
- **`UNCHECKED`:** Initial job ticket state awaiting quality audit.

---

## 3. Objective Metrics

- **PSNR (Peak Signal-to-Noise Ratio):** Measures logarithmic mean squared error in dB against ground truth.
- **SSIM (Structural Similarity Index):** Measures perceptual structural degradation, luminance distortion, and contrast loss.
- **Note on AI Detail Reconstruction:** Where ground truth does not exist (e.g. single-image super-resolution), PSNR is not treated as an absolute quality metric. The system relies on human review and edge-coherence checks.
