# Rendering & Quality Control Known Limitations & Roadmap

## 1. Known Architectural Limitations
1. **Local Apple Silicon Cloud Worker Simulation:**
   - On a standalone Apple Silicon workstation, distributed cloud worker dispatch operates via local asynchronous mock workers or remote API connections. Physical render farm clusters require dedicated network storage (NFS / S3).
2. **Real-Time 8K HDR VMAF Compute Cost:**
   - Full-reference VMAF scoring on 8K 60fps HDR content requires substantial compute time (~3–4x real-time). The system defaults to fast mathematical PSNR/SSIM and statistical defect detection for high-resolution interactive previews.
3. **Hardware Codec Availability:**
   - Apple VideoToolbox does not hardware-encode AV1 on M4 (AV1 hardware decode only; encode uses multithreaded SVT-AV1 CPU).

## 2. Strategic Post-v1.0 Roadmap
- Hardware-accelerated AV1 encoding on future Apple Silicon generations.
- Direct IMF SMPTE CPL/PKL XML packaging export with MXF OP-Atom essence wrapping.
- Web-based real-time frame scrubber for QC defect visual inspection in the Studio UI.

