"""
Data Models for YouTube & Online Media Research, Import, and Reference Analysis.
Department: 03_media_ingestion/online_media
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MediaPermissionTier(str, Enum):
    REFERENCE_ONLY = "reference_only"                    # Watching & structural analysis only; cannot be cut into output edit
    EDITING_PERMITTED = "editing_permitted"              # Licensed or authorized for editorial cutting and derivative use
    COMMERCIAL_PERMITTED = "commercial_permitted"        # Fully cleared for commercial distribution (CC0, public domain, user-owned)
    REQUIRES_PERMISSION = "requires_permission"          # Standard copyright / creator permission required before use
    LICENSE_UNKNOWN = "license_unknown"                  # License or origin unverified; treated as reference-only by default


class PermissionDeclaration(str, Enum):
    USER_OWNED = "user_owned"                            # Media is 100% owned/created by user
    CREATOR_AUTHORIZED = "creator_authorized"            # Direct written consent / authorization from rights holder
    CREATIVE_COMMONS = "creative_commons"                # Published under an open CC license (CC-BY, CC-BY-SA, CC0)
    PUBLIC_DOMAIN = "public_domain"                      # Media in public domain
    REFERENCE_ONLY = "reference_only"                    # Strictly for research, viewing and reference analysis; no production use


class OnlineMediaSourceType(str, Enum):
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    WEB_STREAM = "web_stream"
    USER_UPLOAD = "user_upload"
    STOCK_LIBRARY = "stock_library"


class OnlineVideoChapter(BaseModel):
    title: str
    start_time_seconds: float
    end_time_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class OnlineVideoSubtitleInfo(BaseModel):
    language_code: str
    language_name: str
    is_automatic: bool = False
    format_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class OnlineVideoMetadata(BaseModel):
    video_id: str
    url: str
    title: str
    description: str = ""
    author: str = "Unknown"
    channel_id: Optional[str] = None
    channel_url: Optional[str] = None
    duration_seconds: float = 0.0
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    available_resolutions: List[str] = Field(default_factory=list)
    available_audio_formats: List[str] = Field(default_factory=list)
    chapters: List[OnlineVideoChapter] = Field(default_factory=list)
    subtitles_available: List[OnlineVideoSubtitleInfo] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_embeddable: bool = True
    is_download_permitted: bool = False
    permission_tier: MediaPermissionTier = MediaPermissionTier.REFERENCE_ONLY
    embed_html: Optional[str] = None
    source_type: OnlineMediaSourceType = OnlineMediaSourceType.YOUTUBE

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OnlineVideoMetadata":
        return cls.model_validate(data)


class OnlineMediaSearchQuery(BaseModel):
    query: str
    limit: int = 10
    channel: Optional[str] = None
    min_duration_sec: Optional[float] = None
    max_duration_sec: Optional[float] = None
    order_by: str = "relevance"  # "relevance", "view_count", "date"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class MediaImportRequest(BaseModel):
    url: str
    media_type: str = "video"                           # "video" or "audio_only"
    resolution: str = "1080p"                           # "1080p", "720p", "480p", "best"
    audio_format: str = "wav"                           # "wav", "mp3", "flac", "aac", "m4a"
    permission_declaration: PermissionDeclaration = PermissionDeclaration.REFERENCE_ONLY
    permission_notes: Optional[str] = None
    destination_role: str = "REFERENCE_VIDEO"           # "REFERENCE_VIDEO", "REFERENCE_AUDIO", "SOURCE_FOOTAGE", "MUSIC"
    project_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class MediaImportProgress(BaseModel):
    status: str = "pending"                             # "pending", "downloading", "extracting_audio", "verifying", "completed", "failed", "cancelled"
    progress_pct: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_str: str = ""
    eta_seconds: Optional[float] = None
    error_message: Optional[str] = None
    asset_id: Optional[str] = None
    local_path: Optional[str] = None
    permission_tier: MediaPermissionTier = MediaPermissionTier.REFERENCE_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class AudioExtractionRequest(BaseModel):
    source_asset_id: Optional[str] = None
    source_file_path: Optional[str] = None
    output_format: str = "wav"                          # "wav", "flac", "mp3", "aac"
    sample_rate: int = 48000
    channels: int = 2
    project_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class AudioAnalysisReport(BaseModel):
    duration_seconds: float
    sample_rate: int
    channels: int
    integrated_lufs: float                              # EBU R128 loudness (e.g. -14.0 LUFS)
    peak_dbfs: float
    dynamic_range_db: float
    waveform_peaks: List[float] = Field(default_factory=list)  # Normalized 0.0-1.0 amplitude peaks for UI
    speech_energy_ratio: float = 0.0                    # Fraction of energy in speech band (300Hz-3.4kHz)
    music_energy_ratio: float = 0.0                     # Fraction of energy in harmonic music band
    estimated_bpm: Optional[float] = None
    stem_separation_notes: str = "Source separation provides indicative energy analysis and does not perfectly isolate original studio stems."

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ReferenceComparisonReport(BaseModel):
    compared_profiles: List[str]                        # Profile IDs or names
    average_shot_lengths: Dict[str, float]              # ASL per reference
    pacing_comparison: Dict[str, str]                   # FAST, MODERATE, SLOW per reference
    palette_similarity_score: float                     # 0.0 to 1.0 color overlap
    common_camera_motions: List[str]                    # Frequent camera motions across references
    editing_recommendation: str                         # AI recommendation for original production

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

