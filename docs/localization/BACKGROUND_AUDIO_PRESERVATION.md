# Background Audio & Ambience Preservation Specification

## 1. The Challenge of Clean Voice Replacement
Naive dubbing overlays synthesized dialogue on top of the original mixed audio track, creating muddy speech clashing with the original voice, or completely removes all audio, replacing it with a sterile voice track stripped of background score, room echo, footsteps, and sound effects.

## 2. Department 10 DSP Bridge Architecture
The `AudioProductionBridge` integrates Department 17 with Department 14/10 to execute professional stem preservation:

```
Original Audio Track
        │
        ▼
[Demucs HTDemucs v4 Demixing]
        ├───► [Original Vocals Stem] ──► (Discarded or ducked to -40dB for guide)
        ├───► [Bass Stem]
        ├───► [Drums Stem]          ──► [Preserved Music & Foley Bed]
        └───► [Other / Ambience Stem]
                     │
                     ▼
             [Sidechain Dynamic Ducking]
             - Ingests new Dubbed Speech Stem
             - Ducks Music & Ambience by -3.5dB to -6.0dB during speech utterances
             - Release time: 250ms smooth curve
                     │
                     ▼
             [Final Mixed Multilingual Audio Master]
```

## 3. Acoustic Environment Conformance
- **Reverberation Profiling:** The original acoustic space is matched using convolutional impulse response parameters extracted by the media intelligence layer.
- **Microphone Distance & Proximity Filter:** High-frequency rolloff and gentle low-frequency proximity shelf are applied to make synthetic studio speech sound like on-set boom or lavalier recording.
