# Audio Engine Architecture & Subsystem Specification
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_ENGINE_ARCHITECTURE.md  
**Version:** 1.0.0  

---

## 1. Architectural Mission

The Audio Production Department provides a sample-accurate, non-destructive, multitrack audio manipulation, mixing, and mastering engine. It bridges natural language creative direction from the AI Director (Department 04), speech transcripts from Multimodal Intelligence (Department 03), and timeline synchronization from Non-Linear Editing (Department 05), while rendering final audio conformant to global broadcasting and streaming standards.

```
       ┌────────────────────────────────────────────────────────┐
       │             04_creative_direction (Director)           │
       │           ProductionBlueprint Audio Cue List           │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             14_audio_production / Core Session         │
       │    AudioSession (Sample Rate: 48kHz, Tracks, Buses)    │
       └───────┬───────────────────┬────────────────────┬───────┘
               │                   │                    │
               ▼                   ▼                    ▼
       ┌───────────────┐   ┌───────────────┐   ┌────────────────┐
       │ Dialogue Bus  │   │ Music Bus     │   │ SFX/Foley Bus  │
       │ - Noise Gate  │   │ - Dynamic EQ  │   │ - Spatial Pan  │
       │ - De-Esser    │   │ - Sidechain   │   │ - Procedural   │
       │ - Hum Notch   │   │   Ducker      │   │   Synthesizer  │
       └───────┬───────┘   └───────┬───────┘   └────────┬───────┘
               │                   │                    │
               └───────────────────┼────────────────────┘
                                   │ Summing Bus
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                    Master Output Bus                   │
       │       - Multiband Limiter (Ceiling: -1.0 dBTP)         │
       │       - EBU R128 / YouTube Loudness Normalizer         │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │      08_video_editing (OpenTimelineIO Synchronization)  │
       │            Final Conformed Stems (D, M, E, Master)     │
       └────────────────────────────────────────────────────────┘
```

---

## 2. Subsystem Decomposition

The audio production department is divided into eight modular components:

### 2.1 Core Session Layer (`departments/14_audio_production/core/`)
- `session_models.py`: Strongly-typed Pydantic and dataclass models defining `AudioSession`, `AudioTrack`, `AudioClip`, `AudioBus`, `AutomationLane`, `AutomationPoint`, and `LoudnessStandard`.
- Guarantees sample-accurate positioning using rational integer arithmetic or sample indices ($sample\_index = round(seconds \times sample\_rate)$).

### 2.2 DSP Processing Engine (`departments/14_audio_production/dsp/`)
- `equalizer.py`: 5-band parametric equalizer (High-Pass, Low-Shelf, Peak 1, Peak 2, High-Shelf, Low-Pass).
- `dynamics.py`: Peak and RMS compressor, brickwall peak limiter, downward expander, and noise gate.
- `effects.py`: Algorithmic reverb (early reflections + late diffuse decay), stereo delay, chorus, and stereo widener.
- `loudness.py`: ITU-R BS.1770-4 compliance engine calculating Integrated LUFS, Loudness Range (LRA), and True Peak oversampling.

### 2.3 Dialogue Restoration & Editing (`departments/14_audio_production/dialogue/`)
- `dialogue_cleaner.py`: Spectral noise suppression using minimum-statistics noise estimation, 50 Hz / 60 Hz hum attenuation with sharp notch filter cascades ($Q \ge 30$).
- `de_esser.py`: Frequency-targeted split-band dynamic attenuator targeting 4.5 kHz – 8.5 kHz harsh sibilance without degrading vocal brilliance.
- `room_tone.py`: Ambient acoustic fingerprint extraction during dialogue pauses; crossfaded loop generation to fill editorial silence.

### 2.4 Sound Design & Procedural Foley (`departments/14_audio_production/sound_design/`)
- `sound_library.py`: Metadata catalog for indexed audio assets, supporting semantic search and frequency profile tagging.
- `procedural_sfx.py`: Mathematical synthesis of cinematic sound effects: exponential frequency drops (sub-drops), swept noise (whooshes), frequency-modulated tonal risers, and impact transients.
- `music_engine.py`: Dynamic sidechain envelope generator that detects dialogue presence and computes smooth dB attenuation curves on music beds with variable attack and release slopes.

### 2.5 Multitrack Mixer & Mastering (`departments/14_audio_production/mixing/`)
- `multitrack_mixer.py`: High-speed 32-bit floating point summing engine. Sums all active tracks and buses, processes clip envelopes, crossfades, and routing matrices.
- `mastering_engine.py`: Two-pass loudness normalization engine conforming final audio to target delivery specifications (YouTube, Spotify, Apple Podcasts, EBU R128) with zero hard-clipping.

### 2.6 Vocal Dubbing & Speech Generation (`departments/14_audio_production/voice/`)
- `voice_producer.py`: Interface for neural text-to-speech, emotion-inflected voiceover generation, and voice talent license verification.

### 2.7 Source Separation (`departments/14_audio_production/separation/`)
- `source_separator.py`: 4-stem decomposition manager isolating vocals, drums, bass, and accompaniment.

### 2.8 Bridges & Departmental Integrations (`departments/14_audio_production/integrations/`)
- `timeline_bridge.py`: Bidirectional synchronization between OpenTimelineIO multi-track timelines and `AudioSession`.
- `director_bridge.py`: Parses creative direction cues from `ProductionBlueprint` and configures musical mood, dialogue pacing, and sound effects.
