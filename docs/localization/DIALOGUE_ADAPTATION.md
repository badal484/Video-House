# Dialogue Adaptation & Timing Specification

## 1. The Pacing & Timecode Challenge
Different languages express the same semantic concept with radically different syllable counts. For example:
- English: *"Are you coming with us tomorrow?"* (9 syllables, ~1.8 seconds)
- German: *"Kommst du morgen mit uns mit?"* (7 syllables, ~1.6 seconds)
- Spanish: *"¿Vienes con nosotros mañana?"* (10 syllables, ~2.1 seconds)
- Hindi: *"क्या तुम कल हमारे साथ आ रहे हो?"* (13 syllables, ~2.5 seconds)

If a direct translation is synthesized blindly into the original 1.8-second audio slot, the voice synthesizer must speed up to an unnatural $1.4\times$ rate, making the speech sound frantic, robotic, and unlistenable.

## 2. Adaptation Techniques & Constraints
The `DialogueAdapter` applies algorithmic adaptation to solve this isochronic tension:
1. **Syllable Counting & Duration Estimation:**
   - Evaluates source syllable count $S_{src}$ and target syllable count $S_{tgt}$.
   - Estimates standard phonetic speaking rate (typically 4.0–4.8 syllables/second for standard conversational speech).
2. **Expansion / Condensation Strategies:**
   - **When Target is Too Long ($T_{tgt} > 1.15 \times T_{src}$):**
     - Prunes redundant polite words or filler particles.
     - Replaces lengthy multi-word phrases with concise equivalents (e.g., in Hindi, contracting phrases without losing core meaning).
     - Identifies surrounding video pauses (pre-speech pause, post-speech pause) to safely expand the audio slot into empty gaps without colliding with adjacent dialogue.
   - **When Target is Too Short ($T_{tgt} < 0.85 \times T_{src}$):**
     - Expands phrasing naturally, adding conversational descriptors or slowing down vowel durations within pleasant prosodic bounds ($0.9\times$ normal rate).
3. **Safety Speed Thresholds:**
   - Speech tempo changes are bounded strictly between $0.90\times$ (slight slow-down) and $1.15\times$ (slight speed-up). Any adaptation requiring tempo outside this range triggers automatic textual re-phrasing.
