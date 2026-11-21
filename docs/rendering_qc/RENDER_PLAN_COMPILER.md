# Render Plan Compiler & Preflight Validator Specification

## 1. Compiler Mission & Objectives
The `RenderPlanCompiler` converts an approved high-level creative project into a validated, stage-by-stage execution graph (`RenderPlan`).
It guarantees that:
1. No rendering commences if referenced assets, fonts, LUTs, or plugins are missing.
2. Timeline and DCC dependencies are resolved into an optimal DAG (Directed Acyclic Graph).
3. Compute complexity, disk space, and estimated financial costs are calculated upfront.

## 2. Preflight Inspection Engine (`PreflightValidator`)
The preflight inspector examines the project prior to compilation:
- **Media Asset Availability:** Verifies every clip referenced in the OTIO timeline exists on disk with matching SHA-256 or valid file size. Never silently substitutes missing assets.
- **Font & Motion Graphics Check:** Verifies vector typography fonts (Inter, Montserrat, Roboto Mono) and Motion Canvas dependencies exist.
- **Color Grading & LUT Check:** Verifies 3D `.cube` LUT files and ACES configuration paths exist.
- **Model Dependencies:** Verifies required neural voice checkpoints or lip-sync provider API keys are active.
- **Licensing Compliance:** Verifies that no unapproved CC-BY-NC assets or models are included.

## 3. DAG Compilation Algorithm
The compiler decomposes the project into discrete stages:
```
[Preflight Validation] ──► [Stage 1: DCC Rendering] (Motion Canvas SVG, 3D Cycles, VFX)
                                    │
                                    ▼
                           [Stage 2: Audio Stems] (Demucs separation, DSP mixing, EBU R128)
                                    │
                                    ▼
                           [Stage 3: Timeline Intermediate] (ProRes 422 HQ rasterization)
                                    │
                                    ▼
                           [Stage 4: Encoding & Transcoding] (H.264 / HEVC / AV1 / MXF)
                                    │
                                    ▼
                           [Stage 5: Automated Quality Control] (Video, Audio, Color, Subtitles)
                                    │
                                    ▼
                           [Stage 6: Delivery Packaging] (Manifest, Checksums, Sidecars)
```

## 4. Cost & Resource Estimation
The compiler estimates:
- **Estimated Render Time:** Modeled from timeline duration, resolution, frame rate, and filter complexity.
- **Estimated Disk Space:** Calculated from target bitrate $\times$ duration plus intermediate buffer requirements.
- **Estimated Financial Cost:** If remote cloud workers are required, cost is calculated against worker hourly rates. Any job exceeding $\$1.00$ triggers a mandatory `HumanApprovalGate`.

