# Localization Studio Implementation Architecture

## 1. System Mission & Department Identity
Department 17 (`17_subtitles_dubbing`) is the definitive localization hub of the AI Video Production Studio. It accepts raw audio/video assets, timeline sequences, and multi-track compositions, transforming them into globally accessible, multilingual releases with frame-accurate subtitles, culturally faithful translations, voice-cloned dubbing, and lip-synchronized video tracks.

## 2. Directory Architecture & Subsystem Layout
```
departments/17_subtitles_dubbing/
├── __init__.py
├── interface.py                       # Department contract (ISubtitlesDubbing)
├── service.py                         # SubtitlesDubbingService facade
├── core/
│   ├── __init__.py
│   └── models.py                      # Pydantic v2 domain schemas
├── transcription/
│   ├── __init__.py
│   ├── asr_engine.py                  # WhisperX / Faster-Whisper wrapper
│   └── transcript_manager.py          # Segment splitting, confidence scoring, manual edits
├── translation/
│   ├── __init__.py
│   ├── translator.py                  # Multilingual LLM/NMT engine
│   └── glossary.py                    # Glossary term constraints & code-switch handler
├── adaptation/
│   ├── __init__.py
│   └── dialogue_adapter.py            # Syllable matching, speech rate & timing adaptation
├── subtitles/
│   ├── __init__.py
│   ├── generator.py                   # Subtitle cue segmenter (SRT, VTT, TTML, ASS)
│   └── styler.py                      # Font, color, karaoke, and safe-zone styling engine
├── voice/
│   ├── __init__.py
│   ├── voice_assigner.py              # Speaker profile matching & voice casting
│   └── consent_manager.py             # Biometric consent tokens & authorization check
├── dubbing/
│   ├── __init__.py
│   └── orchestrator.py                # End-to-end multi-language dubbing supervisor
├── lipsync/
│   ├── __init__.py
│   ├── lipsync_orchestrator.py        # Lip-sync router & face compositing pipeline
│   ├── sync_labs_adapter.py           # Sync Labs API client
│   └── local_lipsync_adapter.py       # LatentSync / MuseTalk adapter
├── sync/
│   ├── __init__.py
│   └── sync_manager.py                # Drift detection & rational timebase conformer
├── qc/
│   ├── __init__.py
│   └── quality_controller.py          # Subtitle CPS, audio clipping, sync QC validator
└── integrations/
    ├── __init__.py
    ├── timeline_subtitles_bridge.py   # Part 05 OpenTimelineIO subtitle track bridge
    ├── audio_production_bridge.py     # Part 10 DSP, stem mixing & ducking bridge
    ├── director_localization_bridge.py# Part 04 AI Director script context bridge
    └── asset_store_bridge.py          # Part 21 Common Asset Registry persistence
```

## 3. Department Interactions & Flow
- **Input:** Raw video asset or OTIO timeline containing dialogue clips.
- **Processing:**
  1. Extract audio stem via `AudioProductionBridge`.
  2. Transcribe & diarize speech via `TranscriptionManager`.
  3. Translate text with glossary preservation via `TranslationManager`.
  4. Adapt syllable pacing via `DialogueAdapter`.
  5. Generate standardized subtitles via `SubtitleGenerator`.
  6. Synthesize target dialogue stems via `DubbingOrchestrator` & `VoiceAssigner`.
  7. Apply video lip-sync via `LipSyncOrchestrator`.
  8. Validate quality constraints via `QualityController`.
- **Output:** Conformed OTIO timeline tracks, multi-language subtitle sidecars (`.srt`, `.vtt`, `.ass`, `.xml`), and localized video files registered in Department 21.
