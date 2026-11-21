# Professional Delivery Standards & Specification Matrix

## 1. Professional Delivery Ecosystem
Delivery packaging requires bundling video streams, multilingual audio tracks, closed captions/subtitles, promotional artwork, and machine-readable metadata into standardized directory structures and container formats.

## 2. Professional Delivery Standards

### 2.1 Interoperable Master Format (IMF - SMPTE ST 2067)
- **Standard:** SMPTE ST 2067-2 / BBR (Broadcast & Online Delivery).
- **Core Components:**
  - Composition Playlist (CPL XML): Defines editorial timeline, track routing, and asset UUID references.
  - Packing List (PKL XML): Cryptographic SHA-1/SHA-256 manifest of all essence files.
  - Asset Map (ASSETMAP XML): Resolves logical UUIDs to physical storage file paths.
  - Essence Containers: MXF Track Files (OP-Atom or OP1a) holding JPEG 2000, ProRes, or DNxHR picture tracks and 24-bit 48kHz uncompressed PCM audio.
- **Use Case:** Global streaming platforms (Netflix, Disney+, Amazon Prime).

### 2.2 Apple ProRes Professional Master Delivery
- **Standard:** Apple ProRes Certified Workflow.
- **Profile:** Apple ProRes 422 HQ (or ProRes 4444 for visual effects with alpha channel).
- **Container:** QuickTime MOV (`.mov`) with discrete uncompressed 24-bit 48kHz PCM audio tracks (Channel 1: Left, Channel 2: Right, Channels 3–8: 5.1 Surround, Channels 9+: Multilingual dubs).
- **Use Case:** Theatrical exhibition, broadcast commercials, archival masters.

### 2.3 Broadcast MXF (SMPTE OP1a)
- **Standard:** SMPTE 378M (Operational Pattern 1a).
- **Video:** XDCAM HD422 (MPEG-2 50Mbps 4:2:2) or AVC-Intra 100.
- **Audio:** 8 channels of uncompressed 24-bit 48kHz PCM.
- **Timecode:** Continuous non-drop or drop-frame timecode track (SMPTE 12M).
- **Use Case:** Television broadcast playout (BBC, EBU, Discovery).

### 2.4 Social Media Delivery Package
- **Standard:** YouTube Long-form, YouTube Shorts, Instagram Reels, TikTok.
- **Container:** MP4 with FastStart (`moov` atom at file beginning for instant web playback).
- **Video:** H.264 High Profile / HEVC Main 10 Profile, progressive scan, closed GOP (2-second cadence), chroma subsampling 4:2:0.
- **Audio:** AAC-LC Stereo, 320 kbps, 48,000 Hz, $-14.0\text{ LUFS}$.
- **Sidecars:** WebVTT or SRT subtitle files; cover thumbnail (`poster.jpg`, $1920\times1080$ or $1080\times1920$).

### 2.5 Digital Archival Master (FFV1 / Matroska)
- **Standard:** IETF RFC 9043 (FFV1 Video Codec) in Matroska (`.mkv`).
- **Features:** Lossless intra-frame compression, CRC32 packet-level error detection, 10-bit or 16-bit 4:2:2 / 4:4:4 color fidelity.
- **Use Case:** Library of Congress, FIAF national film heritage preservation.

