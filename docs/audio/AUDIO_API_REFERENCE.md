# Audio Production REST API & CLI Reference
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production & 01_studio_application  
**Document:** AUDIO_API_REFERENCE.md  
**Version:** 1.0.0  

---

## 1. Overview

Department 14 exposes asynchronous and synchronous REST endpoints via the central FastAPI application (`departments/01_studio_application/api.py`).

---

## 2. API Endpoints

### 2.1 Audio Sessions
- `POST /api/v1/audio/sessions`: Create a new multitrack audio session.
- `GET /api/v1/audio/sessions/{session_id}`: Retrieve session manifest, tracks, and clip hierarchy.
- `POST /api/v1/audio/sessions/{session_id}/tracks`: Add a track (Dialogue, Music, SFX, etc.).
- `POST /api/v1/audio/sessions/{session_id}/clips`: Add an audio clip to a track.

### 2.2 Mixing & Mastering
- `POST /api/v1/audio/sessions/{session_id}/mix`: Render full session to master audio buffer.
- `POST /api/v1/audio/sessions/{session_id}/master`: Conforms master buffer to target loudness profile (YouTube, EBU R128, Podcasts).
- `POST /api/v1/audio/sessions/{session_id}/stems`: Exports discrete stem files (Dialogue stem, Music stem, SFX stem).

### 2.3 Audio Restoration & Sound Design
- `POST /api/v1/audio/dialogue/clean`: Clean noisy dialogue with hum removal and de-essing.
- `POST /api/v1/audio/sfx/generate`: Procedurally synthesize whooshes, risers, and cinematic impacts.
- `POST /api/v1/audio/separate`: Decompose composite audio into stems.
