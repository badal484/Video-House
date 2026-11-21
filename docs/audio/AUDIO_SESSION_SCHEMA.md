# Audio Session Schema & Data Model Specification
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_SESSION_SCHEMA.md  
**Version:** 1.0.0  

---

## 1. Entity-Relationship Overview

The Audio Session schema models a multitrack digital audio workstation project:

```
┌────────────────────────────────────────────────────────┐
│                      AudioSession                      │
│   session_id: UUID                                     │
│   project_id: UUID                                     │
│   sample_rate: 48000                                   │
│   channel_layout: STEREO / 5.1                         │
│   tempo_bpm: float = 120.0                             │
│   master_bus: AudioBus                                 │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
            ▼ 1..*                           ▼ 1..*
┌────────────────────────┐       ┌────────────────────────┐
│       AudioTrack       │       │        AudioBus        │
│ track_id: UUID         │       │ bus_id: UUID           │
│ track_type: TrackType  │       │ name: str              │
│ gain_db: float         │       │ gain_db: float         │
│ pan: float (-1 to +1)  │       │ fx_chain: List[AudioFX]│
│ fx_chain: List[AudioFX]│       └────────────────────────┘
│ send_targets: List[str]│
└───────────┬────────────┘
            │ 1..*
            ▼
┌────────────────────────┐       ┌────────────────────────┐
│       AudioClip        │       │     AutomationLane     │
│ clip_id: UUID          │       │ lane_id: UUID          │
│ asset_id: UUID         │       │ parameter: str         │
│ start_time_sec: float  │◄─────┤ points: List[AutoPoint]│
│ duration_sec: float    │       └────────────────────────┘
│ source_in_sec: float   │
│ gain_db: float         │
│ pan: float             │
│ fade_in_sec: float     │
│ fade_out_sec: float    │
│ crossfade_sec: float   │
│ pitch_semitones: float │
└────────────────────────┘
```

---

## 2. Track Types & Roles

Every audio track possesses a semantic `AudioTrackType`:
- `DIALOGUE`: Production dialogue, lavalier and boom microphone recordings. Routed through highpass filter, noise reduction, and de-esser.
- `VOICE_OVER`: Voiceover narration and dubbing. Clean, upfront presence with close proximity EQ.
- `MUSIC`: Background scores, licensed tracks, and synthesized music beds. Subject to automated sidechain ducking.
- `SOUND_EFFECTS`: Spot effects, hard sound effects, vehicle sounds, impacts.
- `FOLEY`: Human-scale interactive audio (footsteps, cloth movement, object handling).
- `AMBIENCE`: Environmental soundscapes (wind, ocean, city rumble, room tone).
- `ROOM_TONE`: Stationary acoustic background recorded on location.
- `BUS`: Auxiliary summing sub-mix group (e.g. Dialogue Bus, Music Bus, FX Bus).
- `MASTER_BUS`: The final summing bus feeding delivery mastering.

---

## 3. Automation & Envelopes

Automation allows parameters (gain, pan, filter cutoff, reverb wet mix) to vary continuously over time.
- `AutomationPoint`: Pair of `(time_sec, value, curve_type)`.
- Supported curve types: `LINEAR`, `EXPONENTIAL`, `LOGARITHMIC`, `S_CURVE`.
- Evaluator: `evaluate_automation(lane, current_time_sec)` computes interpolated parameter values with sub-millisecond precision.
