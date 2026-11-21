# Voice Generation, Dubbing & Speech Synthesis
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production & 17_subtitles_dubbing  
**Document:** VOICE_GENERATION.md  
**Version:** 1.0.0  

---

## 1. Subsystem Architecture

The voice generation subsystem provides automated voiceover, character narration, and multilingual dubbing integrated with the AI Director (Department 04) and Subtitles & Dubbing (Department 17).

```
Creative Script / Dialogue Line
       │
       ▼
[Voice Engine Router]
       ├──> Local Kokoro-82M (Ultra-fast, zero cloud cost, Apache 2.0)
       ├──> Cloud ElevenLabs Turbo (High-emotional expressiveness)
       └──> Scratch TTS (Edge-TTS / espeak for rapid prototyping)
       │
       ▼
[Audio Post-Processing]
       ├──> Room Tone Matching (Acoustic matching to scene environment)
       ├──> Conformance Resampling to 48 kHz 32-bit Float
       └──> Lip-Sync Timestamp Alignment (Phoneme markers)
       │
       ▼
AudioTrack (TrackType: VOICE_OVER / DIALOGUE)
```

---

## 2. Multilingual Dubbing & Accent Support

Department 17 supports seamless language translation and dubbing:
- **Hindi & English Primary Targets**: Native phoneme preservation for Indian and Western accents.
- **Duration Matching (Time Fitting)**: Translated dialogue often takes more or fewer syllables than the original video take. The engine calculates duration differential $\Delta t$ and applies pitch-preserving time stretching ($\pm 15\%$) to match visual actor cuts.
- **Pacing Control**: Dynamic punctuation pauses ($250\text{ ms}$ for commas, $600\text{ ms}$ for periods) inserted programmatically.

---

## 3. Character Consistency & Emotional Directives

Voice profiles are defined in `VoiceProfile` schemas:
- `timbre`: Pitch offset, formants, warmth, breathiness.
- `emotion`: `NEUTRAL`, `EXCITED`, `WHISPER`, `DRAMATIC`, `ANGRY`, `CONTEMPLATIVE`.
- `speaking_rate`: Speed multiplier ($0.8\times$ to $1.3\times$).
- Integrates with Department 12 (`character_production`) so character voices persist across scenes and episodes.
