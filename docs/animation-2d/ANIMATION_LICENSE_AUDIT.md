# 2D ANIMATION & CHARACTER LICENSE AUDIT
**Department:** 10_animation_2d & 12_character_production  
**Scope:** Verification of animation software, rigging frameworks, AI models, and character assets against commercial studio licensing rules  

---

## 1. Studio License Principles

1. **Permissive Core In-Process Runtime:** All libraries linked directly into the Python process must strictly comply with Apache-2.0, MIT, BSD-2/3-Clause, or Python Software Foundation licenses.
2. **Zero In-Process AGPL-3.0:** AGPL-3.0 libraries are strictly barred from core in-process imports.
3. **Subprocess Boundary for GPL Tools:** Standalone GPL software (Blender 4.x, Krita) must operate solely as out-of-process CLI subprocesses via files, scripts, or standard I/O pipes.
4. **Proprietary Commercial Hygiene:** Commercial tools (Spine, Live2D) cannot be mandatory hard runtime dependencies. Open-source or application-owned interchange formats (Spine JSON compatible, standard SVG, PNG sequences) are used to prevent vendor lock-in.
5. **Commercially Clear Character Assets:** All reference character designs, model sheets, color palettes, and fonts must be 100% commercially unencumbered. No unauthorized trademarked character IP may be used in production training or asset stores.

---

## 2. Dependency & Framework Audit Matrix

| Library / Tool | Current Version | License Type | Compliance Status | Operational Boundary |
|---|---|---|---|---|
| **Python Pillow (PIL)** | 12.1.1 | HPND / MIT-like | **APPROVED** | In-process raster manipulation, layer blending, sprite sheets |
| **OpenCV (`opencv-python`)** | 5.0.0 | Apache 2.0 | **APPROVED** | In-process computer vision, optical flow, pose extraction, image processing |
| **NumPy** | 2.4.2 | BSD-3-Clause | **APPROVED** | High-performance matrix mathematics, bone transforms, IK solvers |
| **OpenToonz CLI (`tcomposer`)** | 1.7.x | BSD-3-Clause | **APPROVED** | Headless CLI batch rendering and exposure sheet compilation |
| **Blender (GPencil 3.0)** | 4.x / 3.x | GPL-3.0 | **APPROVED VIA SUBPROCESS** | Headless CLI script execution (`blender -b -P script.py`) |
| **OpenTimelineIO** | 0.16.0 | Apache 2.0 | **APPROVED** | Editorial timeline interchange and track conforming |
| **FFmpeg** | 8.1.2 | LGPL 2.1+ | **APPROVED** | Out-of-process subprocess video encoding (ProRes 4444, WebM) |

---

## 3. AI Model License & Provenance Audit

| Model / Architecture | Original Publisher | Original License | Studio Integration Mode | Commercial Restrictions |
|---|---|---|---|---|
| **LivePortrait** | Kuaishou / USTC | MIT (Code) | Remote GPU / Microservice | Research & Commercial under acceptable use |
| **IP-Adapter / IP-Adapter-Plus** | Tencent AI Lab | Apache 2.0 | Remote GPU worker (HTTP) | Commercial usage permitted |
| **InstantID** | InstantID Team | Apache 2.0 | Remote GPU worker (HTTP) | Commercial usage permitted |
| **ControlNet (OpenPose / Canny)** | Lvmin Zhang / Stanford | Apache 2.0 | Remote GPU worker | Commercial usage permitted |
| **RIFE (Optical Flow)** | Megvii / Community | MIT | Local Metal / Remote GPU | Commercial usage permitted |

---

## 4. Verification Sign-Off

The 2D Animation and Character Production Department adheres 100% to commercial licensing requirements. The studio runtime engine remains completely free of AGPL copyleft viral obligations and proprietary vendor lock-in.

