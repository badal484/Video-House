# Comprehensive Repository Audit & Architecture Decisions
## Advanced Video Reverse Engineering, Multimodal Creative Intelligence & Reference-to-Production System
**Document Version:** 1.0.0  
**Status:** Approved & Baseline Established  
**Hardware Target:** Apple MacBook Pro (Apple M4, 16GB Unified RAM, ~34GB Free Storage)

---

## 1. Executive Summary

This audit assesses the capabilities of the Universal AI Video Production Studio to reverse-engineer accessible reference videos across 12 creative, technical, and editorial dimensions. The objective is to transform any reference video URL or local media into an evidence-grounded, timestamp-accurate temporal event graph and compile it into an executable, original production blueprint for the studio's native editing, motion graphics, audio, and asset discovery engines.

The audit identifies existing foundational components, diagnoses gaps, defines upgrade pathways, and establishes Architecture Decision Records (ADRs) compliant with hardware boundaries (<2GB RAM overhead, zero local weights >2GB, strict storage hygiene).

---

## 2. Comprehensive 12-Capability Assessment Matrix

| # | Capability Domain | Current State in Repository | Critical Missing Dimensions | Upgrade Implementation Plan | Hardware & Dependency Constraints |
|---|---|---|---|---|---|
| **1** | **Media Access & Acquisition** | `OnlineMediaAcquisitionService` with `yt-dlp` metadata extraction and media download; stock asset discovery (`Wikimedia`, `Openverse`, `NasaNoaa`). | No stream chunking; no direct audio-only demuxing without video re-encoding; no multi-resolution proxy caching. | Implement low-res proxy generation (360p/720p) for fast analysis; direct audio demux to 48kHz WAV; metadata caching with SHA-256 deduplication. | Rely on system `ffmpeg`/`ffprobe` and `yt-dlp`. Max download 1080p; auto-clean raw cache. |
| **2** | **Video Decoding & Frame Extraction** | OpenCV `cv2.VideoCapture` with fixed step sampling (e.g. every 5 or 12 frames). | Fixed stride misses rapid cuts (sub-5 frames), flash frames, and swift text reveals; no Presentation Timestamp (PTS) indexing; high RAM if 4K decoded. | Build `HighResolutionTemporalSamplingEngine` with 5-pass multi-resolution sampling (Global, Shot-level PTS, Adaptive high-motion, Keyframe inspection, Verification). | Decode at 360p/720p for optical flow and tracking. Targeted native resolution crops only for OCR/typography. |
| **3** | **Shot & Boundary Detection** | `ShotDetectionService` using PySceneDetect `AdaptiveDetector` with fallback to basic frame difference. | Detects hard cuts only; misses dissolves, whip pans, zoom transitions, flash frames, jump cuts, and speed ramps; lacks transition duration metrics. | Build `TransitionClassifier` detecting 20+ transition types (Hard Cut, Dissolve, Cross Dissolve, Dip to Black/White, Whip Pan, Morph/Match, Push/Slide, Iris/Shape, Zoom, Speed Ramp, Jump Cut, J/L-Cuts). | Use Edge Change Ratio (ECR) + HSV histogram intersection + optical flow magnitude discontinuity. Zero GPU weights. |
| **4** | **Frame-Level Visual Intelligence** | `ComputerVisionService` with OpenCV Haar/contour tracking; basic prompt pass in `gemini_provider.py`. | No spatial composition analysis, rule-of-thirds alignment, visual balance, saliency, lighting direction, or subject-background relationship. | Build `CinematographyIntelligenceEngine` for spatial geometry, subject saliency, contrast ratios, and color temperature ($K$); route deep semantic reasoning to Gemini 1.5/2.0 API. | Cloud API for deep semantic reasoning; local OpenCV/NumPy for spatial geometry and colorimetry. Peak RAM <300MB. |
| **5** | **Audio Intelligence & Separation** | `AudioIntelligenceService` with onset detection, spectral energy, EBU R128 loudness, speech/music ratio; `faster-whisper`. | No deep stem separation on local device (Demucs is GPU/memory prohibitive); no beat/downbeat grid; lacks transient SFX classification (whoosh, riser, impact). | Implement tri-band energy filter bank (Sub/Mid/High) as local stem proxy; autocorrelation beat grid & downbeat tracking; spectral flux transient detector for SFX classification. | Local DSP via NumPy/SciPy/Pedalboard; avoid local Demucs weights (>2GB limit). Remote/Cloud for stem separation if needed. |
| **6** | **Cinematography Intelligence** | `CameraMotionService` with Farneback optical flow (downsampled 320x180) for Static, Pan, Tilt, Zoom. | No camera angle classification; no shot scale (wide/medium/close-up) estimation; no focal length/depth-of-field estimation; coarse motion labels. | Implement 6-DoF camera motion estimation via affine RANSAC (Pan, Tilt, Zoom, Dolly, Truck, Pedestal, Handheld jitter); shot scale from subject area/frequency; camera angle via vanishing points. | Pure mathematical matrix decomposition in NumPy/OpenCV. Fast, deterministic, sub-second execution. |
| **7** | **Editing & Structural Intelligence** | `ReferenceAnalysisService` computes Average Shot Length (ASL), cut frequency (CPM), and coarse pacing string. | No editorial rhythm curve, no acceleration/deceleration trends, no beat-sync alignment score, no narrative montage classification, no J/L cut detection. | Build `EditingIntelligenceEngine` calculating ASL variance, cutting velocity curves, audio-visual sync lag ($\Delta t$ between cut and downbeat/transient), and editorial structure classification. | Deterministic temporal calculations over timestamped events. Negligible RAM overhead. |
| **8** | **Motion Graphics & Typography Intelligence** | `OCRService` with horizontal morphological contour detection; basic position classification (Title, Lower Third, Subtitle). | No spatio-temporal text tracking across frames; no reveal animation detection (typewriter, slide, fade, kinetic bounce); no font style/weight inference; no kinetic trajectory. | Build `MotionGraphicsReverseEngineeringEngine`: spatio-temporal bounding box tracking (IoU tracker), trajectory curves, reveal/exit classification, kinetic typography parameters, and graphic hierarchy. | Local contour tracking + morphological features; OCR text recognition via lightweight Tesseract or Cloud API. |
| **9** | **Animation & Vector Graphics Intelligence** | None. Animation classified generically as video. | Cannot distinguish live action from 2D vector, 3D CGI, whiteboard, or stop-motion; no frame cadence detection (on 1s, on 2s). | Build `AnimationIntelligenceClassifier`: detects visual medium, frame hold cadence ($k$-frame repetition), vector flatness vs texture complexity, and stroke/fill segmentation. | Inter-frame pixel delta variance and color gradient flatness analysis in NumPy. |
| **10** | **Visual Effects (VFX) & Compositing Intelligence** | Basic `vfx_shot_task` database table for tracking VFX jobs. | Cannot detect composite layers, green-screen keying, rotoscope masks, alpha channels, particle systems, light leaks, or blur overlays in reference video. | Build `VFXDecompositionEngine`: detects alpha blending, additive blend overlays, particle bursts, screen glow, and reconstructs an inferred layer Directed Acyclic Graph (DAG). | Edge contrast analysis, color delta thresholding, and additive luminance peak tracking. |
| **11** | **Reference Video Reconstruction** | `ReferenceProfile` stores aggregate statistics (ASL, palette, BPM, key moments). | Cannot reconstruct continuous temporal timeline; lacks shot-by-shot specifications, layer hierarchies, keyframe curves, or audio cue sheets. | Build `ReferenceReconstructionEngine`: integrates all temporal detections into a structured, continuous shot-by-shot and layer-by-layer inferred assembly specification. | Structured Pydantic v2 schemas; stored in Central SQLite database. |
| **12** | **Production Blueprint Generation** | `generate_inspired_production_spec` outputs a generic JSON outline with scenes and durations. | Does not compile into executable OpenTimelineIO files, Motion Canvas AST compositions, Audio DAW tracks, or Asset Discovery queries. | Build `ReferenceToProductionCompiler`: translates reference grammar into executable `.otio` timelines, `MotionComposition` trees, Audio DAW stem layouts, and asset acquisition plans. | Direct integration with Departments 03, 08, 09, 14, 18, and 21. |

---

## 3. Architecture Decision Records (ADRs)

### ADR-001: Multi-Provider Video Intelligence Strategy & Task-Based Routing
- **Status:** Approved
- **Context:** Reverse-engineering video requires both micro-temporal precision (exact cut frames, audio transients) and macro-level creative reasoning (storytelling intent, thematic symbolism). Local CPU/DSP is optimal for precision; cloud multimodal LLMs (Gemini, TwelveLabs) are optimal for creative synthesis.
- **Decision:** Implement a two-tiered hybrid routing engine in `departments/05_multimodal_providers/router.py`:
  1. *Deterministic Tier (Local on-device):* Frame decoding, PySceneDetect cuts, optical flow camera motion, spectral audio beats/transients, morphological text tracking, and colorimetry run locally using NumPy/OpenCV/SciPy.
  2. *Reasoning Tier (Cloud Multimodal API):* Long-context video interpretation, narrative structure extraction, semantic scene understanding, and stylistic intent are delegated to Gemini 1.5/2.0 and TwelveLabs Marengo.
  3. *Graceful Offline Fallback:* If cloud API keys are absent or network is unavailable, the local deterministic engine synthesizes structural approximations without failing.

### ADR-002: Multi-Resolution Temporal Sampling Architecture
- **Status:** Approved
- **Context:** Decoding 1080p/4K video at 30/60 fps across an entire 5-minute video creates enormous memory pressure (>4GB RAM) on the 16GB Apple M4 Mac and consumes excessive compute time.
- **Decision:** Implement a 5-pass multi-resolution pipeline in `departments/04_media_intelligence/temporal_engine/`:
  - **Pass A (Global Overview):** 1 frame per second at 360p for coarse scene changes and global colorimetry.
  - **Pass B (Shot Boundary Detection):** Full frame rate on downscaled luminance stream (360p) for exact cut/transition boundaries.
  - **Pass C (Adaptive High-Motion Burst):** Targeted full-rate sampling $\pm 0.5$s around detected transitions, text appearances, and motion peaks.
  - **Pass D (High-Res Keyframe Inspection):** Native resolution extraction of single keyframes per shot for OCR, typography typography classification, and rule-of-thirds composition.
  - **Pass E (Temporal Verification):** Consistency checking and evidence validation.

### ADR-003: Unified Temporal Event Graph & Evidence Trail
- **Status:** Approved
- **Context:** Creative video elements overlap temporally (e.g. music plays under voiceover while a title animates during a camera pan across a hard cut). Flat lists of shots cannot model cross-element synchronization.
- **Decision:** Build a Unified Temporal Event Graph (`core/intelligence/event_graph.py`) storing nodes (`Video`, `Scene`, `Shot`, `Frame`, `AudioEvent`, `TextElement`, `GraphicElement`, `Transition`, `NarrativeEvent`) and directed edges (`CONTAINS`, `PRECEDES`, `OVERLAPS`, `SYNCHRONIZED_WITH`, `SUPPORTS_NARRATIVE`). Every node carries an `EvidenceRecord` specifying whether the property was directly measured, model-inferred, or user-supplied, with exact timestamps, bounding boxes, and confidence scores.

### ADR-004: Clean Production Translation (Style Inspired, 100% Original Expression)
- **Status:** Approved
- **Context:** Reference videos may be copyrighted. Re-engineering must extract *grammar, pacing, motion dynamics, color harmony, and compositional structure* without copying proprietary copyrighted footage, proprietary characters, or trademarked graphics.
- **Decision:** The `ReferenceToProductionCompiler` converts reference parameters into *abstract creative grammar rules* (e.g. "Target ASL: 2.4s, Cut on audio downbeat, Kinetic typography with ease-out-expo reveal, Analogous teal-orange color palette"). These rules then drive original asset acquisition via Department 03 (Creative Discovery) and original procedural generation via Department 09 (Motion Canvas) and Department 15 (AI Generation).

---

## 4. Hardware Budget & Resource Safeguards
- **Peak RAM:** $\le 1.8$ GB during multi-resolution video analysis.
- **Local Disk Footprint:** Proxy files stored in `temp/` and deleted immediately after event graph persistence; database footprint $<10$ MB per analyzed hour of video.
- **Zero Heavy Model Downloads:** Zero local PyTorch/HuggingFace model downloads exceeding 2GB. Whisper runs via lightweight quantized `faster-whisper` (base/small); CV runs via pure OpenCV/NumPy.

