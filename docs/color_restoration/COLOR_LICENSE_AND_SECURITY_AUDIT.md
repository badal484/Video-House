# Color & Restoration License and Security Audit
**Project:** Universal AI Video Production Studio  
**Department:** 16 — Color Grading, Color Management, Video Restoration & Enhancement  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Executive Summary

All algorithms, mathematical formulations, and software components in Department 16 have been rigorously audited for commercial intellectual property safety.

---

## 2. License Inventory

| Module / Component | License | Commercial Permitted | Usage in Department 16 |
| :--- | :---: | :---: | :--- |
| **ACES (AMPAS / SMPTE)** | Permissive Open Standard | **YES** | Core color science and chromaticity matrices |
| **OpenColorIO (ASWF)** | BSD-3-Clause | **YES** | Configuration schema and color space conventions |
| **NumPy & SciPy** | BSD-3-Clause | **YES** | In-process vectorized array operations |
| **OpenCV (cv2)** | Apache-2.0 | **YES** | Bilateral filter, CLAHE, Inpainting, Optical Flow |
| **Real-ESRGAN (x4plus & anime)** | BSD-3-Clause | **YES** | Neural super-resolution and line-art upscaling |
| **RIFE v4.6** | MIT | **YES** | Video frame interpolation |
| **YADIF Deinterlacer** | LGPL-2.1+ | **YES** | Subprocess / in-process filter |
| **Pillow (PIL)** | HPND | **YES** | Image I/O and buffer conversion |

---

## 3. Strict Prohibitions

1. **No CC-BY-NC Models:** Research models restricted to non-commercial use (e.g. VRT, RVRT) are strictly banned from the studio runtime.
2. **No Untrusted Plugins:** External executable LUT plugins or closed binary dynamic libraries are blocked. Only standard `.cube` text formats and verified Python modules are executed.
