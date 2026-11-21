# Music Generation Models Comparison Matrix
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation & 14_audio_production  
**Document:** MUSIC_GENERATION_COMPARISON.md  
**Version:** 1.0.0  

---

## 1. Music Generation Technology Matrix

| Model / Service | Developer | Architecture | Max Duration | Tempo / Key Control | Looping Support | Audio Quality | Pricing | Commercial License | Studio Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **AudioCraft (MusicGen Small)**| Meta AI Research | Autoregressive Transformer | 30s (Chained) | Via prompt / BPM conditioning | Yes | 32 kHz / Stereo | Free (Local compute) | MIT | **Primary Open-Source Scoring** |
| **Stable Audio 2.0** | Stability AI | Latent Diffusion (DiT) | Up to 180s | Exact BPM, Time signature | Yes | 44.1 kHz / Stereo | ~$0.10/min (API) | Commercial Permitted | **Primary Long-Form Orchestral** |
| **ElevenLabs Music** | ElevenLabs | Diffusion Audio | 60s+ | Style & Instrument prompt | Yes | 44.1 kHz / Stereo | Pay-per-credit | Commercial Permitted | **Secondary Commercial Option** |
| **Suno v3 / v4** | Suno AI | Proprietary Audio LM | Full Song (4 min) | Song prompt (Vocal + Music) | No | 48 kHz / Mixed | $10-$30/mo | Commercial (Pro/Premier only) | **Full Vocal Song Mockup Only** |
| **Udio v1.5** | Udio Inc. | Proprietary Diffusion | 2 min+ (Extendable) | Granular prompt, Lyrics | No | High fidelity | Subscription | Commercial (Standard/Pro) | **Alternative Song Prototyping** |

---

## 2. Integration with Department 14 (Audio Production)

Generated musical tracks are not dumped directly into final exports. They are transferred to Department 14 (`14_audio_production`):
1. Beat grid analysis in `departments/14_audio_production/sound_design/music_engine.py` estimates the exact BPM and downbeat timestamps.
2. The music track is assigned to `AudioTrackType.MUSIC` in `AudioSession`.
3. Sidechain ducking automatically compresses the music level by $-14\text{ dB}$ whenever dialogue or narration is spoken.
