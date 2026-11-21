# Operational Instructions for AI Agents & Developers
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Target:** AI Coding Agents, Human Engineers & Pipeline Developers  

---

## 1. Prime Directives for Operating in this Codebase

1. **Strict Architecture Boundaries:**
   - Never collapse the 22 departments into monolithic utility scripts.
   - Always route cross-department communication through typed interfaces and the Central Common Asset Registry.
   - Do not import one department's internal implementation directly into another. Use Department Interfaces (`interface.py`).
2. **Local Machine Hardware Awareness:**
   - The primary workstation is an **Apple MacBook Pro (Apple M4, 16GB RAM, ~41GB free disk)**.
   - **Never download large model weights (>2 GB)** or heavy video raw files to the local disk.
   - Guard local storage vigilantly: intermediate cache files in `temp/` must be cleaned up post-execution.
   - Heavy CUDA-dependent tasks (Wan2.1 video diffusion, SAM 2.1 4K video tracking) must be routed to remote GPU workers or cloud APIs.
3. **Runtime Isolation from Dev Tools:**
   - Antigravity and Claude Code are **development environments**, not the studio runtime engine.
   - The studio runtime runs as a standalone Python/Node/Temporal service. Do not write code that assumes or invokes Antigravity or Claude Code as an in-process dependency.
4. **Editorial Integrity:**
   - The canonical editorial timeline is **OpenTimelineIO (OTIO)**. Never invent an ad-hoc custom timeline format when OTIO represents it natively.
   - Use rational time arithmetic (`RationalTime(value, rate)`) for all cuts, durations, and transitions to eliminate floating-point drift.
   - 3D worlds belong in **OpenUSD**; VFX composites belong in **Node DAGs**; vector graphics belong in **Motion Canvas ASTs**. Do not force non-editorial data into OTIO tracks.
5. **Multi-Model Consensus & Evidence:**
   - Never trust an LLM text hallucination as the source of truth for cut boundaries or timecodes.
   - Always prioritize deterministic tools (`PySceneDetect`, `FFprobe`, `WhisperX`) for exact timecode boundaries.
6. **Commercial License Hygiene:**
   - Always verify licenses in `LICENSE_REGISTRY.csv`.
   - Never introduce AGPL-3.0 libraries or non-commercial (CC-BY-NC) models into the core runtime without explicit architectural review.

---

## 2. Directory Layout & Department Responsibilities

- `departments/01_studio_application`: FastAPI backend + Web UI streaming client.
- `departments/02_project_management`: Project state, versioning, delivery profiles.
- `departments/03_media_ingestion`: FFmpeg/FFprobe demuxing, conformance, and proxy generation.
- `departments/04_media_intelligence`: PySceneDetect, faster-whisper, Demucs, and TwelveLabs extraction.
- `departments/05_multimodal_providers`: Unified adapters for Gemini, TwelveLabs, Qwen2.5-VL.
- `departments/06_creative_direction`: Natural language brief analysis, storyboards, and scripts.
- `departments/07_production_planning`: Dependency DAG compiler and compute cost estimator.
- `departments/08_video_editing`: OpenTimelineIO multi-track editorial assembly.
- `departments/09_motion_graphics`: Motion Canvas declarative 2D kinetic typography and graphics.
- `departments/10_animation_2d`: Headless Blender Grease Pencil 3.0 anime/vector animation.
- `departments/11_animation_3d`: Headless Blender 4.x and OpenUSD scene rendering.
- `departments/12_character_production`: Character consistency, LoRA profiles, model sheets.
- `departments/13_vfx_compositing`: SAM 2.1 rotoscoping, E2FGVI inpainting, OpenColorIO ACEScg.
- `departments/14_audio_production`: Spotify Pedalboard DSP mixing, dynamic EQ, and stem balancing.
- `departments/15_ai_generation`: Multi-provider router for Runway, Kling, Wan2.1, Flux.1.
- `departments/16_color_restoration`: Real-ESRGAN upscaling, RIFE frame interpolation, LUT grading.
- `departments/17_subtitles_dubbing`: WhisperX timed subtitles and ElevenLabs/Kokoro voice dubbing.
- `departments/18_quality_control`: Automated detection of black frames, freeze frames, audio clips.
- `departments/19_rendering_delivery`: Final FFmpeg master export with EBU R128 loudness conformance.
- `departments/20_agent_orchestration`: LangGraph state machine + Temporal.io durable execution.
- `departments/21_storage_asset_management`: Common Asset Registry (SHA-256, SQLite/PostgreSQL).
- `departments/22_licensing_cost_tracking`: Real-time API cost tracking and license auditing.
