# Color & Restoration Known Limitations & Mitigation Strategies
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

This document formalizes technical constraints, physical boundaries, and mitigation strategies for Department 16.

---

## 2. Known Limitations & Mitigations

### 2.1 Optical & Heavy Motion Blur
- **Limitation:** Blind deconvolution of severe non-linear or rotational motion blur cannot fully recover destroyed spatial information.
- **Mitigation:** The system uses Wiener deconvolution with conservative regularizers to prevent ringing artifacts, falling back to gentle micro-contrast sharpening rather than aggressive deconvolution.

### 2.2 Deep Shadow Noise in 8-Bit Low-Light Clips
- **Limitation:** Severely underexposed 8-bit footage lacks sensor quantization steps. Pushing shadow exposure reveals digital banding and macroblocking.
- **Mitigation:** `LowLightEnhancer` applies bilateral denoising in tandem with CLAHE and gamut-compresses near-black code values to minimize macroblocking.

### 2.3 SDR-to-HDR Inverse Tone Mapping
- **Limitation:** Converting an 8-bit SDR Rec.709 video to HDR10 (Rec.2100 PQ) does not create genuine 1000-nit high-dynamic-range detail.
- **Mitigation:** The studio explicitly flags inverse tone mapping as `SYNTHETIC_HDR_EXPANSION` and requires explicit user confirmation before applying HDR curves to SDR sources.

### 2.4 Video Super-Resolution Temporal Flickering
- **Limitation:** Frame-by-frame GAN upscaling can introduce high-frequency texture flickering across consecutive frames.
- **Mitigation:** The pipeline applies temporal moving-average stabilization on the high-frequency residual component, locking texture coherence across scene cuts.
