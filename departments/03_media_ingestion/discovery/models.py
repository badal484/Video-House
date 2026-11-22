"""
Data models for the External Creative Resource Discovery Subsystem.
Department: 03_media_ingestion/discovery
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResourceMediaType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    VECTOR = "vector"
    MODEL_3D = "model_3d"
    TEXTURE = "texture"


class LicenseCategory(str, Enum):
    PUBLIC_DOMAIN = "public_domain"
    CC0 = "cc0"
    CC_BY = "cc_by"
    CC_BY_SA = "cc_by_sa"
    COMMERCIAL_FREE = "commercial_free"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, lic_str: str) -> "LicenseCategory":
        if not lic_str:
            return cls.UNKNOWN
        l = lic_str.lower()
        if "cc0" in l or "zero" in l or "public domain" in l or "pd" in l:
            return cls.CC0
        if "cc-by-sa" in l or "cc by-sa" in l:
            return cls.CC_BY_SA
        if "cc-by" in l or "cc by" in l:
            return cls.CC_BY
        if "free" in l or "open" in l:
            return cls.COMMERCIAL_FREE
        return cls.RESTRICTED


class ResourceQuery(BaseModel):
    query: str
    media_type: ResourceMediaType = ResourceMediaType.VIDEO
    aspect_ratio: Optional[str] = None  # "9:16", "16:9", "1:1"
    min_width: Optional[int] = 1080
    min_height: Optional[int] = 720
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    license_filter: Optional[List[LicenseCategory]] = None
    semantic_tags: List[str] = Field(default_factory=list)
    limit: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceQuery":
        return cls.model_validate(data)


class DiscoveredAsset(BaseModel):
    asset_id: str
    provider: str
    title: str
    description: str = ""
    media_type: ResourceMediaType
    source_page_url: str
    download_url: str
    preview_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    fps: Optional[float] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    license_category: LicenseCategory = LicenseCategory.UNKNOWN
    license_name: str = "Unknown"
    author: str = "Unknown"
    attribution_text: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiscoveredAsset":
        return cls.model_validate(data)


class AssetEvaluationScore(BaseModel):
    asset_id: str
    semantic_score: float = Field(..., ge=0.0, le=1.0)
    technical_score: float = Field(..., ge=0.0, le=1.0)
    creative_score: float = Field(..., ge=0.0, le=1.0)
    legal_score: float = Field(..., ge=0.0, le=1.0)
    composite_score: float = Field(..., ge=0.0, le=1.0)
    ranking_reason: str = ""
    is_usable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetEvaluationScore":
        return cls.model_validate(data)


class DownloadResult(BaseModel):
    success: bool
    asset_id: str
    local_path: Optional[str] = None
    byte_size: int = 0
    sha256_checksum: Optional[str] = None
    elapsed_seconds: float = 0.0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DownloadResult":
        return cls.model_validate(data)


class AssetResearchPlanItem(BaseModel):
    scene_index: int
    scene_title: str
    scene_duration_seconds: float
    intent: str
    required_media_type: ResourceMediaType
    queries: List[str]
    taxonomic_terms: List[str] = Field(default_factory=list)
    preferred_framing: str = "close_up"  # "macro", "close_up", "wide", "cutaway"
    technical_constraints: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetResearchPlanItem":
        return cls.model_validate(data)


class AssetResearchPlan(BaseModel):
    project_id: str
    title: str
    style_direction: str
    target_aspect_ratio: str = "9:16"
    target_fps: float = 30.0
    total_scenes: int
    items: List[AssetResearchPlanItem]

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetResearchPlan":
        return cls.model_validate(data)
