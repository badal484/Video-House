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

---

## ADR-014: Multimodal Perceptual Tier: Local Deterministic DSP + Cloud Foundation Reasoning

### Status
Accepted & Implemented (Part 03)

### Context & Problem Statement
Video understanding requires both low-level physical precision (exact integer frame cut boundaries, audio transients, optical flow vectors) and high-level conceptual reasoning (narrative intent, emotional tone, editorial critique). Relying solely on cloud LLMs leads to imprecise timecodes and excessive API costs; relying solely on classical CV lacks high-level understanding.

### Decision Outcome
Chosen option: **Hybrid Perceptual Tier**.
- Local Machine Engine (`departments/04_media_intelligence`): PySceneDetect cuts, Farneback optical flow, SciPy onset envelopes, and faster-whisper CTranslate2 int8 run 100% on Apple M4 CPU at zero API cost.
- Cloud Foundation Engine (`departments/05_multimodal_providers`): Google Gemini 2.0 Flash and TwelveLabs Pegasus provide deep narrative synthesis and video embeddings via typed provider adapters with offline simulation fallbacks.

---

## ADR-015: Dual-Engine Cut Detection via PySceneDetect & Color Histogram Fallback

### Status
Accepted & Implemented (Part 03)

### Context & Problem Statement
Video cuts must be identified down to the integer frame without failing when external binary dependencies or dynamic libraries encounter environment conflicts.

### Decision Outcome
Chosen option: **Dual-Engine Shot Detection (`ShotDetectionService`)**.
- Primary: PySceneDetect `AdaptiveDetector(adaptive_threshold=3.0, min_scene_len=15)`.
- Secondary Fallback: OpenCV HSV 32-bin 3-channel color histogram correlation drop ($\rho < 0.70$).
- Guarantees zero unhandled exceptions and exact frame timecodes.

---

## ADR-016: Cinematographic Motion Analysis via Farneback Flow & Affine Decomposition

### Status
Accepted & Implemented (Part 03)

### Context & Problem Statement
Understanding whether a camera is stationary, panning, tilting, zooming, or shaking is vital for matching B-roll cuts and reproducing reference cinematography.

### Decision Outcome
Chosen option: **Farneback Dense Flow with Statistical Moments and Radial Divergence**.
- Classifies camera motion into `STATIC`, `PAN_LEFT`, `PAN_RIGHT`, `TILT_UP`, `TILT_DOWN`, `ZOOM_IN`, `ZOOM_OUT`, `HANDHELD_JITTER`, and `TRACKING`.
- Runs on 480p downsampled frames at <0.2s per second of video on Apple M4 CPU.

---

## ADR-017: Rhythmic Audio Intelligence & Beat Grid Generation via SciPy

### Status
Accepted & Implemented (Part 03)

### Context & Problem Statement
Editorial cuts must snap cleanly to music beats and pause during silence.

### Decision Outcome
Chosen option: **Windowed RMS Energy Profiling & Onset Autocorrelation (`AudioIntelligenceService`)**.
- Energy: 50ms window with 50% overlap; $<-45\text{ dBFS}$ classified as `SILENCE`.
- Tempo & Rhythm: Spectral flux envelope autocorrelation picking peaks in the 60-180 BPM range, emitting deterministic beat grid timestamps.

---

## ADR-018: Reference Video Deconstruction into Mathematical Style Profiles

### Status
Accepted & Implemented (Part 03)

### Context & Problem Statement
Users want their videos edited in the style of existing reference content without vague textual descriptions.

### Decision Outcome
Chosen option: **Structured Style Deconstruction (`ReferenceAnalysisService`)**.
- Extracts Average Shot Length (ASL), Cuts Per Minute (CPM), and Pacing Dynamic (`FAST_PACED`, `DYNAMIC`, `CALM_CONTEMPLATIVE`).
- Clusters video pixel samples via OpenCV K-Means into a dominant 5-color hex palette.
- Measures camera motion distribution and computes multi-video compatibility scores with actionable editorial recommendations.

---

## ADR-019: Structured Creative Brief Parsing with Explicit Assumption Inferences

### Status
Accepted & Implemented (Part 04)

### Context & Problem Statement
User creative briefs range from single vague sentences to dense creative scripts. A production studio cannot execute undefined specifications without assuming reasonable creative baselines (aspect ratio, duration, platform) while logging assumptions transparently.

### Decision Outcome
Chosen option: **Deterministic Schema Normalization & Clarification Triggers (`CreativeBriefService`)**.
- Defaults ambiguous target duration to 30.0s, aspect ratio to 16:9 (or 9:16 for vertical platforms), and production type to `COMMERCIAL`.
- Every inference is explicitly recorded in `CreativeBrief.assumptions`.
- When prompts lack key narrative specifics or contain fewer than 10 words, targeted clarification questions are surfaced before committing generation resources.

---

## ADR-020: Algorithmic Word-per-Minute & Pause-Model Speech Duration Heuristics

### Status
Accepted & Implemented (Part 04)

### Context & Problem Statement
A major defect in generative AI video is dialogue that overflows allocated scene/shot boundaries or causes unnatural cadence when dubbed.

### Decision Outcome
Chosen option: **Algorithmic WPM + Punctuation Pause Model (`ScriptAndNarrativeService`)**.
- Standard narration speed set to 140 WPM (~2.33 words/second).
- Micro-pauses modeled algorithmically: $+0.25$s per comma/semicolon, $+0.45$s per period/exclamation/question mark.
- Total spoken duration is validated against scene durations during screenplay generation.

---

## ADR-021: Mode B Reference Style Alignment and Coverage Gap Remediations

### Status
Accepted & Implemented (Part 04)

### Context & Problem Statement
In Mode B (editing footage with references), naive AI tools hallucinate non-existent timecodes or generate mismatched cuts.

### Decision Outcome
Chosen option: **Deterministic Mapping against Part 03 Shot Boundaries (`EditingBlueprintService`)**.
- Ingests verified shot timestamps from `db.get_shots(asset_id)`.
- Maps source in/out intervals to the timeline sequence within the reference ASL window ($1.2 \times \text{ASL}$).
- Flags coverage deficits as `MissingCoverageItem` entries with recommended remediations (AI B-Roll, stock footage, motion graphics).

---

## ADR-022: Multi-Entity World Continuity Auditing

### Status
Accepted & Implemented (Part 04)

### Context & Problem Statement
Generative image and video models suffer from appearance drift, wardrobe changes, and 180-degree axis crossing across sequential cuts.

### Decision Outcome
Chosen option: **Entity Continuity Registry & Rule Auditor (`WorldContinuityService`)**.
- Dedicated SQLite tables for `characters`, `environments`, and `continuity_rules`.
- Automated pre-generation audit inspecting `PlannedShot` descriptions and requirements against active rules, flagging missing wardrobe constraints, lighting mismatches, and axis crossing.

---

## ADR-023: Mandatory Human Approval Gates for Production Blueprint Readiness

### Status
Accepted & Implemented (Part 04)

### Context & Problem Statement
Autonomous AI agents can rapidly burn API budgets and generate unaligned content without human oversight.

### Decision Outcome
Chosen option: **Approval Gatekeeper (`ProductionBlueprintManager`)**.
- A `ProductionBlueprint` maintains `is_ready_for_production = False` by default.
- Transitions to `True` only when required milestones (`SCRIPT`, `STORYBOARD`, `BUDGET`) receive explicit `ApprovalStatus.APPROVED` from a human reviewer and no unaddressed rejections remain.
