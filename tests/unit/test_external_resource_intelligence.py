"""
Unit Tests for External Creative Resource Intelligence Subsystem.
Department: 03_media_ingestion/discovery & 06_creative_direction
Verifies query formulation, multi-provider discovery, scoring/evaluation,
provenance tracking, and AI Creative Research Agent planning.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from core.assets.database import AssetDatabase, AssetRole
from departments.media_ingestion.discovery.models import (
    AssetEvaluationScore,
    AssetResearchPlan,
    DiscoveredAsset,
    LicenseCategory,
    ResourceMediaType,
    ResourceQuery,
)
from departments.media_ingestion.discovery.evaluator import AssetEvaluator
from departments.media_ingestion.discovery.acquisition import AssetAcquisitionService
from departments.media_ingestion.discovery.service import CreativeResourceDiscoveryService
from departments.media_ingestion.discovery.providers.base import BaseResourceProvider
from departments.creative_direction.research_agent import CreativeResearchAgent


class MockCreativeProvider(BaseResourceProvider):
    def __init__(self, name="Mock Creative Library", is_enabled=True):
        super().__init__(name=name, is_enabled=is_enabled)

    def search(self, query: ResourceQuery):
        return [
            DiscoveredAsset(
                asset_id="mock_001",
                provider="mock",
                title=f"Mock Octopus Shot ({query.query})",
                media_type=query.media_type,
                source_page_url="https://example.com/view/001",
                download_url="https://example.com/octopus.mp4",
                license_category=LicenseCategory.CC_BY,
                license_name="CC-BY-4.0",
                author="Marine Biologist",
                width=1080,
                height=1920,
                duration=8.5,
                tags=["octopus", "tentacles", "marine"],
                description="Cinematic vertical underwater close-up of octopus moving along reef."
            )
        ]

    def get_asset_details(self, asset_id: str):
        return None


class TestExternalResourceIntelligence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="studio_discovery_test_")
        cls.db_path = os.path.join(cls.temp_dir, "test_registry.db")
        cls.db = AssetDatabase(cls.db_path)
        cls.storage_dir = Path(cls.temp_dir) / "assets"
        cls.storage_dir.mkdir(parents=True, exist_ok=True)
        cls.acquisition = AssetAcquisitionService(storage_base_dir=cls.storage_dir, db=cls.db)
        cls.evaluator = AssetEvaluator()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_resource_query_and_asset_models(self):
        """Verifies Pydantic serialization and validation for query and discovered assets."""
        q = ResourceQuery(
            query="octopus branchial heart",
            media_type=ResourceMediaType.VIDEO,
            aspect_ratio="9:16",
            min_width=1080,
            min_height=1920,
            semantic_tags=["cephalopod", "circulatory"]
        )
        self.assertEqual(q.media_type, ResourceMediaType.VIDEO)
        self.assertEqual(q.aspect_ratio, "9:16")

        asset = DiscoveredAsset(
            asset_id="wm_12345",
            provider="wikimedia",
            title="Common Octopus Circulatory Anatomy",
            media_type=ResourceMediaType.VIDEO,
            source_page_url="https://commons.wikimedia.org/wiki/File:Octopus_hearts.webm",
            download_url="https://upload.wikimedia.org/test.webm",
            license_category=LicenseCategory.CC_BY_SA,
            license_name="CC-BY-SA 4.0",
            width=1080,
            height=1920,
            duration=12.0,
            tags=["octopus", "anatomy"]
        )
        d = asset.to_dict()
        self.assertEqual(d["provider"], "wikimedia")
        self.assertEqual(d["width"], 1080)
        self.assertEqual(d["height"], 1920)

        restored = DiscoveredAsset.from_dict(d)
        self.assertEqual(restored.title, asset.title)
        self.assertEqual(restored.license_category, LicenseCategory.CC_BY_SA)

    def test_02_asset_evaluator_multi_dimensional_scoring(self):
        """Verifies multi-dimensional evaluation: semantic, technical, creative, and legal usability."""
        q = ResourceQuery(
            query="octopus three hearts circulation",
            media_type=ResourceMediaType.VIDEO,
            aspect_ratio="9:16",
            min_width=1080,
            min_height=1920,
            semantic_tags=["heart", "gill", "oxygen"]
        )

        candidate_perfect = DiscoveredAsset(
            asset_id="wm_perf",
            provider="wikimedia",
            title="Octopus Three Hearts Circulation Close-Up",
            media_type=ResourceMediaType.VIDEO,
            source_page_url="https://commons.wikimedia.org/wiki/File:Perfect.webm",
            download_url="https://example.com/perf.mp4",
            license_category=LicenseCategory.PUBLIC_DOMAIN,
            license_name="CC0",
            width=1080,
            height=1920,
            duration=10.0,
            tags=["octopus", "heart", "circulation", "gill"],
            description="High resolution vertical video showing the three hearts and gill circulation in cephalopods."
        )

        score_perf = self.evaluator.evaluate_asset(candidate_perfect, q)
        self.assertGreaterEqual(score_perf.composite_score, 0.70)
        self.assertGreater(score_perf.semantic_score, 0.7)
        self.assertEqual(score_perf.legal_score, 1.0)
        self.assertTrue(score_perf.technical_score > 0.8)

        candidate_unrelated = DiscoveredAsset(
            asset_id="ov_bad",
            provider="openverse",
            title="Desert Cactus Landscape",
            media_type=ResourceMediaType.VIDEO,
            source_page_url="https://openverse.org/image/bad",
            download_url="https://example.com/cactus.mp4",
            license_category=LicenseCategory.RESTRICTED,
            license_name="CC-BY-NC",
            width=640,
            height=360,
            tags=["desert", "plants"]
        )
        score_bad = self.evaluator.evaluate_asset(candidate_unrelated, q)
        self.assertLess(score_bad.composite_score, score_perf.composite_score)
        self.assertLess(score_bad.legal_score, 0.5)

    def test_03_discovery_service_multi_provider_aggregation(self):
        """Verifies that CreativeResourceDiscoveryService aggregates and ranks candidates across providers."""
        service = CreativeResourceDiscoveryService(db=self.db)
        mock_p = MockCreativeProvider()
        service.providers["mock"] = mock_p

        q = ResourceQuery(
            query="octopus suction cups",
            media_type=ResourceMediaType.VIDEO,
            aspect_ratio="9:16",
            limit=5
        )

        ranked = service.search_multi_provider(q, provider_keys=["mock"])
        self.assertGreater(len(ranked), 0)
        asset, score = ranked[0]
        self.assertIn("octopus", asset.title.lower())
        self.assertGreater(score.composite_score, 0.4)

    def test_04_asset_acquisition_extension_and_sha256(self):
        """Verifies file extension deduction, SHA-256 generation, and local acquisition mechanics."""
        dummy_file = self.storage_dir / "test_dummy.mp4"
        dummy_file.write_bytes(b"TEST_MP4_CONTENT_1234567890")

        sha256 = self.acquisition.compute_sha256(dummy_file)
        self.assertEqual(len(sha256), 64)

        asset_webm = DiscoveredAsset(
            asset_id="wm_ext_test",
            provider="wikimedia",
            title="Octopus Test",
            media_type=ResourceMediaType.VIDEO,
            source_page_url="https://commons.wikimedia.org/wiki/File:Octopus.webm",
            download_url="https://upload.wikimedia.org/sample.webm",
            license_category=LicenseCategory.PUBLIC_DOMAIN
        )
        ext = self.acquisition._deduce_extension(asset_webm)
        self.assertEqual(ext, "webm")

    def test_05_creative_research_agent_plan_formulation(self):
        """Verifies that the CreativeResearchAgent decomposes narrative scenes into targeted queries and constraints."""
        agent = CreativeResearchAgent()
        scenes = [
            {
                "title": "Scene 1: Hook - Three Hearts",
                "duration_seconds": 6.0,
                "framing": "macro",
                "keywords": ["eye", "gaze", "tentacles"],
                "required_media_type": "video"
            },
            {
                "title": "Scene 2: Cephalopod Locomotion",
                "duration_seconds": 8.0,
                "framing": "wide",
                "keywords": ["swimming", "camouflage"],
                "required_media_type": "video"
            },
            {
                "title": "Scene 3: Anatomical Hearts",
                "duration_seconds": 11.0,
                "framing": "cutaway",
                "keywords": ["branchial", "gills", "systemic"],
                "required_media_type": "video"
            }
        ]

        plan = agent.generate_research_plan(
            project_id=str(uuid4()),
            topic="ऑक्टोपस के तीन दिल क्यों होते हैं?",
            script_scenes=scenes,
            visual_style="Cinematic Natural History Documentary",
            target_aspect_ratio="9:16",
            target_fps=30.0
        )

        self.assertIsInstance(plan, AssetResearchPlan)
        self.assertEqual(plan.total_scenes, 3)
        self.assertEqual(plan.target_aspect_ratio, "9:16")
        self.assertEqual(plan.target_fps, 30.0)

        # Scene 1 must have macro queries
        s1 = plan.items[0]
        self.assertTrue(any("macro" in q.lower() or "close-up" in q.lower() for q in s1.queries))

        # Scene 3 must have anatomical queries
        s3 = plan.items[2]
        self.assertTrue(any("circulat" in q.lower() or "anatom" in q.lower() or "heart" in q.lower() for q in s3.queries))


if __name__ == "__main__":
    unittest.main()
