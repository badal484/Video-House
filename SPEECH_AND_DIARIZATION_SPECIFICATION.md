# Speech Recognition & Diarization Specification

**Document Version:** 1.0.0  
**Status:** Approved & Implemented  
**Engine:** `departments/04_media_intelligence/speech_transcriber.py`  

---

## 1. Specification Scope

This document specifies the speech recognition, word-level temporal alignment, language identification, and speaker diarization pipeline within the studio.

The engine must support:
- Multilingual speech recognition (English, Hindi, Indian English, Hinglish, Spanish, French, German, Japanese).
- Precise word-level timestamps ($start\_sec$, $end\_sec$, $confidence$) for accurate automated subtitle generation, kinetic typography, and text-based video editing.
- Acoustic speaker turn detection and tagging (`SPEAKER_00`, `SPEAKER_01`, ...).
- Zero GPU dependency on the local developer machine; executes via CTranslate2 `int8` quantization on Apple Silicon M4 CPU.

---

## 2. Technology Selection & Architecture

### Model: `faster-whisper` (CTranslate2 Engine)
- **Model Variant:** `base` (74M parameters, ~140 MB disk space).
- **Execution Engine:** CTranslate2 optimized C++ inference runtime.
- **Quantization:** `int8` (Apple M4 NEON vectorized).
- **Inference Speed:** ~12x real-time on M4 CPU (a 60-second audio track transcribes in ~5 seconds).
- **Memory Footprint:** < 250 MB RAM (well within 16GB total RAM budget).
- **License:** MIT (Commercial-friendly, zero restrictions).

### PyAV 19.x Compatibility Patch
To prevent runtime crashes caused by newer PyAV removing deprecated metadata keywords, `speech_transcriber.py` includes a transparent container opening patch that sanitizes `metadata_errors="ignore"` calls from `faster_whisper.audio.decode_audio`.

---

## 3. Acoustic Speaker Turn Diarization

Speaker identification operates via a multi-tiered strategy:
1. **Local Acoustic Turn Detection:**
   - Detects acoustic silence intervals between consecutive transcription segments.
   - Pauses exceeding $\Delta t \ge 1.20\text{ seconds}$ trigger an acoustic speaker turn heuristic, toggling between distinct speaker identifiers (`SPEAKER_00`, `SPEAKER_01`).
2. **Downstream Cloud Diarization (Optional Hook):**
   - When project settings mandate high-precision voiceprint clustering (e.g. 5+ distinct speakers), audio is routed to ElevenLabs or PyAnnote.audio via `departments/05_multimodal_providers`.

---

## 4. Canonical Data Schema & Storage

Extracted speech segments are persisted in the `transcripts` table in `projects/studio_asset_registry.db`:

```sql
CREATE TABLE IF NOT EXISTS transcripts (
    segment_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    speaker_id TEXT NOT NULL,
    start_sec REAL NOT NULL,
    end_sec REAL NOT NULL,
    text TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    words_json TEXT DEFAULT '[]',
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);
```

### Word Alignment Record (`words_json`):
```json
[
  {"word": "Welcome", "start_seconds": 0.500, "end_seconds": 0.820, "confidence": 0.99},
  {"word": "to", "start_seconds": 0.830, "end_seconds": 0.950, "confidence": 0.98},
  {"word": "the", "start_seconds": 0.960, "end_seconds": 1.100, "confidence": 0.99},
  {"word": "studio.", "start_seconds": 1.120, "end_seconds": 1.500, "confidence": 0.97}
]
```
These word timestamps directly power the Downstream Subtitling (`17_subtitles_dubbing`) and Motion Graphics (`09_motion_graphics`) departments.
