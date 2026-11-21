# Codec and Container Comparison & Delivery Matrix

## 1. Professional Codec Taxonomy
Modern video delivery requires distinguishing between:
1. **Production Masters:** Visually lossless, 10-bit or 12-bit, intra-frame (I-frame only) codecs designed for editing, color grading, and archival handoffs.
2. **Intermediate Codecs:** High-throughput, intra-frame formats for rendering cache and multi-pass compositing.
3. **Archival Masters:** Mathematically lossless, open-source, long-term preservation codecs.
4. **Distribution Encodes:** Highly compressed, inter-frame (IPB) codecs optimized for bandwidth-constrained streaming and playback compatibility.

## 2. In-Depth Codec Comparison

| Codec | Type | Chroma Subsampling | Bit Depth | Compression Ratio | Hardware Acceleration (Mac M4) | Editing Suitability | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Apple ProRes 422 HQ** | Intra-frame | 4:2:2 | 10-bit | ~6:1 | **Native Hardware ASIC** | **Outstanding** | Broadcast Master, NLE Intermediate |
| **Apple ProRes 4444 XQ** | Intra-frame | 4:4:4:4 (Alpha) | 12-bit | ~3:1 | **Native Hardware ASIC** | **Outstanding** | VFX Delivery, Alpha Composites |
| **Avid DNxHR HQX** | Intra-frame | 4:2:2 | 10-bit / 12-bit | ~6:1 | CPU / OpenCL | **Outstanding** | Cross-platform Professional Master |
| **H.264 / AVC** | Inter-frame | 4:2:0 (8-bit) / 4:2:2 | 8-bit / 10-bit | ~30:1 to 50:1 | **VideoToolbox ASIC** | Poor (GOP latency) | Universal Web & Social Delivery |
| **H.265 / HEVC** | Inter-frame | 4:2:0 / 4:2:2 | 10-bit (HDR) | ~60:1 to 100:1 | **VideoToolbox ASIC** | Poor (High CPU decode) | 4K HDR Streaming, Apple Ecosystem |
| **AV1 (libsvtav1)** | Inter-frame | 4:2:0 | 8-bit / 10-bit | ~80:1 to 130:1 | Software / M4 HW Decode | Unsuitable | Next-Gen YouTube & Web Delivery |
| **VP9** | Inter-frame | 4:2:0 | 8-bit / 10-bit | ~50:1 to 80:1 | Software Decode | Unsuitable | Legacy YouTube 4K |
| **FFV1 (Version 3)** | Lossless Intra | 4:2:2 / 4:4:4 | 10-bit / 16-bit | ~2.5:1 | Multithreaded CPU | Unsuitable | Digital Library & Archival Master |

## 3. Container File Specifications

| Container | Extensions | Supported Streams | Timecode Tracks | Subtitle Embeds | Streaming Suitability | Archival Standard |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MP4 (ISO Base Media)** | `.mp4`, `.m4v` | H.264, HEVC, AV1, AAC, MP3, Opus | Optional tmcd | mov_text (limited) | **Universal (FastStart `moov` at front)** | Moderate |
| **QuickTime MOV** | `.mov` | ProRes, DNxHR, H.264, PCM, AAC | Native QuickTime TC | tx3g, timed text | Very Good | **Industry Standard Master** |
| **Material Exchange Format (MXF)**| `.mxf` (OP1a) | DNxHR, ProRes, AVC-Intra, PCM | SMPTE 12M TC | SMPTE-TT / IMSC | Broadcast Only | **Broadcast Master Standard** |
| **Matroska (MKV)** | `.mkv` | Any codec, multi-audio, PCM | Matroska tags | SRT, ASS, VTT, PGS | Excellent for desktop | **FIAF Archival Standard** |
| **WebM** | `.webm` | VP9, AV1, Opus, Vorbis | None | WebVTT | Web / HTML5 native | Unsuitable |

## 4. Operational Strategy for Department 19
- **Internal Master Intermediate:** Apple ProRes 422 HQ (or ProRes 4444 for motion graphics with alpha transparency).
- **Web & Social Delivery:** MP4 container with faststart optimization (`-movflags +faststart`), H.264 / HEVC video, and 48kHz AAC stereo audio.
- **Archival Package:** Matroska MKV with lossless FFV1 v3 and 24-bit 48kHz uncompressed PCM audio.

