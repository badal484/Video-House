# Multilingual Delivery & Packaging Specification

## 1. Broadcast & Streaming Master Delivery
Department 17 packages localized productions into standard delivery formats for theatrical, broadcast, OTT streaming, and social channels.

## 2. Deliverables Matrix

### 2.1 Video Masters with Embedded Multi-Audio & Subtitles (MP4 / MKV)
- Single container file holding:
  - Video Stream (H.264 / H.265 / ProRes 422 HQ).
  - Track 1 (Audio): Original Mix (Stereo / 5.1 Surround, e.g. English).
  - Track 2 (Audio): Dubbed Spanish (Stereo / 5.1 Surround).
  - Track 3 (Audio): Dubbed Hindi (Stereo / 5.1 Surround).
  - Track 4 (Subtitle): English SDH (Closed Captions).
  - Track 5 (Subtitle): Spanish Forced Narratives / Dialogue.
  - Track 6 (Subtitle): Hindi Devanagari.

### 2.2 Discrete Subtitle Sidecar Packages
- Directory structure holding standardized `.srt`, `.vtt`, `.ass`, and `.ttml` files labeled by BCP-47 language tags:
  - `subtitles_en-US.vtt`
  - `subtitles_es-ES.vtt`
  - `subtitles_hi-IN.vtt`
  - `subtitles_hi-IN.ass` (for stylized / karaoke social reels)

### 2.3 OpenTimelineIO Multilingual Editorial Assembly
- Exports a complete `.otio` timeline containing distinct video and audio tracks for each localized language, allowing downstream human editors in DaVinci Resolve, Premiere Pro, or Final Cut Pro to adjust cuts and balances.
