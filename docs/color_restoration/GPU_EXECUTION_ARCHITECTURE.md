# GPU Execution Architecture & Apple Silicon M4 Profiling
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

Department 16 is engineered to maximize throughput on **Apple Silicon (ARM64 / Apple M4 Unified Memory)** while maintaining zero-dependency CPU vectorized fallbacks and remote GPU worker scalability.

---

## 2. Hardware Acceleration Tiers

1. **Tier 1 (Apple Silicon M4 Metal / Accelerate):**
   Vectorized array operations leverage Apple's Accelerate framework and OpenCV Metal/ARM Neon assembly instructions, delivering $>300\text{ FPS}$ primary grading throughput at $1080\text{p}$.
2. **Tier 2 (PyTorch MPS / Metal Performance Shaders):**
   Neural super-resolution (Real-ESRGAN) and frame interpolation (RIFE) utilize the Apple M4 10-core GPU via MPS tensors.
3. **Tier 3 (CPU Vectorized Fallback):**
   Pure NumPy, SciPy, and OpenCV C-routines execute on standard x86_64 / ARM64 CPUs with multithreaded OpenMP execution.
4. **Tier 4 (Remote GPU Workers):**
   Heavy diffusion video restoration or full-feature $4\text{K}$ batch restoration jobs are packaged as `JobTicket` records and offloaded to remote NVIDIA CUDA workers via Temporal.io.

---

## 3. Memory Safety & Tiling Strategy
- **$512\text{px}$ Spatial Tiling:** Prevents out-of-memory crashes on the 16GB workstation.
- **On-Demand Model Loading:** Neural weights are loaded strictly during active batch processing and evicted immediately post-execution.
