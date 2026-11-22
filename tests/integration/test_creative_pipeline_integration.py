"""
Integration Tests for End-to-End Creative Resource Intelligence and Motion Design Pipeline.
Department: 01_studio_application, 03_media_ingestion, 06_creative_direction, 09_motion_graphics
Verifies end-to-end pipeline execution from script brief to discovery, scoring,
motion design art direction, design validation, and REST API endpoints.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from departments.studio_application.api import app, db
from departments.media_ingestion.discovery.service import CreativeResourceDiscoveryService
from departments.media_ingestion.discovery.models import ResourceQuery, ResourceMediaType, DiscoveredAsset, LicenseCategory
from departments.creative_direction.research_agent import CreativeResearchAgent
from departments.creative_direction.motion_director import MotionDesignDirector
from departments.motion_graphics.core.design_validator import DesignValidator


class TestCreativePipelineIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.project_uuid = uuid4()
        cls.project_id = str(cls.project_uuid)
        # Ensure project exists in DB for foreign key constraints
        db.create_project(cls.project_uuid, "Integration Test Project")

    def test_01_end_to_end_research_and_discovery_pipeline(self):
        """Verifies script breakdown -> research plan -> multi-provider search and scoring."""
        agent = CreativeResearchAgent()
        discovery = CreativeResourceDiscoveryService()

        scenes = [
            {
                "title": "Scene 1: Hook",
                "duration_seconds": 6.0,
                "description": "Octopus deep in water looking at camera with three hearts.",
                "framing": "macro",
                "required_media_type": "video",
                "keywords": ["eyes", "three hearts"]
            },
            {
                "title": "Scene 2: Circulation",
                "duration_seconds": 11.0,
                "description": "Branchial hearts pumping blood to gills.",
                "framing": "cutaway",
                "required_media_type": "video",
                "keywords": ["gill", "circulation"]
            }
        ]

        # 1. Generate Research Plan
        plan = agent.generate_research_plan(
            project_id=self.project_id,
            topic="Octopus 3 Hearts",
            script_scenes=scenes,
            visual_style="Cinematic Natural History",
            target_aspect_ratio="9:16",
            target_fps=30.0
        )
        self.assertEqual(len(plan.items), 2)

        # 2. Query Discovery Service with plan item 1
        query = ResourceQuery(
            query=plan.items[0].queries[0],
            media_type=plan.items[0].required_media_type,
            aspect_ratio=plan.target_aspect_ratio,
            limit=5
        )
        ranked = discovery.search_multi_provider(query)
        self.assertIsInstance(ranked, list)

    def test_02_end_to_end_motion_director_and_validator_pipeline(self):
        """Verifies script scenes -> MotionDesignDirector -> MotionComposition -> DesignValidator."""
        director = MotionDesignDirector()
        scenes = [
            {"title": "Scene 1: Hook", "duration_seconds": 6.0, "narration_hi": "समुद्र में एक ऐसा जीव है..."},
            {"title": "Scene 2: Tentacles", "duration_seconds": 8.0, "narration_hi": "इसके आठ हाथ होते हैं..."},
            {"title": "Scene 3: Hemodynamics", "duration_seconds": 11.0, "narration_hi": "दो दिल खून को गलफड़ों तक पहुँचाते हैं..."}
        ]

        motion_plan = director.direct_project_motion(
            project_id=self.project_id,
            topic="Octopus 3 Hearts",
            script_scenes=scenes,
            resolution=(1080, 1920),
            fps=30.0
        )

        comp = director.synthesize_motion_composition(self.project_id, motion_plan)
        self.assertEqual(len(comp.scenes), 3)

        val = DesignValidator.validate_composition(comp)
        self.assertTrue(val.get("valid", True), f"Validation failed: {val}")

    def test_03_rest_api_research_plan_endpoint(self):
        """Verifies POST /api/v1/projects/{project_id}/research/plan HTTP endpoint."""
        payload = {
            "topic": "ऑक्टोपस के तीन दिल क्यों होते हैं?",
            "scenes": [
                {"title": "Scene 1: Hook", "duration_seconds": 6.0, "framing": "macro", "keywords": ["tentacle", "eye"]},
                {"title": "Scene 2: Gills", "duration_seconds": 11.0, "framing": "cutaway", "keywords": ["branchial", "gills"]}
            ],
            "visual_style": "Cinematic Natural History Documentary",
            "target_aspect_ratio": "9:16",
            "target_fps": 30.0
        }
        res = self.client.post(f"/api/v1/projects/{self.project_id}/research/plan", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("research_plan", data)
        self.assertEqual(data["research_plan"]["total_scenes"], 2)

    def test_04_rest_api_research_discover_endpoint(self):
        """Verifies POST /api/v1/projects/{project_id}/research/discover HTTP endpoint."""
        payload = {
            "query": "octopus tentacle suction cups",
            "media_type": "video",
            "aspect_ratio": "9:16",
            "limit": 5,
            "semantic_tags": ["cephalopod", "marine"]
        }
        res = self.client.post(f"/api/v1/projects/{self.project_id}/research/discover", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("results", data)
        self.assertIn("total_found", data)

    def test_05_rest_api_motion_compose_endpoint(self):
        """Verifies POST /api/v1/projects/{project_id}/motion-graphics/compose HTTP endpoint."""
        payload = {
            "topic": "ऑक्टोपस के तीन दिल",
            "scenes": [
                {"title": "Scene 1: Hook", "duration_seconds": 6.0, "narration_hi": "क्या आप जानते हैं? तीन दिल..."},
                {"title": "Scene 2: Tentacles", "duration_seconds": 8.0, "narration_hi": "इसके आठ हाथ होते हैं..."},
                {"title": "Scene 5: Systemic Pause", "duration_seconds": 8.0, "narration_hi": "तैरते समय मुख्य दिल रुक जाता है..."}
            ],
            "resolution": [1080, 1920],
            "fps": 30.0,
            "style_name": "Abyssal Biometrics & Micro-Optics"
        }
        res = self.client.post(f"/api/v1/projects/{self.project_id}/motion-graphics/compose", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("composition", data)
        self.assertIn("composition_plan", data)
        self.assertEqual(len(data["composition"]["scenes"]), 3)


if __name__ == "__main__":
    unittest.main()
