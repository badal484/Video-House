# PART 07 — EXISTING SYSTEM AUDIT & VFX CAPABILITIES
**Department:** 13_vfx_compositing (VFX & Compositing Studio)  
**Date:** 2026-11-21  
**Status:** Approved Architecture Audit  

---

## 1. Executive Summary

This audit assesses the state of the Universal AI Video Production Studio across Departments 01–12, 14–22 prior to building Department 13 (`13_vfx_compositing`). The studio requires an extensible, professional-grade visual effects and node-based compositing system capable of processing live-action footage, AI-generated clips, 2D vector elements, 3D render passes, and mixed-media timelines.

---

## 2. Component Audit Across Studio Departments

| Department / Layer | Existing Capability | Integration Point for Department 13 |
|---|---|---|
| **01_studio_application** | FastAPI backend, streaming SSE/WebSocket, REST API | Endpoints for compositing graph creation, task execution, tracking solves, and interactive preview renders |
| **02_project_management** | Project state, versioning, delivery profiles | Scoped `vfx_projects` and `vfx_shot_tasks` records linked to parent projects |
| **03_media_ingestion** | FFmpeg/FFprobe demuxing, format normalization, proxy generation | Ingesting raw plates, green screen footages, reference stills, and background plates |
| **04_media_intelligence** | PySceneDetect shot boundaries, faster-whisper, TwelveLabs extraction | Shot boundary timecodes, motion vectors, and detected objects (`detected_objects`, `camera_movements`) |
| **05_multimodal_providers** | Unified adapters (Gemini, TwelveLabs, Qwen2.5-VL) | Vision-language reasoning for visual defect identification, style matching, and plate analysis |
| **06_creative_direction** | AI Director, production blueprints, `planned_shots` with `vfx_notes` | Translating director `vfx_notes` and shot blueprints into concrete node compositing graphs |
| **07_production_planning** | Dependency DAG compiler and compute cost estimator | Scheduling CPU-local vs remote GPU compositing passes and estimating frame render time |
| **08_video_editing** | OpenTimelineIO multi-track NLE, clip trimming, transitions, conform | Replacing offline edit clips with VFX composite renders on track `V1` or layering overlays on `V2` |
| **09_motion_graphics** | Motion Canvas 2D procedural rendering, alpha transparency PNG/ProRes 4444 | Seamlessly injecting motion graphics renders into compositing nodes as overlay or foreground elements |
| **11_animation_3d** | Headless Blender 4.x, OpenUSD scene graph | Multi-pass OpenEXR AOVs (Beauty, Cryptomatte, Depth, Normal, Shadow, Emission) |
| **18_quality_control** | Black frame, freeze frame, audio clipping checks | Matte holes, edge halo artifacts, spill leakage, tracking jitter detection |
| **21_storage_asset_management** | SQLite/PostgreSQL transactional asset registry, SHA-256 deduplication | Storing composite render outputs, alpha matte caches, and tracking keyframe data |
| **22_licensing_cost_tracking** | License registry and per-shot compute cost tracking | Commercial license enforcement and GPU/API expenditure auditing |

---

## 3. Local Hardware & Execution Realities

The studio's workstation operates on:
- **Architecture:** Apple Silicon M4 (16GB RAM, ~41GB free disk space).
- **Installed CV Tooling:** OpenCV 5.0.0 (`cv2`), NumPy 2.4.2, Pillow 12.1.1, FFmpeg 8.1.2 with Apple VideoToolbox (`h264_videotoolbox`, `hevc_videotoolbox`, `prores_videotoolbox`).
- **Heavy Model Isolation:** Large models (>2GB) like Wan2.1 or full SAM 2.1 video checkpoints are never held permanently on the local flash drive. The engine provides lightweight, deterministic local implementations (Lucas-Kanade optical flow, 4-point homography, GrabCut/threshold keying, Telea/Navier-Stokes inpainting, CPU composite rasterizer) and dispatches heavy AI passes to remote GPU workers or headless containers via JSON job manifests.

---

## 4. Key Architectural Conclusions

1. **Node Graph Representation:** OpenTimelineIO is an editorial container, not a 2D compositing DAG. Compositing must be modeled as an explicit Directed Acyclic Graph (DAG) with typed nodes, input/output sockets, and execution dependencies.
2. **Deterministic Local Fallback:** All core VFX operations (keying, despill, 4-point planar track, object removal, atmospheric glow, camera shake, alpha compositing) must function deterministically on the local machine without requiring cloud connectivity.
3. **OpenEXR & Color Space Conformance:** Compositing calculations must occur in linear color space (linear Rec.709 / ACEScg) with explicit support for straight vs premultiplied alpha channels.

