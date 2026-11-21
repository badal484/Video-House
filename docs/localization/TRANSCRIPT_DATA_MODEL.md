# Transcript Data Model Specification

## 1. Domain Object Hierarchy
Localization data is represented using strongly-typed Pydantic v2 models that maintain sub-second rational timestamps, phoneme breakdowns, speaker metadata, and multi-version edit histories.

```
Transcript
 ├── transcript_id: UUID
 ├── project_id: UUID
 ├── media_asset_id: UUID
 ├── language_code: str (ISO-639-1)
 ├── creation_timestamp: datetime
 ├── segments: List[TranscriptSegment]
 │    ├── segment_id: UUID
 │    ├── start_time: RationalTime (or seconds float)
 │    ├── end_time: RationalTime
 │    ├── text: str
 │    ├── speaker_id: str
 │    ├── words: List[WordTimestamp]
 │    │    ├── word: str
 │    │    ├── start_time: float
 │    │    ├── end_time: float
 │    │    ├── confidence: float
 │    │    └── phonemes: Optional[List[str]]
 │    ├── confidence: float
 │    ├── is_manual_edit: bool
 │    └── translation_history: Dict[str, str]
 └── speakers: List[SpeakerRecord]
      ├── speaker_id: str
      ├── label: str
      ├── gender: str
      ├── voice_profile_id: Optional[str]
      └── biometric_consent_id: Optional[str]
```

## 2. Rational Time Representation
To maintain parity with Department 05 (`video_editing`), timestamps can be represented both as float seconds for fast serializations and as `RationalTime(value, rate)` for editorial assemblies. This completely avoids non-integer frame boundary slips (e.g., 29.97 drop-frame timecode offsets).

## 3. Change Tracking & Manual Overrides
Every `TranscriptSegment` contains an audit trail:
- `original_text`: The raw ASR hypothesis.
- `edited_text`: Human-reviewed or post-processed text.
- `edit_author`: User ID or agent name.
- `confidence`: Calibrated confidence metric between 0.0 and 1.0.
