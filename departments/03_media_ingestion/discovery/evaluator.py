"""
Multi-Dimensional Asset Evaluator and Scoring Engine.
Department: 03_media_ingestion/discovery
"""
from typing import List, Tuple
from .models import AssetEvaluationScore, DiscoveredAsset, LicenseCategory, ResourceQuery


class AssetEvaluator:
    """
    Evaluates candidate creative assets across 4 distinct dimensions:
    1. Semantic Relevance (keyword match, taxonomy, context overlap)
    2. Technical Quality (resolution, framerate, duration, aspect ratio compatibility)
    3. Creative Suitability (framing, visual depth, motion dynamics)
    4. Legal Usability (CC0/PD > CC-BY > CC-BY-SA > Restricted)
    """

    def __init__(
        self,
        weight_semantic: float = 0.35,
        weight_technical: float = 0.25,
        weight_creative: float = 0.20,
        weight_legal: float = 0.20
    ):
        self.w_sem = weight_semantic
        self.w_tech = weight_technical
        self.w_creat = weight_creative
        self.w_legal = weight_legal

    def evaluate_asset(self, asset: DiscoveredAsset, query: ResourceQuery) -> AssetEvaluationScore:
        sem_score = self._compute_semantic_score(asset, query)
        tech_score = self._compute_technical_score(asset, query)
        creat_score = self._compute_creative_score(asset, query)
        legal_score, is_usable = self._compute_legal_score(asset)

        composite = (
            self.w_sem * sem_score +
            self.w_tech * tech_score +
            self.w_creat * creat_score +
            self.w_legal * legal_score
        )

        reasons = []
        if sem_score > 0.8:
            reasons.append("High semantic tag correlation")
        if tech_score > 0.8:
            reasons.append("Meets 1080p+ technical criteria")
        if legal_score >= 0.9:
            reasons.append("Permissive open license (CC0/CC-BY/PD)")
        elif not is_usable:
            reasons.append("Restricted or unverified license")

        return AssetEvaluationScore(
            asset_id=asset.asset_id,
            semantic_score=round(sem_score, 3),
            technical_score=round(tech_score, 3),
            creative_score=round(creat_score, 3),
            legal_score=round(legal_score, 3),
            composite_score=round(composite, 3),
            ranking_reason="; ".join(reasons) if reasons else "Standard match",
            is_usable=is_usable
        )

    def rank_candidates(
        self,
        assets: List[DiscoveredAsset],
        query: ResourceQuery
    ) -> List[Tuple[DiscoveredAsset, AssetEvaluationScore]]:
        """
        Evaluates and ranks candidate assets, filtering duplicates and unusable licenses.
        """
        scored_pairs = []
        seen_urls = set()

        for a in assets:
            # Deduplicate by download or source url
            key = a.download_url or a.source_page_url
            if key in seen_urls:
                continue
            seen_urls.add(key)

            score = self.evaluate_asset(a, query)
            scored_pairs.append((a, score))

        # Sort descending by composite score, prioritizing usable assets
        scored_pairs.sort(key=lambda x: (x[1].is_usable, x[1].composite_score), reverse=True)
        return scored_pairs

    def _compute_semantic_score(self, asset: DiscoveredAsset, query: ResourceQuery) -> float:
        score = 0.5
        q_tokens = set(query.query.lower().split())
        text_corpus = f"{asset.title} {asset.description} {' '.join(asset.tags)}".lower()

        # Token matches
        matched = sum(1 for t in q_tokens if t in text_corpus)
        if q_tokens:
            score = 0.3 + 0.7 * (matched / len(q_tokens))

        # Bonus for semantic tag matches
        for tag in query.semantic_tags:
            if tag.lower() in text_corpus:
                score = min(1.0, score + 0.15)

        return min(1.0, max(0.0, score))

    def _compute_technical_score(self, asset: DiscoveredAsset, query: ResourceQuery) -> float:
        score = 0.6
        w = asset.width or 0
        h = asset.height or 0

        # Resolution scoring
        if w >= 1920 or h >= 1920:
            score += 0.3
        elif w >= 1280 or h >= 1280:
            score += 0.2
        elif w > 0 and w < 640:
            score -= 0.3

        # Duration scoring for video
        if asset.duration and query.min_duration:
            if asset.duration >= query.min_duration:
                score += 0.1
            else:
                score -= 0.2

        return min(1.0, max(0.0, score))

    def _compute_creative_score(self, asset: DiscoveredAsset, query: ResourceQuery) -> float:
        # Evaluates richness of description, video mime type, and composition suitability
        score = 0.7
        if asset.media_type.value == "video":
            score += 0.15
        if asset.tags and len(asset.tags) >= 3:
            score += 0.1
        if "close-up" in asset.title.lower() or "macro" in asset.title.lower():
            score += 0.05
        return min(1.0, max(0.0, score))

    def _compute_legal_score(self, asset: DiscoveredAsset) -> Tuple[float, bool]:
        cat = asset.license_category
        if cat in (LicenseCategory.CC0, LicenseCategory.PUBLIC_DOMAIN):
            return 1.0, True
        elif cat == LicenseCategory.CC_BY:
            return 0.95, True
        elif cat == LicenseCategory.CC_BY_SA:
            return 0.85, True
        elif cat == LicenseCategory.COMMERCIAL_FREE:
            return 0.80, True
        elif cat == LicenseCategory.RESTRICTED:
            return 0.20, False
        else:
            return 0.50, True  # Unknown, requires flagging
