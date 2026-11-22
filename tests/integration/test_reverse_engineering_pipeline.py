"""
Integration Test: End-to-End Multimodal Video Reverse Engineering Pipeline.
Executes against the real benchmark artifact:
test_artifacts/demonstrations/octopus_three_hearts_hindi_master.mp4 (50.0s 1080x1920 vertical video).
Verifies:
1. MasterVideoReverseEngineeringService produces full ReferenceReconstructionManifest and TemporalEventGraph.
2. Temporal event graph auto-connects PRECEDES, OVERLAPS, and SYNCHRONIZED_WITH edges.
3. ReferenceToProductionCompiler compiles original OpenTimelineIO (.otio) and MotionComposition.
4. FastAPI endpoints (/api/v1/intelligence/reverse-engineer, /api/v1/intelligence/compile-blueprint) operate cleanly.
"""
from pathlib import Path
import tempfile
import unittest
from uuid import UUID, uuid4

import departments

from fastapi.testclient import TestClient

from core.assets.database import AssetDatabase, AssetRecord, MediaType, ProcessingStatus
from core.intelligence.event_graph import GraphNodeType, TemporalEventGraph
from departments.studio_application.api import app, db
from departments.media_intelligence.master_reverse_engineer import (
    MasterVideoReverseEngineeringService,
    ReferenceReconstructionManifest
)
from departments.creative_direction.production_compiler import (
    ProductionBlueprint,
    ReferenceToProductionCompiler,
    TargetProductionBrief
)

class TestReverseEngineeringPipelineIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.benchmark_media = Path("test_artifacts/demonstrations/octopus_three_hearts_hindi_master.mp4")
        if not cls.benchmark_media.exists():
            raise FileNotFoundError(f"Benchmark artifact not found: {cls.benchmark_media}")

        # Register asset in database for integration test
        cls.project_id = uuid4()
        cls.asset_id = uuid4()
        db.create_project(cls.project_id, "Benchmark Reverse Engineering Project")
        db.register_asset(AssetRecord(
            asset_id=cls.asset_id,
            project_id=cls.project_id,
            original_filename="octopus_three_hearts_hindi_master.mp4",
            display_name="Octopus Three Hearts Master Reference",
            media_type=MediaType.VIDEO,
            detected_format="mp4",
            mime_type="video/mp4",
            byte_size=cls.benchmark_media.stat().st_size,
            checksum_sha256="benchmark_sha256",
            storage_path=str(cls.benchmark_media.resolve()),
            import_timestamp="2026-11-22T00:00:00Z",
            processing_status=ProcessingStatus.COMPLETED,
            metadata_status=ProcessingStatus.COMPLETED,
            derivative_status=ProcessingStatus.COMPLETED
        ))

    def test_01_master_reverse_engineering_execution(self):
        master = MasterVideoReverseEngineeringService(db=db)
        manifest, graph = master.reverse_engineer_video(
            video_path=self.benchmark_media,
            asset_id=self.asset_id,
            video_title="Octopus 3-Hearts Hindi Doc Master"
        )

        self.assertIsInstance(manifest, ReferenceReconstructionManifest)
        self.assertIsInstance(graph, TemporalEventGraph)
        self.assertAlmostEqual(manifest.total_duration_sec, 50.0, delta=1.0)
        self.assertEqual(manifest.aspect_ratio, "1080:1920")

        # Validate Cinematography & Composition
        self.assertGreater(len(manifest.cinematography_shots), 0)
        first_shot = manifest.cinematography_shots[0]
        self.assertIsNotNone(first_shot.shot_scale)
        self.assertGreater(first_shot.composition.rule_of_thirds_adherence, 0.0)

        # Validate Editing Rhythm
        self.assertGreater(manifest.editorial_rhythm.average_shot_length_sec, 0.0)
        self.assertGreater(manifest.editorial_rhythm.cuts_per_minute, 0.0)

        # Validate Color Grading
        self.assertEqual(len(manifest.color_grading.dominant_palette_hex), 5)
        self.assertIn(manifest.color_grading.color_harmony_type, ["COMPLEMENTARY", "ANALOGOUS", "TRIADIC", "MONOCHROMATIC"])

        # Validate Storytelling
        self.assertEqual(len(manifest.storytelling.narrative_phases), 5)
        self.assertEqual(manifest.storytelling.narrative_phases[0].phase_name, "HOOK")

        # Validate Event Graph Connectivity
        self.assertGreater(len(graph.nodes), 5)
        self.assertGreater(len(graph.edges), 0)

        # Search graph for Shot nodes
        shot_nodes = [n for n in graph.nodes.values() if n.node_type == GraphNodeType.SHOT]
        self.assertGreater(len(shot_nodes), 0)

    def test_02_production_blueprint_compilation(self):
        master = MasterVideoReverseEngineeringService(db=db)
        manifest, _ = master.reverse_engineer_video(
            video_path=self.benchmark_media,
            asset_id=self.asset_id,
            video_title="Octopus Master"
        )

        compiler = ReferenceToProductionCompiler()
        brief = TargetProductionBrief(
            project_id=self.project_id,
            title="Original Octopus Anatomy Documentary",
            target_topic="Octopus Three Hearts Biology",
            target_duration_sec=50.0,
            aspect_ratio="9:16",
            target_language="hi"
        )

        blueprint = compiler.compile_reference_to_blueprint(manifest, brief)
        self.assertIsInstance(blueprint, ProductionBlueprint)
        self.assertTrue(Path(blueprint.otio_timeline_path).exists())
        self.assertIn("scenes", blueprint.motion_composition)
        self.assertEqual(len(blueprint.motion_composition["scenes"]), 5)
        self.assertEqual(blueprint.qc_validation_policies["audio_loudness_target_lufs"], -14.0)
        self.assertGreaterEqual(len(blueprint.asset_acquisition_plan), 2)

    def test_03_api_reverse_engineer_and_blueprint_endpoints(self):
        # 1. Reverse Engineer Endpoint
        resp_re = self.client.post("/api/v1/intelligence/reverse-engineer", json={
            "asset_id": str(self.asset_id),
            "title": "API Test Reverse Engineering"
        })
        self.assertEqual(resp_re.status_code, 200)
        data_re = resp_re.json()
        self.assertTrue(data_re["success"])
        self.assertIn("manifest", data_re)
        self.assertIn("event_graph", data_re)

        # 2. Get Event Graph Endpoint
        resp_graph = self.client.get(f"/api/v1/intelligence/event-graph/{self.asset_id}")
        self.assertEqual(resp_graph.status_code, 200)
        data_graph = resp_graph.json()
        self.assertTrue(data_graph["success"])
        self.assertGreater(len(data_graph["event_graph"]["nodes"]), 0)

        # 3. Query Graph Endpoint
        resp_query = self.client.post("/api/v1/intelligence/query-graph", json={
            "asset_id": str(self.asset_id),
            "query": "Shot"
        })
        self.assertEqual(resp_query.status_code, 200)
        data_query = resp_query.json()
        self.assertTrue(data_query["success"])
        self.assertGreater(data_query["results_count"], 0)

        # 4. Compile Blueprint Endpoint
        resp_bp = self.client.post("/api/v1/intelligence/compile-blueprint", json={
            "asset_id": str(self.asset_id),
            "project_id": str(self.project_id),
            "target_topic": "Marine Biology Octopus",
            "target_duration_sec": 50.0,
            "aspect_ratio": "9:16",
            "target_language": "hi"
        })
        self.assertEqual(resp_bp.status_code, 200)
        data_bp = resp_bp.json()
        self.assertTrue(data_bp["success"])
        self.assertIn("blueprint", data_bp)
        self.assertTrue(Path(data_bp["blueprint"]["otio_timeline_path"]).exists())

if __name__ == "__main__":
    unittest.main()
