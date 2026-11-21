# Dubbing Pipeline Specification

## 1. End-to-End Dubbing Architecture
The `DubbingOrchestrator` oversees the comprehensive voice dubbing lifecycle:

```
[Master Audio Stream]
         │
         ▼
[Department 10 Demucs Source Separation]
         │
         ├───► [Dialogue Stem (Isolated Original Speech)]
         └───► [Music & Ambience / Foley Stems]
                     │
                     ▼
             [Department 17 Pipeline]
             1. ASR & Word Alignment
             2. Diarization & Speaker Attribution
             3. Translation & Glossary Preservation
             4. Dialogue Syllable Adaptation
             5. Synthetic Speech Synthesis (ElevenLabs/Kokoro)
                     │
                     ▼
             [Raw Dubbed Dialogue Stem]
                     │
                     ▼
             [Department 10 DSP & Mixing Integration]
             1. Room Acoustic Convolution Reverb
             2. EQ Matching to Original Stems
             3. Sidechain Ducking against Music & Ambience
             4. EBU R128 Master Loudness Normalization (-23 LUFS / -14 LUFS)
                     │
                     ▼
             [Final Multilingual Master Audio Stem]
```

## 2. Multi-Language Dubbing Orchestration
- Supports concurrent generation of multiple language dubs (e.g. producing Spanish, French, German, and Hindi dubs in a single production pass).
- Each language track is generated as a discrete audio asset in Department 21, mapped into an OTIO multi-track audio structure.
