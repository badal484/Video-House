"""
Character & Environment Reference Profiles
Department 15: 15_ai_generation
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CharacterReferenceProfile(BaseModel):
    """Reusable character identity definition to enforce consistency across scenes and shots."""
    character_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    name: str
    gender: Optional[str] = None
    apparent_age: Optional[int] = None
    face_reference_asset_ids: List[str] = Field(default_factory=list)
    turnaround_sheet_asset_ids: List[str] = Field(default_factory=list)
    body_proportions: Dict[str, float] = Field(default_factory=dict)  # height_cm, head_to_body_ratio
    hairstyle: str = "short dark hair"
    clothing: str = "signature outfit"
    accessories: List[str] = Field(default_factory=list)
    color_palette: List[str] = Field(default_factory=list)
    distinguishing_features: List[str] = Field(default_factory=list)  # scars, tattoos, birthmarks
    style_description: str = "photorealistic cinematic"
    negative_identity_prompt: str = "distorted face, different eye color, altered age"
    approved_output_asset_ids: List[str] = Field(default_factory=list)
    known_limitations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CharacterReferenceProfile:
        return cls(**data)


class EnvironmentReferenceProfile(BaseModel):
    """Reusable environment and scene architecture reference."""
    environment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    name: str
    reference_image_asset_ids: List[str] = Field(default_factory=list)
    architecture_style: str = "modern industrial"
    lighting_profile: str = "volumetric soft backlight"
    color_palette: List[str] = Field(default_factory=list)
    spatial_continuity_notes: str = ""
    time_of_day: str = "dusk"
    weather: str = "clear"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EnvironmentReferenceProfile:
        return cls(**data)
