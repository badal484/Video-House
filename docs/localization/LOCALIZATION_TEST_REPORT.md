# Localization Studio Test Report & Verification

## 1. Test Suite Architecture
The test suite in `tests/unit/test_subtitles_dubbing.py` provides end-to-end verification of Department 17's components, honoring the 28 core acceptance criteria:
1. Pydantic v2 domain schemas validation (`Transcript`, `TranscriptSegment`, `WordTimestamp`, etc.).
2. Multilingual ASR and word timestamp alignment.
3. Indic language (Hindi, Tamil, Telugu) and Hinglish code-switching handling.
4. Diarization speaker assignment and clustering.
5. Contextual translation with glossary preservation.
6. Dialogue syllable adaptation and time budget matching.
7. Subtitle cue segmentation, line wrapping, and CPS audit.
8. Subtitle format export: SRT, WebVTT, ASS/SSA, and TTML.
9. Social media kinetic & karaoke subtitle styling.
10. Voice talent casting and acoustic profiling.
11. Biometric voice consent verification and authorization enforcement.
12. Multi-language dubbing orchestration.
13. Background audio preservation via Department 10 DSP integration.
14. Lip-sync provider routing and commercial license validation.
15. Rational timecode synchronization and clock drift elimination.
16. Automated Quality Control (CPS, loudness, clipping, sync checks).
17. OpenTimelineIO subtitle track bridging.
18. Asset registry persistence and derivative linking.

## 2. Test Execution Baseline
- **Platform:** macOS Sonoma, Apple M4, 16GB RAM.
- **Python:** 3.11.
- **Target Pass Rate:** 100% pass across all Department 17 unit tests without regressions to prior 151 studio tests.
