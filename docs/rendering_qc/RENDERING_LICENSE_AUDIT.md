# Rendering and Quality Control License Audit & Governance

## 1. Compliance Audit Overview
In accordance with Studio Prime Directive #6, all codecs, muxers, demuxers, libraries, and binaries utilized in Department 18 (`quality_control`) and Department 19 (`rendering_delivery`) must be rigorously audited for commercial deployment safety.

## 2. Dependency License Audit Matrix

| Library / Tool | Stated License | Commercial Distribution Status | Guardrails & Operational Constraints |
| :--- | :--- | :--- | :--- |
| **FFmpeg (Core Libraries)** | LGPL-2.1+ (Default build) | **Permitted** | Core pipeline builds without `--enable-gpl` or `--enable-nonfree` to maintain clean LGPL compliance. |
| **x264 (Software H.264)** | GPL-2.0 / Commercial | **Isolated** | Invoked strictly via external subprocess boundary or substituted with Apple VideoToolbox / Cisco OpenH264. |
| **x265 (Software HEVC)** | GPL-2.0 / Commercial | **Isolated** | Substituted with Apple `hevc_videotoolbox` hardware encoder on Apple Silicon. |
| **SVT-AV1 (libsvtav1)** | BSD-2-Clause-Patent | **Permitted** | Highly efficient, commercially clean open-source AV1 encoder. |
| **MediaInfo / libmediainfo** | BSD-2-Clause | **Permitted** | Completely safe for in-process or CLI metadata parsing. |
| **Netflix VMAF** | BSD-2-Clause-Patent | **Permitted** | Clean permissive license for reference-based perceptual quality scoring. |
| **OpenTimelineIO** | Apache 2.0 | **Permitted** | ASWF industry standard for editorial timeline representation. |
| **pysubs2** | BSD-3-Clause | **Permitted** | Permissive subtitle parsing and generation library. |
| **Python Pillow (PIL)** | HPND | **Permitted** | Permissive imaging library for thumbnails and poster frames. |
| **OpenCV (cv2)** | Apache 2.0 | **Permitted** | Permissive computer vision library for pixel-level frame analysis. |

## 3. Patent & Commercial Indemnification Considerations
- **H.264 / HEVC Patent Pools (MPEG LA / Via Licensing):**
  - Using hardware ASICs provided by the host operating system (e.g. Apple Silicon VideoToolbox) leverages the hardware vendor's existing codec patent licenses.
  - For software encoding, AV1 (`libsvtav1`) and VP9 are open, royalty-free standards supported across modern browsers and YouTube.
- **Apple ProRes Licensing:**
  - Apple ProRes encoding on macOS via VideoToolbox is officially licensed and hardware-accelerated by Apple Silicon Media Engine.
