# Sound Effects & Foley Generation Models Comparison
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation & 14_audio_production  
**Document:** SOUND_GENERATION_COMPARISON.md  
**Version:** 1.0.0  

---

## 1. Sound FX Generation Technology Matrix

| Model / Service | Developer | Architecture | Max Duration | Audio Quality | Latency | Commercial License | Studio Verdict |
|---|---|---|---|---|---|---|---|
| **Procedural SFX Engine (Studio Core)**| Video House Studio | Pure Mathematical / SciPy | Arbitrary | 48 kHz / 24-bit Float | < 1 ms (Instant) | Apache 2.0 | **Primary Instant Zero-Cost SFX** |
| **ElevenLabs Sound Effects** | ElevenLabs | Diffusion Transformer | Up to 22s | 44.1 kHz / Stereo | ~1.2s (Cloud API) | Commercial Permitted | **Primary Organic Cinematic SFX** |
| **AudioCraft (AudioGen)** | Meta AI Research | Autoregressive Transformer | 10s | 16 kHz / Mono | ~2.5s (Compute) | MIT | **Secondary Open Source Sound FX** |
| **Audiobox** | Meta AI Research | Flow Matching | 10s | 48 kHz / Stereo | Research API | Research / Limited | **Experimental Reference** |

---

## 2. Realism vs Procedural Reproducibility

- **Procedural Synthesis**: Used for impacts, sub-drops, whooshes, tension risers, and drone beds. 100% deterministic, zero licensing fee, zero network latency.
- **Neural Foley (ElevenLabs SFX)**: Used for organic physical interactions (e.g. "footsteps on wet autumn leaves", "creaking heavy oak door opening", "distant thunder over ocean waves").
