# VFX & COMPOSITING LICENSE AUDIT
**Department:** 13_vfx_compositing  
**Scope:** Verification of third-party software, libraries, and models against studio commercial licensing rules  

---

## 1. Studio License Policy Principles

1. **Permissive In-Process Code:** Core runtime libraries imported directly into the Python process must adhere to MIT, Apache-2.0, BSD-2/3-Clause, or Python Software Foundation licenses.
2. **Zero In-Process AGPL-3.0:** AGPL-3.0 libraries are strictly prohibited from being imported into the core in-process runtime.
3. **Isolated Process Boundaries for GPL:** Tools with GPL licenses (such as standalone Blender CLI or FFmpeg with GPL filters) must be executed exclusively as separate subprocesses via standard stdin/stdout, CLI arguments, or JSON/file interfaces.
4. **No Non-Commercial (CC-BY-NC) Weights in Core Pipeline:** Pre-trained weights or AI models restricted to non-commercial research cannot be bundled or required for commercial production outputs.

---

## 2. Dependency Audit Matrix

| Library / Tool | Current Version | License Type | Compliance Status | Usage Constraints |
|---|---|---|---|---|
| **OpenCV (`opencv-python`)** | 5.0.0 | Apache 2.0 | **APPROVED** | In-process image processing, tracking, keying, inpainting |
| **NumPy** | 2.4.2 | BSD-3-Clause | **APPROVED** | High-performance matrix mathematics and vector operations |
| **Pillow (PIL)** | 12.1.1 | HPND / MIT-like | **APPROVED** | Image I/O, RGBA buffer manipulation, alpha composition |
| **FFmpeg** | 8.1.2 | LGPL 2.1+ | **APPROVED** | Out-of-process subprocess execution for media multiplexing |
| **Blender (Headless)** | 4.x / 3.x | GPL-3.0 | **APPROVED VIA SUBPROCESS** | Headless CLI invocation (`blender -b -P script.py`); zero in-process linkage |
| **OpenColorIO (OCIO)** | v2 (Specification) | BSD-3-Clause | **APPROVED** | Color transformation math and linear ACEScg conversions |
| **OpenTimelineIO** | 0.16.0 | Apache 2.0 | **APPROVED** | ASWF editorial timeline integration |

---

## 3. Remote AI Model License Audit

| Model / Architecture | Original Publisher | Original License | Studio Integration Mode |
|---|---|---|---|
| **SAM 2.1 (Segment Anything)** | Meta AI | Apache 2.0 | Remote GPU worker (HTTP/REST API) |
| **RobustVideoMatting (RVM)** | ByteDance | GPL-3.0 | Remote containerized microservice; isolated network RPC |
| **ProPainter** | SCUT / NTU | Apache 2.0 | Remote worker for flow-guided video inpainting |
| **E2FGVI** | Fudan University | Apache 2.0 | Remote worker for video cleanup |

---

## 4. Verification Sign-Off

Department 13 (`13_vfx_compositing`) maintains 100% compliance with commercial studio licensing requirements. All local in-process modules rely exclusively on Apache 2.0, BSD-3-Clause, and MIT licensed foundations.
