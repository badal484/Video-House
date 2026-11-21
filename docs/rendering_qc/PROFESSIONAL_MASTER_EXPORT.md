# Professional Master Export Specification

## 1. Mastering Workflow Overview
Professional masters serve as the highest-quality archive of a completed video project. They must preserve 10-bit or 12-bit dynamic range, wide color gamuts, uncompressed multitrack audio, and frame-accurate timecode.

## 2. Standard Master Profiles Implemented

### 2.1 Apple ProRes 422 HQ Master (`prores_422_hq_master`)
- **Container:** QuickTime MOV (`.mov`)
- **Video Codec:** Apple ProRes 422 HQ (Profile 3)
- **Pixel Format:** `yuv422p10le` (10-bit 4:2:2)
- **Bitrate:** Variable (~220 Mbps at 1080p24, ~880 Mbps at 4K24)
- **Color Space:** Rec.709 (SDR) or Rec.2020 (HDR)
- **Audio Codec:** Uncompressed 24-bit 48kHz PCM (`pcm_s24le`)
- **Audio Channels:** Discrete 8-channel layout (L, R, C, LFE, Ls, Rs, Lt, Rt)

### 2.2 Apple ProRes 4444 XQ with Alpha (`prores_4444_alpha_master`)
- **Container:** QuickTime MOV (`.mov`)
- **Video Codec:** Apple ProRes 4444 XQ (Profile 5)
- **Pixel Format:** `yuva444p10le` (12-bit 4:4:4 with 16-bit lossless alpha channel)
- **Bitrate:** ~500 Mbps at 1080p24
- **Use Case:** VFX deliverable, motion graphics overlays, title card assets

### 2.3 Avid DNxHR HQX Master (`dnxhr_hqx_master`)
- **Container:** QuickTime MOV (`.mov`) or MXF OP1a
- **Video Codec:** Avid DNxHR HQX (10-bit High Quality Extended)
- **Pixel Format:** `yuv422p10le`
- **Use Case:** Cross-platform Windows/Linux non-linear editing exchange
