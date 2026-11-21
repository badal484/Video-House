# Audio Plugin Compatibility & Host Architecture
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_PLUGIN_COMPATIBILITY.md  
**Version:** 1.0.0  

---

## 1. Plugin Hosting Overview

The Universal AI Video Production Studio supports headless execution in automated server environments, cloud containers, and local developer workstations. While traditional DAWs require interactive GUI thread event loops to host audio plugins, Department 14 utilizes **Spotify Pedalboard** to load, configure, parameter-automate, and render standard **VST3** (Steinberg VST 3.7+) and **Audio Units (AU v2/v3)** plugins purely via Python code.

---

## 2. Plugin Format Compatibility

| Plugin Architecture | Supported | macOS (Apple Silicon M4) | Linux (x86_64 / aarch64) | Headless / Automated | Notes |
|---|---|---|---|---|---|
| **Built-in DSP (Pedalboard)** | Yes | Yes (Native arm64) | Yes | Yes (100% headless) | Highpass, Lowpass, Compressor, Limiter, Reverb, Delay |
| **VST3 (.vst3)** | Yes | Yes (arm64 binary) | Yes (.so) | Yes | Parameter discovery via `plugin.parameters` |
| **Audio Units (.component)** | Yes | Yes (arm64) | No (macOS only) | Yes | Native CoreAudio AU hosting |
| **CLAP (CLever Audio Plugin)**| Planned | Via VST3 wrapper | Via VST3 wrapper | Yes | Emerging open audio standard |
| **LADSPA / LV2** | Via FFmpeg | Yes | Yes | Yes | Scriptable via FFmpeg `ladspa` filter |

---

## 3. Sandboxed Plugin Execution & Safety

Third-party binary plugins run natively in-process. To guard against crashes, memory leaks, and segmentation faults:
1. **Validation Probe**: Plugins are verified via a lightweight sub-process probe with a $1.0\text{ s}$ timeout before being allowed into the main studio render pipeline.
2. **State Persistence**: Plugin parameters are serialized as base64-encoded binary chunk states or JSON parameter maps, allowing exact session recreation across reboots.
3. **Fallback Strategy**: If an external VST3 fails to load or crashes, the pipeline automatically falls back to native SciPy/Pedalboard DSP equivalents without halting the production job.
