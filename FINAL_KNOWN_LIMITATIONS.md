# Final Known Limitations & Hardware Capability Boundaries
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Verification Date:** 2026-11-21  
**Status:** Authoritative Architectural Truth  

---

## 1. Hardware & Platform Boundaries

1. **Local Apple Silicon Execution (M4, 16GB RAM):**
   - **Video Diffusion Limitation:** Massive generative diffusion models requiring CUDA (Wan2.1 14B, Flux.1 Schnell, HunyuanVideo) cannot run in local unified memory without severe paging. These workloads require remote GPU worker dispatching.
   - **Hardware VideoToolbox Concurrency:** Apple Silicon VideoToolbox ASIC hardware encoders support up to 4 concurrent hardware encoding sessions. Concurrent renders beyond 4 are queued or automatically routed to CPU fallback (`libx264`).
   - **Local Storage Ceiling:** Local storage (~38 GB free disk) requires strict hygiene. Multi-terabyte 4K ProRes master archives must be offloaded to NAS or S3/R2 object storage.

---

## 2. Media Codec & Format Boundaries

1. **Interlaced Video (1080i):**
   - The studio timeline enforces progressive framebases (24p, 25p, 30p, 60p). Interlaced camera footage (1080i50, 1080i59.94) must be deinterlaced via `yadif=mode=1` during Department 03 ingestion.
2. **Proprietary Camera RAW Codecs (RED R3D, ARRI ARRIRAW, Blackmagic BRAW):**
   - Requires vendor proprietary SDKs not included in standard FFmpeg distributions. Raw camera files must be converted to Apple ProRes 4444 XQ or OpenEXR image sequences before ingestion.
3. **Multi-Track Audio Formats beyond 7.1 Surround (Dolby Atmos):**
   - The studio DAW mixing engine supports Mono, Stereo, 5.1, and 7.1 channel configurations. Spatial audio bed rendering (Dolby Atmos ADM BWF) is planned for future enterprise releases.

---

## 3. Third-Party Generative Cloud Provider Dependencies

1. **API Key Requirement:** Live generation via Runway Gen-3, TwelveLabs, or ElevenLabs requires valid commercial API keys. When keys are unconfigured, the router operates in deterministic synthetic fixture mode with clear provenance metadata.
2. **Rate Limits & Outages:** External provider outages or rate throttling do not crash the studio pipeline; failed generative calls transition to `RETRYING` or trigger manual coverage replacement in the production planner.

---

## 4. 3D OpenUSD & Headless Blender Integration

1. **Blender Executable Requirement:** Department 11 requires a locally installed Blender 4.x binary (`blender`) in system PATH to execute OpenUSD viewport rendering. In headless cloud environments, a Blender container layer must be mounted.
