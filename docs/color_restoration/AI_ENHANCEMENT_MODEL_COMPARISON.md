# AI Enhancement & Super-Resolution Model Comparison
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

Super-resolution and neural enhancement models reconstruct high-resolution video frames from low-resolution, compressed, or blurry sources. In film and broadcast production, upscaling is required for mastering archival footage (480p SD to 1080p HD, or 1080p HD to 4K UHD), restoring vintage animation, and preparing social media clips for high-resolution distribution.

This report evaluates key contemporary neural super-resolution models:
- **Real-ESRGAN** (General Live-Action & Anime variants)
- **BasicVSR++** (Recurrent Video Super-Resolution)
- **VRT / RVRT** (Video Restoration Transformer)
- **SwinIR / Restormer** (Transformer Image Restoration)
- **SeedVR / FlashVSR** (Modern Video Diffusion Super-Resolution)
- **Bicubic / Lanczos Baseline** (Deterministic Mathematical Baseline)

---

## 2. Comparative Matrix

| Model / Architecture | Primary Domain | Scale Factors | Temporal Consistency | Commercial License Status | Local Hardware Feasibility (Apple M4 16GB) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Real-ESRGAN (x4plus)** | General Live Action | 2x, 4x | Medium (Per-frame GAN) | BSD-3-Clause (Permissive) | Excellent (~1.2s per 1080p frame, MPS/CPU) |
| **Real-ESRGAN Anime6B** | 2D Animation / Cel | 4x | High (Smooth cel gradients) | BSD-3-Clause (Permissive) | Excellent (Lightweight 6-block RRDBNet) |
| **BasicVSR++** | Video Super-Resolution | 4x | Very High (Bidirectional flow) | Apache-2.0 (OpenMMLab) | Moderate (Memory intensive on 1080p chunks) |
| **VRT (Video Restor. Transformer)**| Multi-task Video | 4x | State-of-the-art | Non-Commercial / Research Only | Heavy (Requires >24GB VRAM GPU) |
| **Restormer** | Denoising / Deblur | 1x (Restoration)| N/A (Image-level) | Apache-2.0 | Good (Transposed self-attention) |
| **RIFE v4.6** | Frame Interpolation | 2x, 4x fps | Excellent | MIT (Permissive) | Good on Metal/MPS or CPU |
| **Lanczos-4 Baseline** | Deterministic Scaling| Any arbitrary | Perfect (Deterministic) | Public Domain / Permissive | Real-time (>60 fps) |

---

## 3. Commercial License Warnings & Traps

> [!WARNING]
> Many academic video restoration models (e.g. VRT, RVRT, early BasicVSR checkpoints, and some SwinIR weights trained on non-commercial datasets) carry **CC-BY-NC (Creative Commons Non-Commercial)** restrictions.
> 
> **Department 16 Rule:** The core studio runtime must strictly use models whose architecture and weights permit commercial use:
> 1. **Real-ESRGAN** (BSD-3-Clause).
> 2. **RIFE** (MIT License).
> 3. **Restormer / OpenMMLab BasicVSR++ Apache 2.0 checkpoints**.
> 4. Deterministic classical signal processing algorithms (Lanczos, YADIF, Bilateral, Wiener) which are 100% royalty-free and license-safe.

---

## 4. Tiling & Memory Strategy for Apple Silicon M4 (16GB RAM)

Processing a 4K frame ($3840 \times 2160 \times 3$ channels $\times 32$-bit float) requires $\sim 100\text{ MB}$ raw buffer, but forward passes through deep convolutional networks expand memory consumption by $40\times-60\times$ ($\sim 4-6\text{ GB}$).

To prevent out-of-memory (OOM) crashes:
1. **Spatial Tiling:** Images larger than $1080\text{p}$ are divided into overlapping tiles (e.g. $512 \times 512$ with $32\text{px}$ margin padding).
2. **Linear Cosine Feathering:** Tile seams are blended using cosine weighted alpha ramps to completely eliminate visible boundary seams.
3. **Chunked Video Processing:** Frames are processed in streaming batches of 8-16 frames, flushing intermediate buffers post-encode.
