"""
Sound FX Library Catalog & Semantic Search
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SFXAssetMetadata(BaseModel):
    sfx_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # IMPACT, WHOOSH, RISER, FOLEY, AMBIENCE, TRANSITION
    tags: List[str] = Field(default_factory=list)
    duration_sec: float
    file_path: Optional[str] = None
    frequency_profile: str = "FULL_RANGE"  # SUB_HEAVY, MID_PRESENCE, AIR, HIGH_PASS
    commercial_cleared: bool = True


class SoundLibrary:
    """Catalog of audio effects and Foley assets."""

    def __init__(self):
        self._assets: Dict[str, SFXAssetMetadata] = {}

    def register_sfx(self, metadata: SFXAssetMetadata) -> None:
        self._assets[metadata.sfx_id] = metadata

    def get_sfx(self, sfx_id: str) -> Optional[SFXAssetMetadata]:
        return self._assets.get(sfx_id)

    def search(
        self,
        query: str = "",
        category: Optional[str] = None,
        max_duration_sec: Optional[float] = None,
    ) -> List[SFXAssetMetadata]:
        """Filters catalog by tags, query string, category, and duration."""
        results = []
        tokens = query.lower().split() if query else []
        for asset in self._assets.values():
            if category and asset.category.lower() != category.lower():
                continue
            if max_duration_sec and asset.duration_sec > max_duration_sec:
                continue
            if tokens:
                text_to_search = f"{asset.name.lower()} {' '.join(asset.tags).lower()}"
                if not all(tok in text_to_search for tok in tokens):
                    continue
            results.append(asset)
        return results
