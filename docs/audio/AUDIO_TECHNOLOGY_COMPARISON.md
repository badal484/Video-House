# Audio Technology Comparison Matrix
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production & 17_subtitles_dubbing  
**Document:** AUDIO_TECHNOLOGY_COMPARISON.md  
**Version:** 1.0.0  

---

## 1. Digital Signal Processing (DSP) Libraries

| Library | License | Speed / Execution | VST3/AU Support | Multi-Channel Support | Automation Envelopes | Studio Verdict |
|---|---|---|---|---|---|---|
| **Spotify Pedalboard** | Apache 2.0 | C++ (JUCE) / Ultra Fast | Yes (Native) | Mono, Stereo, 5.1 | Yes (Sample-accurate) | **Primary DSP Engine** |
| **SciPy (scipy.signal)** | BSD-3-Clause | C/Fortran / Fast | No | Arbitrary N-channel | Yes (Vectorized) | **Primary Math / Fallback** |
| **FFmpeg Audio Filters** | LGPL / GPL | C / High Performance | Via frei0r/ladspa | Mono, Stereo, 7.1, Ambisonic | Via timeline expressions | **Delivery & Transcoding** |
| **Pydub** | MIT | Pure Python + FFmpeg / Slow | No | Mono, Stereo | Rough frame slices | **Rejected** (High latency, abandoned) |
| **librosa** | ISC | Python / SciPy / Moderate | No | Variable | No (Analysis only) | **Analysis Only** |
| **FAUST** | LGPL / MIT | JIT Compiled C++ / Real-time | Yes (Compile target) | Arbitrary | Yes | **Future Plugin Compiler** |

---

## 2. Audio Loudness & Metering Engines

| Solution | Standards Supported | True Peak Oversampling | EBU Gating (BS.1770-4) | Real-Time Latency | Headless API | Studio Verdict |
|---|---|---|---|---|---|---|
| **FFmpeg ebur128** | EBU R128, ITU BS.1770-4, ATSC A/85 | Yes (4x oversampling) | Yes (-70 LKFS / -10 LU relative) | Non-realtime / 2-pass | CLI stdout / JSON | **Primary Mastering Meter** |
| **Pedalboard Loudness** | ITU-R BS.1770-4 | Integrated | Integrated | Real-time | Python API | **In-Process Mix Meter** |
| **pyloudnorm** | MIT | Interpolated | BS.1770-4 compliant | Batch | Python API | **Auxiliary Verification** |
| **TC Electronic Radar** | Commercial | Proprietary | Hardware compliant | Zero (DSP) | Proprietary | **Not Applicable** (Headless Studio) |

---

## 3. Audio Source Separation Models

| Model | Architecture | Stems Extracted | Local Inference Speed | RAM Footprint | Commercial License | Studio Verdict |
|---|---|---|---|---|---|---|
| **Meta Demucs v4 (HTDemucs)** | Hybrid Transformer + Conv | 4 (Vocals, Drums, Bass, Other) | 0.8x RT (Apple M4 MPS) | ~1.8 GB | MIT | **Recommended Remote / Local** |
| **SciPy Harmonic-Percussive** | Median STFT Filtering | 2 (Harmonic, Percussive) | 8.0x RT (M4 CPU) | < 200 MB | BSD-3-Clause | **Built-in Fast Fallback** |
| **Spleeter (Deezer)** | U-Net CNN (TensorFlow 1.x) | 2, 4, 5 stems | 1.2x RT (CPU) | ~1.2 GB | MIT | **Deprecated** (TF1 dependency, phase smear) |
| **Open-Unmix (UMX)** | Bi-LSTM STFT | 4 stems | 0.5x RT (CPU) | ~1.0 GB | MIT | **Backup Architecture** |

---

## 4. Speech Synthesis & Vocal Engines

| Engine | Architecture | Parameter Count | Multilingual (Hindi/EN) | Real-Time Factor | Voice Cloning | License | Studio Verdict |
|---|---|---|---|---|---|---|---|
| **Kokoro-82M** | StyleTTS2 / ISTFT | 82M | Yes | 0.15x (Fast) | Fixed profiles | Apache 2.0 | **Primary Local Engine** |
| **ElevenLabs** | Proprietary Diffusion | Private | Yes (30+ languages) | Cloud API (~1.0s) | Yes (Zero-shot) | Commercial API | **Primary High-End Voice** |
| **Edge-TTS** | Microsoft Azure neural | Remote | Yes | Cloud API (~0.4s) | Presets | Microsoft ToS | **Rapid Scratch Track** |
| **Tortoise-TTS** | Autoregressive + Diffusion | ~400M | English only | 15.0x (Very slow) | Yes | Apache 2.0 | **Rejected** (Too slow for production) |
| **Bark (Suno)** | GPT-style Audio LM | Large | Multilingual | 8.0x (Slow) | Prompt-based | MIT | **SFX / Non-verbal only** |

---

## 5. Delivery Loudness Standards Reference

| Platform / Standard | Target Integrated Loudness | Max True Peak | Max Short-Term | Loudness Range (LRA) Target |
|---|---|---|---|---|
| **YouTube Video** | -14.0 LUFS (±0.5 LU) | -1.0 dBTP | -11.0 LUFS | 6–10 LU |
| **Spotify (Normal)** | -14.0 LUFS (±0.5 LU) | -1.0 dBTP | -11.0 LUFS | 5–8 LU |
| **Apple Podcasts** | -16.0 LUFS (±1.0 LU) | -1.0 dBTP | -13.0 LUFS | 4–8 LU |
| **EBU R128 (European Broadcast)** | -23.0 LUFS (±0.5 LU) | -1.0 dBTP | -18.0 LUFS | ≤ 14 LU |
| **ATSC A/85 (US Broadcast)** | -24.0 LUFS (±0.5 LU) | -2.0 dBTP | -19.0 LUFS | ≤ 15 LU |
| **Theatrical Film (5.1/7.1)** | -24.0 to -27.0 LUFS | -2.0 dBTP | Unrestricted | ≥ 15 LU (High Dynamic Range) |
