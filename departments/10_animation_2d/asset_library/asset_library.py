"""
Animation Asset Library
Manages reusable 2D animation assets: character rigs, poses, expressions,
motion clips, multiplane backgrounds, and props with versioning and licensing.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class AssetCategory(str, Enum):
    CHARACTER_RIG = "CHARACTER_RIG"
    POSE = "POSE"
    EXPRESSION = "EXPRESSION"
    ANIMATION_CLIP = "ANIMATION_CLIP"
    BACKGROUND = "BACKGROUND"
    PROP = "PROP"
    COLOR_PALETTE = "COLOR_PALETTE"


@dataclass
class AnimationAsset:
    asset_id: str
    name: str
    category: AssetCategory
    version: str = "1.0.0"
    license_type: str = "PROPRIETARY_STUDIO"
    data: Dict[str, Any] = field(default_factory=dict)
    preview_path: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "category": self.category.value,
            "version": self.version,
            "license_type": self.license_type,
            "data": self.data,
            "preview_path": self.preview_path,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationAsset":
        return cls(
            asset_id=data["asset_id"],
            name=data["name"],
            category=AssetCategory(data["category"]),
            version=data.get("version", "1.0.0"),
            license_type=data.get("license_type", "PROPRIETARY_STUDIO"),
            data=data.get("data", {}),
            preview_path=data.get("preview_path"),
            tags=data.get("tags", []),
        )


class AnimationAssetLibrary:
    """
    Central catalog storing and retrieving reusable animation assets.
    """

    def __init__(self):
        self._assets: Dict[str, AnimationAsset] = {}

    def register_asset(self, asset: AnimationAsset) -> str:
        self._assets[asset.asset_id] = asset
        return asset.asset_id

    def get_asset(self, asset_id: str) -> Optional[AnimationAsset]:
        return self._assets.get(asset_id)

    def list_by_category(self, category: AssetCategory) -> List[AnimationAsset]:
        return [a for a in self._assets.values() if a.category == category]

    def search_assets(self, query: str) -> List[AnimationAsset]:
        q = query.lower()
        return [
            a for a in self._assets.values()
            if q in a.name.lower() or any(q in t.lower() for t in a.tags)
        ]
