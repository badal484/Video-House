# Architecture Decision Records (ADRs)
**Project:** Universal AI Video Production Studio  
**Status:** Approved Architectural Baseline  
**Format:** MADR 3.0.0 (Markdown Architectural Decision Records)  
**Last Verified:** 2026-11-21  

---

## ADR-001: Selection of OpenTimelineIO as Canonical Editorial Timeline

### Context & Problem Statement
The studio requires an editorial timeline representation capable of multi-track video and audio sequencing, sub-frame or frame-accurate cuts, gap handling, transitions, and lossless export/import with commercial NLEs (Adobe Premiere Pro, Apple Final Cut Pro, DaVinci Resolve). Should the studio build a proprietary timeline schema or adopt an existing open standard?

### Decision Drivers
- Multi-track complexity and rational-time arithmetic (preventing rounding drift).
- Bi-directional interoperability with professional post-production houses.
- Active industry maintenance and open permissive licensing.

### Considered Options
1. **OpenTimelineIO (ASWF / Pixar)**
2. Custom proprietary JSON timeline schema
3. CMX 3600 EDL (Edit Decision List)
4. FCPXML / Final Cut Pro XML standard

### Decision Outcome
Chosen option: **OpenTimelineIO (ASWF)**.
- **Justification:** OTIO is backed by the Academy Software Foundation and Pixar, carries a permissive Apache 2.0 license, features robust C++ and Python implementations, natively implements rational-time math, and provides built-in bidirectional adapters for FCPXML, Premiere XML, AAF, and EDL.
- **Consequences:** All editorial actions (append, split, transition, slip, slide) are expressed as OTIO mutations.

---

## ADR-002: Dual-Layer Orchestration (LangGraph + Temporal.io)

### Context & Problem Statement
AI video generation, 3D rendering, and video processing require both creative cognitive reasoning (probabilistic, cyclical, LLM-driven) and heavy long-running compute execution (deterministic, multi-hour, network-intensive). Relying on an LLM agent framework to keep open network sockets during a 45-minute render leads to timeout crashes and lost state.

### Decision Drivers
- State durability against server reboots and worker drops.
- Support for complex cyclical creative agent loops (storyboard drafting, critique, human review).
- Separation of concerns between cognitive planning and compute task dispatch.

### Considered Options
1. **Dual-Layer Architecture:** LangGraph for cognitive state graph + Temporal.io for durable workflow execution.
2. Monolithic LangGraph execution (running all render activities inside LangGraph tool calls).
3. Celery / Redis task queue without workflow orchestration.
4. AutoGen conversational agents.

### Decision Outcome
Chosen option: **Dual-Layer Architecture (LangGraph + Temporal.io)**.
- **Justification:** LangGraph manages the stateful decision graph and human review approvals. When a render or generation job is confirmed, LangGraph creates a `JobTicket` and dispatches it to Temporal. Temporal guarantees activity execution, automatic retries with exponential backoff, worker heartbeats, and complete resumption upon infrastructure failure.
- **Consequences:** Requires running Temporal Server in production.

---

## ADR-003: Subprocess Isolation for GPL v3 Dependencies (Blender)

### Context & Problem Statement
Blender 4.x is the premier open-source 3D and 2D Grease Pencil animation engine, but it is licensed under **GNU General Public License v3.0 (GPL v3)**. Linking Blender's C/Python internal modules (`bpy`) directly into the core studio application runtime could trigger copyleft obligations on proprietary studio intellectual property.

### Decision Drivers
- Complete protection of studio proprietary IP and licensing freedom.
- Headless automated rendering capability.

### Decision Outcome
Chosen option: **Subprocess Execution with Open Data Interchanges**.
- **Justification:** The studio application communicates with Blender exclusively through standard command-line subprocess invocation (`blender -b -P script.py -- args`) and standardized file interfaces (OpenUSD, OpenEXR, PNG). Under copyright law, process isolation with standardized format exchanges prevents GPL copyleft contagion across application boundaries.
- **Consequences:** All Blender automation scripts are maintained in a dedicated headless script directory (`departments/11_animation_3d/blender_scripts/`).

---

## ADR-004: Quad-Representation Architecture (OTIO, USD, VFX Nodes, Vector AST)

### Context & Problem Statement
Previous monolithic video tools forced all 3D scene data, compositor layers, and vector motion graphics into an editorial timeline, leading to brittle, unmaintainable schemas.

### Decision Outcome
Chosen option: **Decoupled Quad-Representation**.
- Editorial Timeline: **OpenTimelineIO** (1D temporal tracks).
- 3D Virtual Worlds: **OpenUSD** (3D spatial hierarchy and skeletal rigs).
- VFX Compositing: **Directed Acyclic Node Graph** (2D pixel flow).
- Motion Graphics: **Motion Canvas AST** (Declarative TypeScript vector animations).
- **Consequences:** Each department uses the best data model for its domain. Departments hand off rendered image sequences and stems to OTIO via timecode-aligned clips.

---

## ADR-005: Multi-Model Consensus Engine for Multimodal Media Intelligence

### Context & Problem Statement
Multimodal LLMs frequently hallucinate timestamps, misidentify cut boundaries, or misinterpret acoustic events when processing raw video files. Relying on a single foundation model description introduces unacceptable errors into automated video editing.

### Decision Outcome
Chosen option: **Decoupled 4-Pipeline Analysis with Deterministic Priority Consensus**.
- Deterministic cut detection (`PySceneDetect`) always overrides LLM cut timestamps.
- Audio-specialist speech alignment (`WhisperX`) always overrides visual lip-reading for dialogue.
- Foundation vision-language models (Gemini, TwelveLabs, Qwen2.5-VL) provide semantic reasoning, shot descriptions, and narrative context anchored to verified cut boundaries.
- **Consequences:** Every observation carries an empirical confidence score, source pipeline identifier, and verifiable mathematical evidence.

---

## ADR-006: Hybrid Execution Tiering (Local Edge vs. Remote GPU vs. Cloud API)

### Context & Problem Statement
The local workstation (Apple MacBook Pro M4, 16GB RAM, 41GB disk) has high CPU/SIMD performance and hardware VideoToolbox encoding, but lacks the VRAM (16GB ceiling) and storage (41GB available) required for dense diffusion video generation (Wan2.1) and massive vision models (Qwen2.5-VL-72B).

### Decision Outcome
Chosen option: **Tiered Execution Strategy**.
- **Tier 1 (Local Workstation):** Editorial timeline operations, FFmpeg stream demux/remux/proxy encoding, lightweight faster-whisper speech transcription, Spotify Pedalboard audio DSP, Motion Canvas rendering.
- **Tier 2 (Cloud APIs):** Google Gemini 2.0/1.5 Pro (long video understanding), TwelveLabs (video semantic search), ElevenLabs (voice synthesis), Runway/Kling (hero video generation).
- **Tier 3 (Self-Hosted Remote GPU Cluster):** SAM 2.1 video segmentation, Wan2.1 video diffusion, Cycles 3D raytracing, Qwen2.5-VL private reasoning.
- **Consequences:** Strict disk space guardrails enforced locally (no large model weight downloads; aggressive proxy cache eviction).
