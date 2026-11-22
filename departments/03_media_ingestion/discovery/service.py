"""
Discovery & Creative Resource Intelligence Service.
Department: 03_media_ingestion/discovery
"""
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from core.assets.database import AssetDatabase
from .acquisition import AssetAcquisitionService
from .evaluator import AssetEvaluator
from .models import (
    AssetEvaluationScore, AssetResearchPlan, DiscoveredAsset, DownloadResult, ResourceQuery
)
from .providers.base import BaseResourceProvider
from .providers.nasa_noaa import NasaNoaaProvider
from .providers.openverse import OpenverseProvider
from .providers.wikimedia import WikimediaCommonsProvider


class CreativeResourceDiscoveryService:
    """
    Central orchestration service for external creative resource intelligence.
    Funnels queries across all enabled providers, ranks candidates multi-dimensionally,
    and coordinates reliable acquisition and provenance verification.
    """

    def __init__(self, db: Optional[AssetDatabase] = None):
        self.db = db or AssetDatabase()
        self.evaluator = AssetEvaluator()
        self.acquisition = AssetAcquisitionService(db=self.db)
        self.providers: Dict[str, BaseResourceProvider] = {
            "wikimedia": WikimediaCommonsProvider(),
            "openverse": OpenverseProvider(),
            "nasa_noaa": NasaNoaaProvider()
        }

    def search_multi_provider(
        self,
        query: ResourceQuery,
        provider_keys: Optional[List[str]] = None
    ) -> List[Tuple[DiscoveredAsset, AssetEvaluationScore]]:
        """
        Fans out search across providers, aggregates results, and ranks them intelligently.
        """
        targets = provider_keys or list(self.providers.keys())
        all_candidates: List[DiscoveredAsset] = []

        for key in targets:
            provider = self.providers.get(key)
            if provider and provider.is_enabled:
                try:
                    results = provider.search(query)
                    all_candidates.extend(results)
                except Exception:
                    pass

        return self.evaluator.rank_candidates(all_candidates, query)

    def execute_plan_acquisition(
        self,
        plan: AssetResearchPlan,
        project_id: UUID,
        max_assets_per_scene: int = 1
    ) -> Dict[int, List[DownloadResult]]:
        """
        Executes an AI Creative Research Plan: searches, ranks, and acquires the top
        candidate for each scene in the plan.
        """
        results_by_scene: Dict[int, List[DownloadResult]] = {}

        for item in plan.items:
            acquired: List[DownloadResult] = []
            for q_str in item.queries[:2]:  # Try top 2 query formulations
                query = ResourceQuery(
                    query=q_str,
                    media_type=item.required_media_type,
                    aspect_ratio=plan.target_aspect_ratio,
                    semantic_tags=item.taxonomic_terms,
                    limit=5
                )
                ranked = self.search_multi_provider(query)
                for candidate, score in ranked:
                    if score.is_usable and score.composite_score >= 0.65:
                        res = self.acquisition.acquire_asset(candidate, project_id=project_id)
                        if res.success:
                            acquired.append(res)
                            break
                if len(acquired) >= max_assets_per_scene:
                    break
            results_by_scene[item.scene_index] = acquired

        return results_by_scene
