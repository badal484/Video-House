"""
External Creative Resource Discovery Subsystem.
Department: 03_media_ingestion/discovery
"""
from .acquisition import AssetAcquisitionService
from .evaluator import AssetEvaluator
from .models import (
    AssetEvaluationScore, AssetResearchPlan, AssetResearchPlanItem,
    DiscoveredAsset, DownloadResult, LicenseCategory, ResourceMediaType, ResourceQuery
)
from .service import CreativeResourceDiscoveryService

__all__ = [
    "CreativeResourceDiscoveryService",
    "AssetAcquisitionService",
    "AssetEvaluator",
    "DiscoveredAsset",
    "ResourceQuery",
    "ResourceMediaType",
    "LicenseCategory",
    "AssetEvaluationScore",
    "DownloadResult",
    "AssetResearchPlan",
    "AssetResearchPlanItem"
]
