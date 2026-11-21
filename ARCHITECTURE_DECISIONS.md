# Architecture Decision Records (ADRs)
**Project:** Universal AI Video Production Studio  
**Status:** Approved Architectural Baseline  
**Format:** MADR 3.0.0 (Markdown Architectural Decision Records)  
**Last Verified:** 2026-11-21  

---

## ADR-001: Selection of OpenTimelineIO as Canonical Editorial Timeline

### Context & Problem Statement
The studio requires an editorial timeline representation capable of multi-track video and audio sequencing, sub-frame or frame-accurate cuts, gap handling, transitions, and lossless export/import with commercial NLEs (Adobe Premiere Pro, Apple Final Cut Pro, DaVinci Resolve). Should the studio build a proprietary timeline schema or adopt an existing open standard?

### Decision Outcome
Chosen option: **OpenTimelineIO (ASWF)**.
- **Justification:** OTIO is backed by the Academy Software Foundation and Pixar, carries a permissive Apache 2.0 license, features robust C++ and Python implementations, natively implements rational-time math, and provides built-in bidirectional adapters for FCPXML, Premiere XML, AAF, and EDL.

---

## ADR-002: Dual-Layer Orchestration (LangGraph + Temporal.io)

### Context & Problem Statement
AI video generation, 3D rendering, and video processing require both creative cognitive reasoning (probabilistic, cyclical, LLM-driven) and heavy long-running compute execution (deterministic, multi-hour, network-intensive).

### Decision Outcome
Chosen option: **Dual-Layer Architecture (LangGraph + Temporal.io)**.
- **Justification:** LangGraph manages the stateful decision graph and human review approvals. When a render or generation job is confirmed, LangGraph creates a `JobTicket` and dispatches it to Temporal.

---

## ADR-003: Subprocess Isolation for GPL v3 Dependencies (Blender)

### Context & Problem Statement
Blender 4.x is licensed under **GNU General Public License v3.0 (GPL v3)**. Linking Blender's internal modules directly into the studio application runtime could trigger copyleft obligations.

### Decision Outcome
Chosen option: **Subprocess Execution with Open Data Interchanges**.
- **Justification:** The studio communicates with Blender exclusively through standard command-line subprocess invocation (`blender -b -P script.py -- args`) and standardized file interfaces (OpenUSD, OpenEXR, PNG).

---

## ADR-004: Quad-Representation Architecture (OTIO, USD, VFX Nodes, Vector AST)

### Context & Problem Statement
Previous monolithic video tools forced all 3D scene data, compositor layers, and vector motion graphics into an editorial timeline, leading to brittle schemas.

### Decision Outcome
Chosen option: **Decoupled Quad-Representation**.
- Editorial Timeline: **OpenTimelineIO** (1D temporal tracks).
- 3D Virtual Worlds: **OpenUSD** (3D spatial hierarchy and skeletal rigs).
- VFX Compositing: **Directed Acyclic Node Graph** (2D pixel flow).
- Motion Graphics: **Motion Canvas AST** (Declarative TypeScript vector animations).

---

## ADR-005: Multi-Model Consensus Engine for Multimodal Media Intelligence

### Context & Problem Statement
Multimodal LLMs frequently hallucinate timestamps, misidentify cut boundaries, or misinterpret acoustic events when processing raw video files.

### Decision Outcome
Chosen option: **Decoupled 4-Pipeline Analysis with Deterministic Priority Consensus**.
- Deterministic cut detection (`PySceneDetect`) always overrides LLM cut timestamps.
- Audio-specialist speech alignment (`WhisperX`) always overrides visual lip-reading for dialogue.
- Foundation vision-language models (Gemini, TwelveLabs, Qwen2.5-VL) provide semantic reasoning anchored to verified cut boundaries.

---

## ADR-006: Hybrid Execution Tiering (Local Edge vs. Remote GPU vs. Cloud API)

### Context & Problem Statement
The local workstation (Apple MacBook Pro M4, 16GB RAM, 41GB disk) has high CPU/SIMD performance and hardware VideoToolbox encoding, but lacks the VRAM (16GB ceiling) and storage required for dense diffusion video generation (Wan2.1).

### Decision Outcome
Chosen option: **Tiered Execution Strategy**.
- Tier 1 (Local): Editorial, FFmpeg VideoToolbox proxy encoding, faster-whisper, Pedalboard DSP.
- Tier 2 (Cloud APIs): Gemini 2.0/1.5 Pro, TwelveLabs, ElevenLabs, Runway.
- Tier 3 (Remote GPU): SAM 2.1, Wan2.1, Cycles 3D raytracing, Qwen2.5-VL.

---

## ADR-007: SQLite as Central Asset Registry Database Engine

### Context & Problem Statement
The studio requires an embedded, fast, transactional database to track project media assets, technical stream metadata, derivative relationships, and processing jobs without forcing the user to install or run a separate database server.

### Decision Outcome
Chosen option: **SQLite 3.x in WAL Mode**.
- **Justification:** Zero external daemon dependencies; fully transactional with ACID guarantees; foreign key enforcement; fast indexed queries over SHA-256 and media types; native to Python standard library (`sqlite3`).
- **Consequences:** Ideal for local workstation and edge nodes. When scaling to multi-tenant distributed cloud deployment in Part 07, repository models map cleanly to PostgreSQL.

---

## ADR-008: Non-Blocking Asynchronous Derivative Generation

### Context & Problem Statement
Transcoding video proxies, generating contact sheets, and computing waveform peaks takes several seconds to minutes. Blocking HTTP upload requests until processing completes results in HTTP gateway timeouts and poor user experience.

### Decision Outcome
Chosen option: **Asynchronous Job Queue Handshake**.
- **Justification:** Upload/import endpoints return `202 Accepted` immediately with the `asset_id` and initial status `QUEUED`. Background workers process metadata and derivatives asynchronously with progress telemetry and retry logic.
- **Consequences:** Frontend clients poll job status or listen to WebSocket events for completion.

---

## ADR-009: Content-Based Magic Signature Inspection

### Context & Problem Statement
Relying solely on user-provided file extensions (`.mp4`, `.png`) allows malicious payloads, corrupted files, and wrong-codec files to bypass validation, crashing downstream decoders.

### Decision Outcome
Chosen option: **Deep Magic Byte & Structural Introspection**.
- **Justification:** `MediaValidator` checks verified binary signatures (`ftyp`, `EBML`, `RIFF`, `fLaC`, `PNG`, `glTF`, `BLENDER`) and structural JSON/XML contents before an asset is registered.
- **Consequences:** Extension spoofing is detected and rejected at the ingestion boundary.

---

## ADR-010: Project-Partitioned Storage & Checksum Deduplication

### Context & Problem Statement
Stitching media files into a global flat folder risks filename collisions and accidental file overwrites. Re-uploading the same 2GB video card card wastes limited local storage (~41GB available).

### Decision Outcome
Chosen option: **Project-Partitioned Directory Structure with SHA-256 Deduplication**.
- Originals are stored at `assets/{project_id}/originals/{asset_id}_{filename}`.
- If a file with an identical SHA-256 hash is already registered in the project, the system reuses the existing asset record and attaches the new role without duplicating physical disk space.
