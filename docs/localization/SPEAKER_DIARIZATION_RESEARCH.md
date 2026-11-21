# Speaker Diarization & Word Alignment Research

## 1. The Challenge of "Who Spoke When" in Video Localization
Video localization requires precise speaker attribution. Assigning an utterance to the wrong speaker results in:
1. Incorrect subtitle placement (left/right screen positioning, distinct speaker colors).
2. Catastrophic dubbing failure (wrong voice synthesis model, gender mismatch, unnatural tone).
3. Incorrect visual targeting for face-tracking lip-synchronization.

## 2. Diarization Architectures

### 2.1 pyannote.audio 3.1
- **Architecture:** End-to-end neural speaker diarization (segmentation transformer + speaker embeddings via ECAPA-TDNN or WeSpeaker).
- **Performance:** Diarization Error Rate (DER) < 11.5% on VoxConverse; handles speaker overlaps robustly.
- **Licensing:** MIT license for code; Hugging Face gated models (Hugging Face user token required for weight download).
- **Local Mac Footprint:** Runs on PyTorch MPS/CPU with ~1.1GB RAM.

### 2.2 WhisperX Integrated Diarization
- WhisperX bundles `pyannote.audio` speaker clustering with word-level forced alignment.
- Each word output contains `(start, end, word, score, speaker_id)`.
- Overlapping speech is resolved by assigning words based on spectral overlap and phoneme likelihood.

### 2.3 Visual-Audio Active Speaker Detection (ASD)
- In cinematic and multi-person scenes, purely acoustic diarization cannot distinguish between off-screen narration and on-screen dialogue.
- Active Speaker Detection integrates face bounding boxes (MediaPipe / RetinaFace) and lip motion optical flow (or TalkNet architecture) with acoustic energy to verify which actor's mouth is moving at timestamp $t$.

## 3. Word-Level Forced Alignment Mechanics
Forced alignment matches the phonetic transcription to the raw audio waveform:
1. **Phonemizer:** Converts text into phoneme sequences (e.g. CMU Pronouncing Dictionary for English, Epitran for multilingual).
2. **Acoustic Model:** A pre-trained Wav2Vec2 or CTC model predicts emission probabilities across time frames (typically 20ms or 50Hz).
3. **Dynamic Programming / Viterbi Trellis:** Determines the optimal alignment path that matches phonemes to frame emissions, yielding exact start and end timestamps for every single character and word.

```
Audio Frame:   [f0]   [f1]   [f2]   [f3]   [f4]   [f5]   [f6]   [f7]
Phonemes:      /h/    /h/    /e/    /l/    /l/    /o/    /o/    <sil>
Word Span:     |------------ "hello" -------------|
```

## 4. Architectural Implementation in Department 17
- The `SpeakerDiarizer` and `AlignmentEngine` provide a unified interface.
- Output records adhere to standard Pydantic models with `speaker_id`, `gender_estimate`, `pitch_range`, and `confidence_score`.
- Downstream modules (voice casting, subtitle styling, lip-sync targeting) consume these records directly.
