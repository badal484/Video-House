# Global Multimodal Model and Provider Evaluation

**Document Version:** 1.0.0  
**Status:** Approved Architecture Reference  
**Subject:** Multimodal AI Foundation Models, Speech, and Vision Systems  

---

## 1. Video-Language Foundation Model Evaluation

| Candidate Model / Service | Latency (1 min video) | Timestamp Precision | Commercial Terms & Privacy | Apple M4 Feasibility | Final Selection Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Google Gemini 2.0 Flash** | ~1.5 - 2.8s | Sub-second native grounding | $0.0001 / sec video, opt-out available | Cloud API (Zero RAM impact) | **Selected: Cloud Primary (Reasoning & Commentary)** |
| **Google Gemini 1.5 Pro** | ~5.0 - 8.2s | High semantic accuracy | $0.0005 / sec video | Cloud API | **Selected: Cloud Secondary (Deep Complex Narratives)** |
| **TwelveLabs Marengo 2.6 / Pegasus 1.1** | ~3.0s indexing | Native temporal vector search | $0.05 / video min indexed | Cloud API | **Selected: Cloud Secondary (Vector Search & Embeddings)** |
| **Qwen2.5-VL-7B (Local)** | ~18s / frame on M4 | Frame-accurate | Apache-2.0, Zero API cost | Requires 14GB RAM (Exceeds headroom) | **Deferred to Remote GPU Workers** |
| **OpenCV + Farneback + PySceneDetect** | ~0.15s / min video | Exact frame ($1/24\text{s}$) | MIT / BSD, 100% Offline | Extremely lightweight (< 150 MB RAM) | **Selected: Local Core (Deterministic Truth)** |

---

## 2. Speech Recognition & Diarization Evaluation

| Candidate | Alignment Accuracy | Speed Factor | Resource Consumption | Commercial License | Final Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **faster-whisper (CTranslate2 int8)** | Word-level exact | ~12x real-time (M4 CPU) | ~220 MB RAM, 140 MB disk | MIT | **Selected: Core Local Speech Engine** |
| **WhisperX (Wav2Vec2 alignment)** | Phoneme-level exact | ~8x real-time | ~600 MB RAM | BSD-4-Clause | **Selected: High-Precision Conformance Tier** |
| **OpenAI Whisper API** | Good word timestamps | Network dependent | Zero local RAM, $0.006 / min | Commercial Cloud | **Alternative: Cloud Speech Fallback** |
| **ElevenLabs Scribe** | Excellent diarization | ~2.5s turn-around | Zero local RAM, Commercial | Proprietary | **Optional: Downstream Dubbing / Diarization** |

---

## 3. Computer Vision & Motion Intelligence Evaluation

| Tool / Pipeline | Computational Mode | Hardware Profile | Cut / Motion Accuracy | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **PySceneDetect AdaptiveDetector** | Luminance / delta correlation | M4 CPU (Instantaneous) | Broadcast standard exact frame cuts | **Selected: Primary Cut Detector** |
| **Farneback Dense Flow + RANSAC** | Mathematical vector fields | M4 CPU (Vectorized) | High accuracy on Pan/Tilt/Zoom | **Selected: Primary Camera Motion Engine** |
| **OpenCV MOG2 + Centroid IoU Tracker** | Foreground motion modeling | M4 CPU (Lightweight) | Robust object presence & tracking | **Selected: Primary Local Object Tracker** |
| **SAM 2.1 (Segment Anything)** | Deep Video Transformer | Requires CUDA GPU (>8GB VRAM) | Pixel-perfect mask tracking | **Routed to Remote GPU Workers (Part 13)** |

---

## 4. Hardware Awareness & Cost Constraints

In accordance with prime operational instructions:
- No large model weights (>2 GB) are downloaded to the developer machine.
- Local inference operates strictly within the 16GB Apple M4 RAM envelope.
- Temporary files generated during video sampling are cleaned up upon task completion.

