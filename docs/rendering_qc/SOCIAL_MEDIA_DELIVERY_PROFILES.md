# Social Media Delivery Profiles Specification

## 1. Social Platform Requirements Overview
Social media delivery profiles optimize for bandwidth efficiency, mobile display aspect ratios, rapid time-to-first-frame streaming, and punchy loudness.

## 2. Platform Profile Specifications

### 2.1 YouTube Long-Form (1080p / 4K Landscape)
- **Container:** MP4 (`-movflags +faststart`)
- **Aspect Ratio:** 16:9 Landscape ($1920\times1080$ or $3840\times2160$)
- **Video Codec:** H.264 High Profile / HEVC Main 10 Profile
- **Bitrate:** 12 Mbps (1080p) / 45 Mbps (4K)
- **Audio:** AAC-LC Stereo, 384 kbps, 48,000 Hz, target $-14.0\text{ LUFS}$
- **Subtitles:** WebVTT sidecar + burn-in optional

### 2.2 YouTube Shorts / TikTok / Instagram Reels (Vertical 9:16)
- **Container:** MP4 (`-movflags +faststart`)
- **Aspect Ratio:** 9:16 Portrait ($1080\times1920$)
- **Video Codec:** H.264 High Profile (Level 4.2)
- **Frame Rate:** 30 fps or 60 fps
- **Bitrate:** 8–10 Mbps
- **Audio:** AAC-LC Stereo, 256 kbps, 48,000 Hz, target $-14.0\text{ LUFS}$
- **Subtitles:** Burned-in kinetic typography (centered in vertical 35% safe area)
- **Thumbnail:** Custom cover poster frame ($1080\times1920$ JPEG)

### 2.3 Instagram Feed / Facebook (Square 1:1)
- **Container:** MP4
- **Aspect Ratio:** 1:1 Square ($1080\times1080$)
- **Video Codec:** H.264 High Profile
- **Bitrate:** 6 Mbps
- **Audio:** AAC-LC Stereo, 192 kbps, target $-14.0\text{ LUFS}$

