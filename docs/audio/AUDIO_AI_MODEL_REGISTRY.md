# Audio AI Model Registry
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production & 17_subtitles_dubbing  
**Document:** AUDIO_AI_MODEL_REGISTRY.md  
**Version:** 1.0.0  

---

## 1. Registry Purpose & Scope

The Audio AI Model Registry catalogues all machine learning and deep learning models utilized across Department 14 (Audio Production) and Department 17 (Subtitles & Dubbing). Every model must have documented weights size, inference device target, commercial license terms, and memory characteristics.

---

## 2. Audio & Speech Model Catalog

### 2.1 Speech Synthesis (TTS & Dubbing)

| Model Name | Version | Developer | Parameter Size | Download Size | Primary Device | License | Commercial Permitted |
|---|---|---|---|---|---|---|---|
| **Kokoro** | 82M (v0.19) | Hexgrad | 82 Million | ~80 MB | M4 CPU / MPS | Apache 2.0 | **Yes** |
| **ElevenLabs Turbo v2.5**| 2.5 | ElevenLabs Inc. | Remote API | N/A (Cloud) | Cloud GPU | Commercial SaaS | **Yes (Paid Tier)** |
| **Edge-TTS** | 2024 | Microsoft | Remote API | N/A (Edge) | Cloud CDN | Service Agreement | Restricted (Internal/Scratch) |
| **WhisperX** | Large-v3 | Max Bain / OpenAI | 1.5 Billion | Remote / MPS | Cloud GPU / MPS | MIT / Apache 2.0 | **Yes** |
| **Faster-Whisper** | Medium / Large-v3 | Systran / CTranslate2| 769M / 1.5B | ~1.4 GB | M4 CPU (int8) | MIT | **Yes** |

### 2.2 Source Separation & Audio Isolation

| Model Name | Version | Developer | Checkpoint Size | Device Target | License | Production Use |
|---|---|---|---|---|---|---|
| **Demucs (HTDemucs)** | v4 | Meta AI Research | ~1.8 GB | Remote GPU / M4 MPS | MIT | **Approved (Commercial safe)** |
| **SciPy Median HPSS** | N/A (DSP) | SciPy Community | 0 MB (Code) | M4 CPU (Immediate) | BSD-3-Clause | **Default Built-in Fallback** |
| **DeepFilterNet** | 3.0 | Rihards Fischer | ~45 MB | M4 CPU (Real-time) | MIT / Apache 2.0 | **Approved (Vocal cleanup)** |

### 2.3 Music & Sound Generation

| Model Name | Purpose | Weights Size | Hosting / Inference | License | Commercial Status |
|---|---|---|---|---|---|
| **MusicGen (Small)** | Original Scoring | ~1.2 GB | Remote API / RunPod | MIT | **Approved** |
| **Procedural Audio Synth**| Foley & SFX Generation | 0 MB (Code) | Local Python / SciPy | MIT | **Approved (100% Commercial safe)** |
| **AudioCraft (AudioGen)**| Environmental SFX | ~1.4 GB | Remote GPU | MIT | **Approved** |

---

## 3. Storage & Memory Budget Compliance

In compliance with `AGENTS.md` Prime Directive 2:
- **No local checkpoints exceed 2.0 GB.**
- Large neural workloads (MusicGen, HTDemucs 4-stem batch) execute via remote GPU endpoints or lightweight quantized Apple Silicon MPS execution.
- Kokoro-82M (80MB) and DeepFilterNet (45MB) run locally with negligible memory footprint (<250MB combined).
