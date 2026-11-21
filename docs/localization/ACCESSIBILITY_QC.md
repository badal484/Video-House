# Accessibility & Quality Control (QC) Specification

## 1. Automated Localization Quality Control
The `LocalizationQualityController` runs deterministic rule-based checks on all transcripts, translations, subtitle tracks, dubbed audio, and lip-synced videos prior to final export approval.

## 2. QC Inspection Categories

### 2.1 Subtitle & Captioning QC
- **Reading Speed (CPS) Audit:** Flags any cue where characters-per-second exceeds 17 CPS (Adult) or 13 CPS (Children).
- **Line Length (CPL) Audit:** Flags cues exceeding 42 characters per line (Latin) or 16 (CJK).
- **Duration Audit:** Flags cues shorter than 0.83 seconds or longer than 6.0 seconds.
- **Overlapping Cues:** Flags any subtitle event whose start time precedes the prior cue's end time.
- **Shot Boundary Flash Audit:** Flags cues that start 1 frame before or after a scene cut, recommending alignment with the shot boundary.

### 2.2 Dubbed Audio QC
- **Loudness Compliance:** Verifies target dialogue meets EBU R128 (-23.0 LUFS $\pm 0.5$ LUFS for broadcast, -14.0 LUFS for YouTube/Spotify).
- **Peak Clipping Audit:** Flags true peak levels exceeding $-1.0 \text{ dBTP}$.
- **Signal-to-Noise & Bleed:** Checks that original foreign dialogue does not audibly leak through background ambience.

### 2.3 Lip-Sync QC
- **SyncNet Confidence Score:** Evaluates visual mouth motion against acoustic speech phonemes, flagging frames where confidence falls below $0.75$.
- **Artifact & Jitter Detection:** Analyzes boundary edge gradients around the mouth crop region to ensure seamless blending without edge seams or discoloration.
