# Music Production, Dynamic Ducking & Beat Matching
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** MUSIC_PRODUCTION.md  
**Version:** 1.0.0  

---

## 1. Musical Roles in Video Production

Music establishes emotional tone, rhythm, and pacing. Background music must support speech without competing for the same acoustic frequency space or masking vital dialogue.

---

## 2. Dynamic Dialogue Ducking (Sidechain Gain Reduction)

Dynamic ducking automatically lowers the music volume whenever dialogue or voiceover is present.

```
Dialogue Track:  ───[  Voice Active  ]─────────[  Voice Active  ]───
                       │                              │
Sidechain Detector:    ▼                              ▼
Ducking Envelope: ───┐               ┌──────────────┐               ┌───
                     │ -14 dB Duck   │              │ -14 dB Duck   │
Music Output:     ───┴───────────────┴──────────────┴───────────────┴───
```

### Parameter Specifications:
- **Detection Threshold**: $-24.0\text{ dBFS}$ (dialogue energy threshold).
- **Attenuation Depth**: $-12.0\text{ dB}$ to $-18.0\text{ dB}$ (cinematic balance).
- **Attack Time**: $150\text{ ms}$ (smooth fade down before first syllable).
- **Hold Time**: $400\text{ ms}$ (prevents fluttering during brief speech pauses).
- **Release Time**: $800\text{ ms}$ to $1200\text{ ms}$ (gentle return to full volume).

---

## 3. Beat Grid Detection & Editorial Synchronization

- **Tempo (BPM) Estimation**: Autocorrelation of onset strength envelopes extracts musical tempo.
- **Beat Grid Generation**: Calculates exact video frame timestamps for musical downbeats.
- **Edit Snapping**: Video cuts in Department 05 (Video Editing) snap to beat grid timestamps for rhythmic montage editing.
