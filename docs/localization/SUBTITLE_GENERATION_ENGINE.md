# Subtitle Generation Engine Specification

## 1. Subtitle Segmentation Rules & Architecture
The `SubtitleGenerator` ingests word-level timestamped transcripts and segments them into broadcast-compliant subtitle cues following global industry standards (Netflix, EBU, BBC).

### 1.1 Segmentation Algorithm
1. **Max Characters Per Line (CPL):**
   - Latin scripts: Max 37 to 42 characters per line.
   - Asian scripts (CJK): Max 16 characters per line.
   - Indic scripts: Max 36 characters per line.
2. **Line Breaking Rules:**
   - Never break a line across a hyphenated word.
   - Never break between a person's title and their surname (e.g., "Dr." and "Smith").
   - Break at natural linguistic syntactic boundaries: after punctuation (periods, commas, em dashes), before conjunctions ("and", "but", "because"), or between prepositional phrases.
3. **Max Lines Per Cue:**
   - Strict maximum of 2 lines per subtitle event.
4. **Duration Bounds:**
   - Minimum duration: $0.833$ seconds (20 frames at 24fps) to ensure readability.
   - Maximum duration: $6.0$ seconds to avoid stale on-screen text.
5. **Frame Gap Enforcer:**
   - Enforces a minimum gap of 2 to 3 frames between adjacent subtitle cues, preventing visual flicker caused by instant transitions.

## 2. Supported Export Formats
The engine natively serializes subtitle cues into:
- **SubRip (.srt):** Formatted with index, timecode strings, and clean line breaks.
- **WebVTT (.vtt):** With `WEBVTT` header, voice identifiers, and cue placement parameters.
- **Advanced SubStation Alpha (.ass):** With style script definitions, alignment codes, margin overrides, and drop shadows.
- **Timed Text Markup Language (TTML/IMSC 1.1):** Valid XML compliant with W3C and Netflix specifications.
