# Subtitle Format Standards & International Guidelines

## 1. Professional Subtitle Format Specifications
Department 17 supports five primary subtitle and captioning formats to satisfy broadcast television, streaming platforms (Netflix, Amazon Prime, YouTube), theatrical exhibition, and social media platforms.

### 1.1 SubRip (.SRT)
- **Standard:** De facto consumer and web standard. Plain text with sequential numeric index, comma-separated millisecond timestamps (`HH:MM:SS,mmm --> HH:MM:SS,mmm`), and text payload.
- **Support:** Limited inline formatting (`<i>`, `<b>`, `<u>`, `<font color>`).
- **Use Case:** YouTube, basic video players, social media uploads.

### 1.2 WebVTT (.VTT)
- **Standard:** W3C Web Video Text Tracks format for HTML5 `<track>`.
- **Key Features:** Dot-separated milliseconds (`HH:MM:SS.mmm`), header tags (`WEBVTT`), cue settings for position (`line:10%`, `position:50%`, `align:middle`), voice tags (`<v SpeakerName>`), and CSS styling (`::cue`).
- **Use Case:** Web browsers, HLS / DASH streaming video players.

### 1.3 Advanced SubStation Alpha (.ASS / .SSA)
- **Standard:** De facto standard for anime, karaoke, and precision typographical styling.
- **Key Features:** Complete coordinate-based positioning (`\pos(x,y)`), arbitrary font styling, drop shadows, borders, margins, color gradients, and per-syllable karaoke tags (`\k<duration>`).
- **Use Case:** Animated subtitles, social media highlight animations (TikTok/Reels/Shorts), anime subbing.

### 1.4 Timed Text Markup Language (TTML1 / TTML2) & IMSC 1.1
- **Standard:** W3C Recommendation; foundation for SMPTE-TT, EBU-TT-D, and Netflix TTML specs.
- **Key Features:** XML schema supporting precise frame-accurate timebases, regions, cell resolutions, styling blocks, and accessibility metadata.
- **Use Case:** High-end OTT delivery (Netflix, Disney+, Apple TV+).

### 1.5 Subtitles for the Deaf and Hard of Hearing (SDH) & Closed Captions (CEA-608 / CEA-708)
- Requires explicit transcription of non-speech audio events enclosed in brackets or parentheses:
  - Sound effects: `[dramatic violin swell]`, `[glass shatters]`, `[heavy footsteps approach]`
  - Music cues: `♪ energetic synthpop ♪`
  - Speaker identification tags when off-screen: `NARRATOR (V.O.): ...`

## 2. Broadcast & Streaming Subtitle Standards Matrix

| Guideline Parameter | Netflix Standard | BBC / EBU Standard | YouTube / Social Media Standard |
| :--- | :--- | :--- | :--- |
| **Max Characters Per Line (CPL)** | 42 characters (Latin) / 16 (CJK) | 37 characters | 32–36 characters |
| **Max Lines Per Event** | 2 lines | 2 lines | 1–2 lines (large font for mobile) |
| **Min Duration Per Cue** | 5/6 of a second (20 frames @ 24fps) | 1.0 second | 0.8 seconds |
| **Max Duration Per Cue** | 7.0 seconds | 6.0 seconds | 5.0 seconds |
| **Max Reading Speed** | 17 characters/sec (Adults) / 13 (Kids) | 16–18 characters/sec | Up to 20 CPS (viral short clips) |
| **Frame Gap Between Cues** | Minimum 2 frames gap | Minimum 3 frames gap | 1–2 frames gap |
| **Screen Placement** | Bottom center; top if lower-third graphics | Bottom center or top | Center-weighted or bottom 20% safe zone |
