# Audio Source Separation Engine
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_SOURCE_SEPARATION.md  
**Version:** 1.0.0  

---

## 1. Architectural Purpose

When ingesting legacy footage, archival video, or mixed production tracks, dialogue, music, and sound effects are often baked into a single stereo or mono audio channel. To perform professional editing, dialogue cleanup, or dubbing, the system must decompose composite audio into discrete stems:
- **Vocals / Dialogue**
- **Drums / Percussion**
- **Bass**
- **Other / Accompaniment & SFX**

---

## 2. Dual-Engine Separation Architecture

```
Composite Mixed Audio File
            │
            ▼
┌───────────────────────────────────────┐
│       Source Separation Router        │
└───────────────────┬───────────────────┘
                    │
      ┌─────────────┴─────────────┐
      ▼                           ▼
[Tier 1: Local DSP HPSS]   [Tier 2: Deep Learning Demucs]
- Median filter STFT       - HTDemucs 4-Stem Model
- Real-time on Apple M4    - Remote GPU or Local MPS
- Harmonic / Percussive    - Vocals, Drums, Bass, Other
      │                           │
      └─────────────┬─────────────┘
                    ▼
Discrete Audio Stems (WAV 48 kHz, 24-bit)
```

---

## 3. Harmonic-Percussive Source Separation (HPSS)

For instant local execution without heavy neural models:
1. Compute Short-Time Fourier Transform: $X(t, f) = \text{STFT}(x)$.
2. Calculate median filtering across time ($M_{\text{harmonic}}$) to preserve continuous pitch.
3. Calculate median filtering across frequency ($M_{\text{percussive}}$) to preserve broadband vertical transients.
4. Construct soft binary masks:
   $$W_H = \frac{M_{\text{harmonic}}^2}{M_{\text{harmonic}}^2 + M_{\text{percussive}}^2}, \quad W_P = \frac{M_{\text{percussive}}^2}{M_{\text{harmonic}}^2 + M_{\text{percussive}}^2}$$
5. Invert back to time domain via inverse STFT.
