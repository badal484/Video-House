"""
Domain models for Department 17: Subtitles, Dubbing & Localization.
Strongly typed Pydantic v2 schemas honoring zero-drift rational time and broadcast standards.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class SubtitleFormat(str, enum.Enum):
    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"
    TTML = "ttml"
    JSON = "json"


class SubtitleStylePreset(str, enum.Enum):
    CINEMATIC = "cinematic"
    SOCIAL_KINETIC = "social_kinetic"
    SDH_HIGH_CONTRAST = "sdh_high_contrast"
    ANIME = "anime"
    MINIMAL_LOWER = "minimal_lower"


class WordTimestamp(BaseModel):
    word: str = Field(..., description="Spoken word or lexical token")
    start_time: float = Field(..., ge=0.0, description="Start offset in seconds")
    end_time: float = Field(..., ge=0.0, description="End offset in seconds")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Acoustic alignment confidence")
    phonemes: Optional[List[str]] = Field(default=None, description="Optional phonetic transcription (IPA or ARPAbet)")


class TranscriptSegment(BaseModel):
    segment_id: UUID = Field(default_factory=uuid4, description="Unique segment identifier")
    start_time: float = Field(..., ge=0.0, description="Start offset in seconds")
    end_time: float = Field(..., ge=0.0, description="End offset in seconds")
    text: str = Field(..., description="Transcript text")
    original_text: Optional[str] = Field(default=None, description="Original unedited text")
    speaker_id: str = Field(default="speaker_0", description="Assigned speaker ID")
    words: List[WordTimestamp] = Field(default_factory=list, description="Word-level timestamps")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall segment confidence")
    is_manual_edit: bool = Field(default=False, description="Flag indicating human or post-processed correction")
    translation_history: Dict[str, str] = Field(default_factory=dict, description="Cache of translations by language code")


class SpeakerRecord(BaseModel):
    speaker_id: str = Field(..., description="Speaker identifier (e.g. speaker_0)")
    label: str = Field(default="Narrator", description="Human-readable character or talent name")
    gender: str = Field(default="unknown", description="Estimated or assigned gender (male, female, neutral)")
    pitch_hz: Optional[float] = Field(default=None, description="Estimated average fundamental frequency F0")
    voice_profile_id: Optional[str] = Field(default=None, description="Associated neural voice profile ID")
    biometric_consent_id: Optional[UUID] = Field(default=None, description="Linked BiometricConsentRecord UUID")


class Transcript(BaseModel):
    transcript_id: UUID = Field(default_factory=uuid4, description="Unique transcript UUID")
    project_id: UUID = Field(..., description="Target project UUID")
    media_asset_id: UUID = Field(..., description="Source media asset UUID")
    language_code: str = Field(default="en", description="ISO 639-1 language code (e.g. en, hi, es, fr)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    segments: List[TranscriptSegment] = Field(default_factory=list, description="Ordered speech segments")
    speakers: List[SpeakerRecord] = Field(default_factory=list, description="Active speaker profiles")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="ASR model, engine version, and parameters")


class GlossaryTerm(BaseModel):
    term_id: UUID = Field(default_factory=uuid4)
    source_term: str = Field(..., description="Source keyword or phrase")
    target_term: str = Field(..., description="Mandatory translation in target language")
    source_language: str = Field(default="en")
    target_language: str = Field(..., description="Target language code (e.g. hi, es, de)")
    case_sensitive: bool = Field(default=False)
    notes: Optional[str] = Field(default=None, description="Contextual disambiguation notes")


class TranslationRecord(BaseModel):
    translation_id: UUID = Field(default_factory=uuid4)
    source_segment_id: UUID = Field(..., description="Referenced source TranscriptSegment UUID")
    source_language: str = Field(...)
    target_language: str = Field(...)
    source_text: str = Field(...)
    translated_text: str = Field(...)
    adapted_text: Optional[str] = Field(default=None, description="Isochronically adapted dialogue for dubbing")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    glossary_terms_preserved: List[str] = Field(default_factory=list)


class SubtitleCue(BaseModel):
    cue_index: int = Field(..., ge=1, description="Sequential cue number")
    start_time: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end_time: float = Field(..., ge=0.0, description="End timestamp in seconds")
    text: str = Field(..., description="Formatted subtitle text (max 2 lines)")
    speaker_id: Optional[str] = Field(default=None)
    style_override: Optional[Dict[str, Any]] = Field(default=None)


class SubtitleTrack(BaseModel):
    track_id: UUID = Field(default_factory=uuid4)
    project_id: UUID = Field(...)
    language_code: str = Field(default="en")
    format: SubtitleFormat = Field(default=SubtitleFormat.SRT)
    style_preset: SubtitleStylePreset = Field(default=SubtitleStylePreset.CINEMATIC)
    cues: List[SubtitleCue] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BiometricConsentRecord(BaseModel):
    consent_id: UUID = Field(default_factory=uuid4)
    talent_name: str = Field(..., description="Full legal name of the voice talent")
    voice_profile_id: str = Field(..., description="Identifier of the synthesized/cloned voice profile")
    is_authorized: bool = Field(default=True, description="Whether authorization is legally in good standing")
    authorized_purposes: List[str] = Field(default_factory=lambda: ["commercial", "dubbing", "localization"])
    territories: List[str] = Field(default_factory=lambda: ["worldwide"])
    expiry_date: Optional[str] = Field(default=None, description="ISO-8601 expiry date or None for perpetual")
    signature_hash: str = Field(default="sig_sha256_verified_token")


class DubbingJob(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    project_id: UUID = Field(...)
    source_transcript_id: UUID = Field(...)
    target_language: str = Field(...)
    voice_mappings: Dict[str, str] = Field(default_factory=dict, description="speaker_id -> voice_profile_id")
    status: str = Field(default="pending", description="pending, processing, completed, failed")
    output_audio_asset_id: Optional[UUID] = Field(default=None)
    preserve_background: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LipSyncJob(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    project_id: UUID = Field(...)
    video_asset_id: UUID = Field(...)
    audio_asset_id: UUID = Field(...)
    provider: str = Field(default="synclabs", description="synclabs, latentsync, musetalk")
    status: str = Field(default="pending")
    output_video_asset_id: Optional[UUID] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LocalizationQCReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    project_id: UUID = Field(...)
    passed: bool = Field(default=True)
    total_issues: int = Field(default=0)
    reading_speed_violations: int = Field(default=0)
    line_length_violations: int = Field(default=0)
    overlap_violations: int = Field(default=0)
    loudness_lufs: Optional[float] = Field(default=None)
    true_peak_db: Optional[float] = Field(default=None)
    sync_drift_ms: float = Field(default=0.0)
    details: List[str] = Field(default_factory=list)
    inspected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
