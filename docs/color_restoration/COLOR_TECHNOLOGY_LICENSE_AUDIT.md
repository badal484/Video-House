# Color & Restoration Technology Commercial License Audit
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

Every software library, algorithmic formulation, and pretrained neural model checkpoint integrated into Department 16 must be audited for commercial licensing compliance. Copyleft licenses (GPL v3, AGPL v3) and non-commercial model weights (CC-BY-NC) present severe intellectual property risks for commercial video production.

This audit establishes the approved technology stack for Department 16.

---

## 2. Commercial License Audit Matrix

| Technology / Component | Repository / Provider | Code License | Weights License | Commercial Use Permitted | Action / Architectural Boundary |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **OpenColorIO (OCIO)** | Academy Software Foundation | BSD-3-Clause | N/A | **YES** | Core in-process dependency & config standard |
| **ACES (AMPAS)** | Academy of Motion Picture Arts | Permissive | N/A | **YES** | Core mathematical standard (SMPTE ST 2065-1) |
| **NumPy / SciPy** | SciPy Community | BSD-3-Clause | N/A | **YES** | Core in-process array and signal processing |
| **OpenCV (cv2)** | OpenCV Foundation | Apache-2.0 | N/A | **YES** | Core in-process computer vision & filtering |
| **Pillow (PIL)** | Alex Clark et al. | HPND | N/A | **YES** | Image I/O and format encoding |
| **Real-ESRGAN** | xinntao / Real-ESRGAN | BSD-3-Clause | BSD-3-Clause | **YES** | Approved for super-resolution & upscaling |
| **RIFE v4.6** | hzwer / Practical-RIFE | MIT | MIT | **YES** | Approved for frame rate conversion & slow-mo |
| **Restormer** | Syed Waqas Zamir et al. | Apache-2.0 | Apache-2.0 | **YES** | Approved for denoising and deblurring |
| **YADIF Deinterlacer** | FFmpeg / libavfilter | LGPL-2.1+ | N/A | **YES** | Subprocess invocation or in-process filter |
| **BasicVSR++** | OpenMMLab (mmediting) | Apache-2.0 | Apache-2.0 | **YES** | Video super-resolution (Apache weights only) |
| **VRT / RVRT** | Jiezhang et al. | Apache-2.0 | **CC-BY-NC 4.0** | **NO (FORBIDDEN)** | **REJECTED from commercial core runtime** |
| **DaVinci Resolve API** | Blackmagic Design | Proprietary | N/A | Restricted | Optional external desktop bridge only |

---

## 3. License Hygiene Directives

1. **Strictly Forbidden:** Models carrying `CC-BY-NC`, `CC-BY-NC-SA`, or unclear research-only licensing are strictly prohibited from in-process deployment.
2. **Attribution Logging:** All generated derivatives retain provenance metadata identifying the exact algorithm, model version, and license identifier in `derivative_metadata.json`.
