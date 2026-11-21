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

---

## ADR-024: Immutable Rational Time Arithmetic (`RationalTime`)

### Status
Accepted & Implemented (Part 05)

### Context & Problem Statement
Floating-point time values accumulate rounding errors across multi-track edits, mixed frame rates (23.976 vs 24 vs 29.97 fps), and audio sample rates (48 kHz). Over long sequences, cuts drift out of synchronization with audio by multiple frames.

### Decision Outcome
Chosen option: **Immutable Integer Ratio Representation (`core/timeline/time_model.py`)**.
- All temporal values (in-points, out-points, durations, offsets) are represented strictly as `RationalTime(value: int, rate: float)`.
- Implements exact dunder arithmetic (`+`, `-`, `*`, `/`) with automatic rate rescaling.
- Converts bidirectionally to standard SMPTE 12M timecode (`HH:MM:SS:FF`) for non-drop-frame and drop-frame media.

---

## ADR-025: OpenTimelineIO (ASWF) as Primary Editorial Interchange Standard

### Status
Accepted & Implemented (Part 05)

### Context & Problem Statement
The studio must interchange timelines with industry-standard commercial NLEs (Adobe Premiere Pro, Apple Final Cut Pro, DaVinci Resolve) without loss of multi-track clip positions, gaps, or transitions.

### Decision Outcome
Chosen option: **OpenTimelineIO 0.18.1 (`core/timeline/otio_adapter.py`)**.
- Direct bidirectional serialization between Studio `Timeline` models and `.otio` files.
- Empty time ranges between non-contiguous clips are preserved explicitly as `otio.schema.Gap` instances.
- Commercial NLE adapters (`fcpxml`, `xml`, `edl`, `aaf`) operate out-of-the-box over exported `.otio` documents.

---

## ADR-026: Dynamic FFmpeg Complex Filtergraph Compilation for Deterministic Rendering

### Status
Accepted & Implemented (Part 05)

### Context & Problem Statement
Concatenating pre-rendered intermediate video clips degrades generation quality, consumes excessive local SSD storage on the Apple M4 workstation, and cannot represent layered compositing or crossfades.

### Decision Outcome
Chosen option: **Single-Pass `-filter_complex` DAG Compilation (`departments/08_video_editing/render_engine.py`)**.
- The engine compiles the multi-track timeline DAG directly into an FFmpeg complex filter string containing `trim`, `setpts`, `scale`, `pad`, `xfade`, `overlay`, `atrim`, `volume`, and `amix`.
- Zero intermediate generation loss; renders directly from source/proxy files to the master container.
- Real-time progress monitoring via `-progress pipe:1` with cancellation support.

---

## ADR-027: Five-Mode Continuous Keyframe Curve Interpolation

### Status
Accepted & Implemented (Part 05)

### Context & Problem Statement
Visual and audio effects (opacity fades, position pans, zooms, volume automation) require smooth, continuous parameter curves between arbitrary keyframe points.

### Decision Outcome
Chosen option: **Hermite / Cubic / Ease Keyframe Engine (`core/timeline/keyframe_engine.py`)**.
- Supports 5 canonical easing modes: `HOLD`, `LINEAR`, `EASE_IN` ($\tau^2$), `EASE_OUT` ($1 - (1-\tau)^2$), and `EASE_IN_OUT` ($3\tau^2 - 2\tau^3$ smoothstep).
- Evaluates parameter values at arbitrary rational time offsets with boundary clamping.

---

## ADR-028: Transactional Snapshot Undo/Redo Architecture for Editorial State

### Status
Accepted & Implemented (Part 05)

### Context & Problem Statement
Interactive and automated video editing operations (split, roll edit, ripple delete) modify multiple track and clip records simultaneously. Failure midway leaves the timeline corrupted.

### Decision Outcome
Chosen option: **Immutable State Snapshots & ACID SQLite Persistence (`TimelineManager`)**.
- Before applying any mutating edit operation, `TimelineManager` serializes the current timeline state onto an in-memory undo stack.
- Changes are committed transactionally to the SQLite `timelines`, `tracks`, and `clips` tables.
- Enables multi-level non-destructive undo and redo across all editorial actions.

---

## ADR-029: Dual-Engine Routing (Procedural Vector SVG + Canvas2D Raster) for Motion Graphics

### Status
Accepted & Implemented (Part 06)

### Context & Problem Statement
Heavy headless browser frameworks (Chromium/Playwright/Remotion) consume 400MB–1.4GB RAM and introduce 8–18s cold-start latencies per 10s composition. Conversely, naive raster drawing cannot produce scalable vector definitions for interchange.

### Decision Outcome
Chosen option: **Dual-Engine Routing (`MotionRendererRouter`)**.
- Clean text, titles, lower-thirds, and data charts default to `SVGVectorRenderer`, generating crisp, resolution-independent SVG XML per frame.
- High-density raster effects, particle streaks, and video overlays stream via `CanvasRasterRenderer` using Pillow and FFmpeg `image2pipe`.
- Headless web rendering (HyperFrames) is retained strictly as an optional adapter.

---

## ADR-030: Unicode Annex #29 Grapheme Cluster Tokenization for Indic/Devanagari Script Shaping

### Status
Accepted & Implemented (Part 06)

### Context & Problem Statement
Standard string slicing (`text[:k]`) breaks complex scripts such as Hindi/Devanagari, splitting consonants from dependent viramas and matras (e.g. producing detached `्` or `े` instead of bonded conjuncts like `स्ते`).

### Decision Outcome
Chosen option: **Orthographic Syllable / Grapheme Cluster Tokenizer (`TypographyEngine`)**.
- Inspects Unicode categories (`Mn`, `Mc`) and virama (`U+094D`).
- Bonds base consonants, viramas, following consonants, and vowel matras into single indivisible syllables for kinetic typewriter and character reveals.

---

## ADR-031: SIL OFL 1.1 Commercial Typography Hygiene and Exclusion of Proprietary Font Runtimes

### Status
Accepted & Implemented (Part 06)

### Context & Problem Statement
Broadcasting video content constitutes commercial publication. Standard desktop font licenses (EULAs) prohibit embedding glyphs into broadcast video without enterprise extensions.

### Decision Outcome
Chosen option: **Standardization on Permissive Open Fonts (SIL OFL 1.1 & Apache 2.0)**.
- Bundled and verified font families: Inter, Montserrat, Roboto Mono, Playfair Display, Noto Sans Devanagari.
- Zero commercial royalty obligations or broadcast licensing restrictions.

---

## ADR-032: Direct NLE Track V3 Placement via ProRes 4444 Transparent Media

### Status
Accepted & Implemented (Part 06)

### Context & Problem Statement
Motion graphics must integrate into the Part 05 Non-Linear Editing Engine without requiring flattened video re-renders or losing alpha transparency.

### Decision Outcome
Chosen option: **Transparent Video Conformance & Timeline Insertion (`TimelineMotionAdapter`)**.
- Compositions compile into Apple ProRes 4444 (`-c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le`) or transparent WebM (`-c:v libvpx-vp9 -pix_fmt yuva420p`).
- Output files are registered in the Central Asset Registry and inserted onto video track `V3` of the destination timeline as standard `Clip` records.

---

## ADR-033: Automated Layout Aspect Ratio Adaptation (16:9, 9:16, 1:1)

### Status
Accepted & Implemented (Part 06)

### Context & Problem Statement
Repurposing landscape video graphics for vertical mobile feeds (9:16) often causes clipped lower-thirds, unreadable text, or awkward horizontal stretching.

### Decision Outcome
Chosen option: **Semantic Coordinate Re-anchoring (`DesignValidator.adapt_aspect_ratio`)**.
- Re-scales coordinates proportionally.
- Intelligently detects vertical aspect ratios ($H > W$), automatically enlarges typography for mobile viewing, and re-centers lower thirds to prevent collision with mobile app UI buttons.

---

## ADR-034: Directed Acyclic Graph (DAG) for Node-Based Compositing

### Status
Accepted & Implemented (Part 07)

### Context & Problem Statement
OpenTimelineIO and NLE timeline tracks are designed for sequential horizontal editorial cuts, not for complex multi-branch 2D pixel transformations, planar tracking corner pins, and matte extractions.

### Decision Outcome
Chosen option: **Explicit Directed Acyclic Graph (DAG) Compositing Schema (`CompositingGraph`)**.
- Nodes possess typed input/output sockets (`IMAGE_RGBA`, `IMAGE_RGB`, `MASK_ALPHA`, `TRANSFORM_MATRIX`, `TRACK_DATA`).
- Cycle detection enforces acyclic topology, executed strictly in topological sort order via Kahn's algorithm.

---

## ADR-035: Dual-Engine Compositing Architecture (LocalCompositorEngine + BlenderCompositorEngine)

### Status
Accepted & Implemented (Part 07)

### Context & Problem Statement
Local Apple Silicon M4 hardware constraints require instant, zero-network, sub-millisecond 2D compositing without heavy 3D rendering overhead, while preserving future headless 3D OpenUSD/Cycles multi-pass rendering.

### Decision Outcome
Chosen option: **Hybrid Dual-Engine Architecture with Dynamic Router (`VFXEngineRouter`)**.
- `LocalCompositorEngine`: Pure Python + NumPy + OpenCV 5.0 for deterministic local execution of chroma keying, planar perspective warping, inpainting, and alpha merges.
- `BlenderCompositorEngine`: Standalone Python script generator for headless Blender compositor node trees and multi-pass OpenEXR compositing.

---

## ADR-036: Premultiplied Alpha Math & Linear Color Space Conformance

### Status
Accepted & Implemented (Part 07)

### Context & Problem Statement
Evaluating blurs, glows, and alpha merges in gamma-encoded sRGB produces dark fringing, muddy edges, and unphysical light summation.

### Decision Outcome
Chosen option: **Linear Radiance Space Processing with Premultiplied Alpha Blending**.
- All merge operations evaluate $C_{out} = C_{fg} + C_{bg} \times (1.0 - \alpha_{fg})$ in premultiplied linear float32 space before converting back to sRGB.
- Built-in color difference despill suppresses green/blue edge reflection on foreground subjects.

---

## ADR-037: Application-Owned Canonical 2D Animation Project Model

### Status
Accepted & Implemented (Part 08)

### Context & Problem Statement
Proprietary 2D animation tools (Live2D, Spine, Rive) introduce vendor lock-in and non-permissive runtime licenses, while simple video renders eliminate the ability to edit timing or swap character parts.

### Decision Outcome
Chosen option: **Engine-Agnostic Canonical Animation Project Schema (`AnimationProject`)**.
- Application-owned models for projects, scenes, shots, tracks, drawing exposures, keyframes, cameras, and character instances.
- Stepped exposure holds on 1s (24 fps), 2s (12 fps), and 3s (8 fps) preserve authentic animation cadence.

---

## ADR-038: Quantitative Multi-Vector Character Identity Verification

### Status
Accepted & Implemented (Part 08)

### Context & Problem Statement
Diffusion and generative AI models frequently suffer from character drift (altering face shapes, eye colors, hair volume, and costume details across seeds).

### Decision Outcome
Chosen option: **Quantitative Character DNA & Multi-Vector Validation (`IdentityValidator`)**.
- Enforces strict anatomical proportion tolerance ($\Delta_{prop} \le 5\%$) and CIE Lab color distance ($\Delta E \le 8.0$).
- Automatically discards drifting candidate frames before committing to the studio asset store.

---

## ADR-039: Authentic Japanese Anime Pipeline Standards (Settei, Genga, Doga, Shiage)

### Status
Accepted & Implemented (Part 08)

### Context & Problem Statement
Treating anime as a generic image filter produces unconvincing results without the disciplined cadence, clean line cleanup, and multiplane depth characteristic of professional anime studios.

### Decision Outcome
Chosen option: **Dedicated Anime Production Subsystems (`AnimeCelShader`, `MultiplaneBackgroundEngine`)**.
- 5-angle Settei turnaround model sheets with horizontal guide alignments.
- 3-tier cel shading (flat base, core shadow, specular rim highlight) with directional lighting.
- Multiplane parallax backgrounds with depth-scaled camera scrolling velocities ($V = V_{cam} / (1 + Z)$).

---

## ADR-040: In-Process C++ DSP Acceleration via Spotify Pedalboard with SciPy Fallback

### Status
Accepted & Implemented (Part 10)

### Context & Problem Statement
Audio processing via CLI subprocess wrappers (e.g. repeated FFmpeg invocations per clip) introduces significant process spawn overhead and file I/O bottlenecks. Conversely, launching external DAW GUI applications prevents headless automation.

### Decision Outcome
Chosen option: **In-Memory C++ JUCE DSP Processing via Spotify Pedalboard & SciPy Fallbacks**.
- Native Apple Silicon M4 ARM64 execution with sub-millisecond per-block latency.
- Full studio-grade parametric EQ, dynamic compression, brickwall limiting, algorithmic reverb, and VST3/AU hosting directly in Python.
- 100% pure NumPy/SciPy fallback topologies ensure zero platform lock-in.

---

## ADR-041: Strict ITU-R BS.1770-4 / EBU R128 Gated Loudness Normalization

### Status
Accepted & Implemented (Part 10)

### Context & Problem Statement
Un-normalized audio causes jarring volume fluctuations across scenes and triggers aggressive, unpredictable platform compression on YouTube, Spotify, and broadcast networks.

### Decision Outcome
Chosen option: **Standardized Gated Integrated Loudness (LUFS) & 4x Oversampled True Peak Metering**.
- Target profiles: YouTube (-14.0 LUFS, -1.0 dBTP), Apple Podcasts (-16.0 LUFS, -1.0 dBTP), EBU R128 (-23.0 LUFS, -1.0 dBTP).
- 2-pass normalization eliminates digital inter-sample clipping on consumer DACs without sacrificing dynamic range.

---

## ADR-042: Automated Dialogue-Driven Sidechain Ducking & Procedural Foley Synthesis

### Status
Accepted & Implemented (Part 10)

### Context & Problem Statement
Background music and sound effects frequently mask dialogue intelligibility. Furthermore, external royalty-free sound libraries introduce storage overhead and potential licensing copyright claims.

### Decision Outcome
Chosen option: **Automatic Sidechain Ducking & Deterministic Procedural SFX Synthesis**.
- Sidechain ducking dynamically reduces background music gain (by -14 dB) with 120ms attack and 750ms release during speech activity.
- Pure procedural synthesis generates sub-bass impacts, swept whooshes, tension risers, and ambient drones purely from mathematical equations, providing 100% royalty-free commercial safety.

---

## ADR-043: Provider-Independent Capability-Based Generative Model Orchestration

### Status
Accepted & Implemented (Part 11)

### Context & Problem Statement
The generative AI landscape is evolving rapidly. Hardcoding vendor-specific APIs (Runway, Kling, Midjourney, ElevenLabs) throughout the application creates tight vendor lock-in, breaks when APIs deprecate parameters, and prevents seamless fallback to open-weight models (Wan2.1, FLUX.1, Kokoro-82M).

### Decision Outcome
Chosen option: **Decoupled Capability-Based Adapter & Registry Architecture (`BaseGenerationProvider`, `GenerationRouter`, `ProviderRegistry`)**.
- Generation requests specify capabilities (`modality`, `min_resolution`, `aspect_ratio`, `target_fps`, `max_cost`) rather than specific vendors.
- The `GenerationRouter` dynamically selects the best available registered model based on project budget and technical constraints.
- Local mock adapters ensure deterministic, zero-cost unit testing and CI/CD execution without external API dependencies.

---

## ADR-044: Structured Multi-Dimensional Prompt Compilation vs Raw Plain-Text Prompts

### Status
Accepted & Implemented (Part 11)

### Context & Problem Statement
Different generative models demand fundamentally different prompt syntax for optimal quality. Runway Gen-3 Alpha responds best to bracketed camera directives (`[Camera: pan right]`), Kling 1.5 requires anatomical physics descriptors, while FLUX.1 generates superior results from descriptive prose paragraphs without keyword tagging.

### Decision Outcome
Chosen option: **Multi-Dimensional Prompt Compiler (`PromptCompiler`)**.
- Creative agents emit structured prompt dimensions (`StructuredPromptDimensions`: subject, action, environment, camera, lighting, mood, style, technical specs).
- Dedicated compiler targets translate these dimensions deterministically into model-specific syntax (Runway, Kling, FLUX, Midjourney, AudioCraft).
- Negative prompts and character-consistency triggers are automatically appended based on bound reference profiles.

---

## ADR-045: Multi-Tier Budget Firewalls & Human-in-the-Loop Approval Gates for Paid APIs

### Status
Accepted & Implemented (Part 11)

### Context & Problem Statement
Autonomous AI creative agents operating in iterative loops can inadvertently exhaust project budgets by submitting repeated, unconstrained paid API calls (e.g. 4K high-tier video generation at $0.50-$2.00 per attempt).

### Decision Outcome
Chosen option: **Multi-Tier Financial Firewall & Cryptographic Idempotency (`GenerationBudgetManager`, `ApprovalGateManager`, `GenerationJobQueue`)**.
- **Cryptographic Idempotency:** SHA-256 hashing of request parameters prevents duplicate paid generation calls on network retries.
- **Budget Ceiling Firewall:** Hard project caps ($100 default) and per-shot caps ($5.00 default) halt execution before external charges occur.
- **Human Approval Gates:** Generation jobs exceeding $1.00 or utilizing unverified biometric voice clones are held in an `ApprovalTicket` queue awaiting human confirmation.



---

## ADR-034: Directed Acyclic Graph (DAG) for Node-Based Compositing

### Status
Accepted & Implemented (Part 07)

### Context & Problem Statement
OpenTimelineIO and NLE timeline tracks are designed for sequential horizontal editorial cuts, not for complex multi-branch 2D pixel transformations, planar tracking corner pins, and matte extractions.

### Decision Outcome
Chosen option: **Explicit Directed Acyclic Graph (DAG) Compositing Schema (`CompositingGraph`)**.
- Nodes possess typed input/output sockets (`IMAGE_RGBA`, `IMAGE_RGB`, `MASK_ALPHA`, `TRANSFORM_MATRIX`, `TRACK_DATA`).
- Cycle detection enforces acyclic topology, executed strictly in topological sort order via Kahn's algorithm.

---

## ADR-035: Dual-Engine Compositing Architecture (LocalCompositorEngine + BlenderCompositorEngine)

### Status
Accepted & Implemented (Part 07)

### Context & Problem Statement
Local Apple Silicon M4 hardware constraints require instant, zero-network, sub-millisecond 2D compositing without heavy 3D rendering overhead, while preserving future headless 3D OpenUSD/Cycles multi-pass rendering.

### Decision Outcome
Chosen option: **Hybrid Dual-Engine Architecture with Dynamic Router (`VFXEngineRouter`)**.
- `LocalCompositorEngine`: Pure Python + NumPy + OpenCV 5.0 for deterministic local execution of chroma keying, planar perspective warping, inpainting, and alpha merges.
- `BlenderCompositorEngine`: Standalone Python script generator for headless Blender compositor node trees and multi-pass OpenEXR compositing.

---

## ADR-036: Premultiplied Alpha Math & Linear Color Space Conformance

### Status
Accepted & Implemented (Part 07)

### Context & Problem Statement
Evaluating blurs, glows, and alpha merges in gamma-encoded sRGB produces dark fringing, muddy edges, and unphysical light summation.

### Decision Outcome
Chosen option: **Linear Radiance Space Processing with Premultiplied Alpha Blending**.
- All merge operations evaluate $C_{out} = C_{fg} + C_{bg} \times (1.0 - \alpha_{fg})$ in premultiplied linear float32 space before converting back to sRGB.
- Built-in color difference despill suppresses green/blue edge reflection on foreground subjects.

---

## ADR-037: Application-Owned Canonical 2D Animation Project Model

### Status
Accepted & Implemented (Part 08)

### Context & Problem Statement
Proprietary 2D animation tools (Live2D, Spine, Rive) introduce vendor lock-in and non-permissive runtime licenses, while simple video renders eliminate the ability to edit timing or swap character parts.

### Decision Outcome
Chosen option: **Engine-Agnostic Canonical Animation Project Schema (`AnimationProject`)**.
- Application-owned models for projects, scenes, shots, tracks, drawing exposures, keyframes, cameras, and character instances.
- Stepped exposure holds on 1s (24 fps), 2s (12 fps), and 3s (8 fps) preserve authentic animation cadence.

---

## ADR-038: Quantitative Multi-Vector Character Identity Verification

### Status
Accepted & Implemented (Part 08)

### Context & Problem Statement
Diffusion and generative AI models frequently suffer from character drift (altering face shapes, eye colors, hair volume, and costume details across seeds).

### Decision Outcome
Chosen option: **Quantitative Character DNA & Multi-Vector Validation (`IdentityValidator`)**.
- Enforces strict anatomical proportion tolerance ($\Delta_{prop} \le 5\%$) and CIE Lab color distance ($\Delta E \le 8.0$).
- Automatically discards drifting candidate frames before committing to the studio asset store.

---

## ADR-039: Authentic Japanese Anime Pipeline Standards (Settei, Genga, Doga, Shiage)

### Status
Accepted & Implemented (Part 08)

### Context & Problem Statement
Treating anime as a generic image filter produces unconvincing results without the disciplined cadence, clean line cleanup, and multiplane depth characteristic of professional anime studios.

### Decision Outcome
Chosen option: **Dedicated Anime Production Subsystems (`AnimeCelShader`, `MultiplaneBackgroundEngine`)**.
- 5-angle Settei turnaround model sheets with horizontal guide alignments.
- 3-tier cel shading (flat base, core shadow, specular rim highlight) with directional lighting.
- Multiplane parallax backgrounds with depth-scaled camera scrolling velocities ($V = V_{cam} / (1 + Z)$).

---

## ADR-040: In-Process C++ DSP Acceleration via Spotify Pedalboard with SciPy Fallback

### Status
Accepted & Implemented (Part 10)

### Context & Problem Statement
Audio processing via CLI subprocess wrappers (e.g. repeated FFmpeg invocations per clip) introduces significant process spawn overhead and file I/O bottlenecks. Conversely, launching external DAW GUI applications prevents headless automation.

### Decision Outcome
Chosen option: **In-Memory C++ JUCE DSP Processing via Spotify Pedalboard & SciPy Fallbacks**.
- Native Apple Silicon M4 ARM64 execution with sub-millisecond per-block latency.
- Full studio-grade parametric EQ, dynamic compression, brickwall limiting, algorithmic reverb, and VST3/AU hosting directly in Python.
- 100% pure NumPy/SciPy fallback topologies ensure zero platform lock-in.

---

## ADR-041: Strict ITU-R BS.1770-4 / EBU R128 Gated Loudness Normalization

### Status
Accepted & Implemented (Part 10)

### Context & Problem Statement
Un-normalized audio causes jarring volume fluctuations across scenes and triggers aggressive, unpredictable platform compression on YouTube, Spotify, and broadcast networks.

### Decision Outcome
Chosen option: **Standardized Gated Integrated Loudness (LUFS) & 4x Oversampled True Peak Metering**.
- Target profiles: YouTube (-14.0 LUFS, -1.0 dBTP), Apple Podcasts (-16.0 LUFS, -1.0 dBTP), EBU R128 (-23.0 LUFS, -1.0 dBTP).
- 2-pass normalization eliminates digital inter-sample clipping on consumer DACs without sacrificing dynamic range.

---

## ADR-042: Automated Dialogue-Driven Sidechain Ducking & Procedural Foley Synthesis

### Status
Accepted & Implemented (Part 10)

### Context & Problem Statement
Background music and sound effects frequently mask dialogue intelligibility. Furthermore, external royalty-free sound libraries introduce storage overhead and potential licensing copyright claims.

### Decision Outcome
Chosen option: **Automatic Sidechain Ducking & Deterministic Procedural SFX Synthesis**.
- Sidechain ducking dynamically reduces background music gain (by -14 dB) with 120ms attack and 750ms release during speech activity.
- Pure procedural synthesis generates sub-bass impacts, swept whooshes, tension risers, and ambient drones purely from mathematical equations, providing 100% royalty-free commercial safety.

---

## ADR-043: Provider-Independent Capability-Based Generative Model Orchestration

### Status
Accepted & Implemented (Part 11)

### Context & Problem Statement
The generative AI landscape is evolving rapidly. Hardcoding vendor-specific APIs (Runway, Kling, Midjourney, ElevenLabs) throughout the application creates tight vendor lock-in, breaks when APIs deprecate parameters, and prevents seamless fallback to open-weight models (Wan2.1, FLUX.1, Kokoro-82M).

### Decision Outcome
Chosen option: **Decoupled Capability-Based Adapter & Registry Architecture (`BaseGenerationProvider`, `GenerationRouter`, `ProviderRegistry`)**.
- Generation requests specify capabilities (`modality`, `min_resolution`, `aspect_ratio`, `target_fps`, `max_cost`) rather than specific vendors.
- The `GenerationRouter` dynamically selects the best available registered model based on project budget and technical constraints.
- Local mock adapters ensure deterministic, zero-cost unit testing and CI/CD execution without external API dependencies.

---

## ADR-044: Structured Multi-Dimensional Prompt Compilation vs Raw Plain-Text Prompts

### Status
Accepted & Implemented (Part 11)

### Context & Problem Statement
Different generative models demand fundamentally different prompt syntax for optimal quality. Runway Gen-3 Alpha responds best to bracketed camera directives (`[Camera: pan right]`), Kling 1.5 requires anatomical physics descriptors, while FLUX.1 generates superior results from descriptive prose paragraphs without keyword tagging.

### Decision Outcome
Chosen option: **Multi-Dimensional Prompt Compiler (`PromptCompiler`)**.
- Creative agents emit structured prompt dimensions (`StructuredPromptDimensions`: subject, action, environment, camera, lighting, mood, style, technical specs).
- Dedicated compiler targets translate these dimensions deterministically into model-specific syntax (Runway, Kling, FLUX, Midjourney, AudioCraft).
- Negative prompts and character-consistency triggers are automatically appended based on bound reference profiles.

---

## ADR-045: Multi-Tier Budget Firewalls & Human-in-the-Loop Approval Gates for Paid APIs

### Status
Accepted & Implemented (Part 11)

### Context & Problem Statement
Autonomous AI creative agents operating in iterative loops can inadvertently exhaust project budgets by submitting repeated, unconstrained paid API calls (e.g. 4K high-tier video generation at $0.50-$2.00 per attempt).

### Decision Outcome
Chosen option: **Multi-Tier Financial Firewall & Cryptographic Idempotency (`GenerationBudgetManager`, `ApprovalGateManager`, `GenerationJobQueue`)**.
- **Cryptographic Idempotency:** SHA-256 hashing of request parameters prevents duplicate paid generation calls on network retries.
- **Budget Ceiling Firewall:** Hard project caps ($100 default) and per-shot caps ($5.00 default) halt execution before external charges occur.
- **Human Approval Gates:** Generation jobs exceeding $1.00 or utilizing unverified biometric voice clones are held in an `ApprovalTicket` queue awaiting human confirmation.



---

## ADR-046: Scene-Referred ACEScg/ACEScct Floating-Point Architecture with OCIO Compatibility

### Status
Accepted & Implemented (Part 12)

### Context & Problem Statement
Applying color grading, VFX compositing, or neural restoration directly on display-referred 8-bit integer pixels (e.g. standard Rec.709 sRGB) leads to severe quantization banding, clipped highlight blowout, and inconsistent behavior across camera sources (e.g. ARRI LogC3, Sony S-Log3, Canon C-Log3).

### Decision Outcome
Chosen option: **Scene-Referred ACEScg/ACEScct 32-bit Floating-Point Architecture (`ColorManager`)**.
- All media is linearized upon ingestion via Input Device Transforms (IDTs) into ACEScg (AP1 primaries) or ACEScct (logarithmic toe for tactile grading).
- Primary corrections (exposure, contrast, balance) operate in linear radiance before applying Output Device Transforms (ODTs) conforming to Rec.709, Display P3, or Rec.2100 HDR.
- Seamless fallback to analytical NumPy vector math when native OpenColorIO C++ libraries or configs are absent.

---

## ADR-047: Strict Separation of Creative Color Grading from Technical Video Restoration

### Status
Accepted & Implemented (Part 12)

### Context & Problem Statement
Creative color grading (artistic look, mood, contrast, saturation) and technical video restoration (deinterlacing, denoising, scratch removal, deflicker, upscaling) have fundamentally different objectives, mathematical models, validation methods, and risks. Conflating them causes destructive processing and unpredictable regressions.

### Decision Outcome
Chosen option: **Decoupled Grading Node Graphs (`GradingGraph`) vs Modular Restoration Chains (`RestorationPipeline`)**.
- Color grading operates via non-destructive parameter graphs without altering source pixels.
- Restoration operates as staged, reversible signal-processing filters creating distinct master derivatives in the Central Asset Database.
- Quality control metrics for restoration (PSNR, SSIM, duration sync) are separate from color gamut audits.

---

## ADR-048: Non-Destructive DAG-Based Grading & Reversible Inpainting Derivative Registration

### Status
Accepted & Implemented (Part 12)

### Context & Problem Statement
Overwriting camera raw files or intermediate renders prevents creative experimentation, breaks A/B comparisons, and destroys editorial integrity. Furthermore, neural upscaling can hallucinate synthetic details that must not be falsely claimed as authentic historical media.

### Decision Outcome
Chosen option: **Non-Destructive Versioned Derivation with Provenance Tagging (`AssetStoreBridge`)**.
- Source files remain byte-for-byte read-only.
- Graded and restored deliverables are registered as independent derivatives in the Central Asset Database (`derivatives` table).
- AI upscaled frames are explicitly labeled with `detail_reconstruction_type: "AI_SYNTHESIZED_TEXTURE"` and `is_authentic_ground_truth: False`.
