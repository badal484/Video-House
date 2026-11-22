"""
Integration Tests for Online Media & Reference Intelligence HTTP Services.
Department: 01_studio_application, 03_media_ingestion, 04_media_intelligence
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from departments.studio_application.api import app, db
from core.assets.database import AssetRole, MediaType


class TestOnlineMediaPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.project_uuid = uuid4()
        cls.project_id = str(cls.project_uuid)
        db.create_project(cls.project_uuid, "Online Media Integration Test")

        # Create a synthetic 1-second video asset in DB for testing analysis
        cls.temp_dir = tempfile.mkdtemp(prefix="studio_pipeline_test_")
        cls.synth_video = Path(cls.temp_dir) / "synth_pipeline_video.mp4"
        cmd = [
            "/opt/homebrew/bin/ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-c:v", "libx264", "-c:a", "aac",
            str(cls.synth_video)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Register synthetic asset
        from departments.media_ingestion.online_media.online_acquisition_service import OnlineMediaAcquisitionService
        acq = OnlineMediaAcquisitionService(storage_base_dir=Path(cls.temp_dir), db=db)
        cls.sample_asset = acq.import_local_media_file(
            local_path=cls.synth_video,
            project_id=cls.project_uuid,
            display_name="Pipeline Sample Asset",
            role=AssetRole.REFERENCE_VIDEO
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_api_search_endpoint(self):
        """Verifies POST /api/v1/online-media/search returns list of metadata."""
        res = self.client.post("/api/v1/online-media/search", json={"query": "octopus", "limit": 2})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("results", data)
        self.assertIn("total_found", data)

    def test_02_api_inspect_endpoint(self):
        """Verifies POST /api/v1/online-media/inspect with a valid YouTube URL."""
        res = self.client.post(
            "/api/v1/online-media/inspect",
            json={"url": "https://www.youtube.com/watch?v=9ZnbvL8CVyA"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["video_id"], "9ZnbvL8CVyA")
        self.assertIn("available_resolutions", data["metadata"])

    def test_03_api_inspect_invalid_url(self):
        """Verifies that an invalid URL returns HTTP 400 error."""
        res = self.client.post("/api/v1/online-media/inspect", json={"url": "not_valid"})
        self.assertEqual(res.status_code, 400)

    def test_04_api_import_reference_only_endpoint(self):
        """Verifies POST /api/v1/online-media/import with reference_only declaration."""
        payload = {
            "url": "https://www.youtube.com/watch?v=9ZnbvL8CVyA",
            "media_type": "video",
            "permission_declaration": "reference_only",
            "destination_role": "REFERENCE_VIDEO",
            "project_id": self.project_id
        }
        res = self.client.post("/api/v1/online-media/import", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["import_result"]["permission_tier"], "reference_only")
        self.assertEqual(data["import_result"]["downloaded_bytes"], 0)

    def test_05_api_extract_audio_endpoint(self):
        """Verifies POST /api/v1/online-media/extract-audio extracts WAV and analyzes LUFS/waveform."""
        payload = {
            "source_asset_id": str(self.sample_asset.asset_id),
            "output_format": "wav",
            "sample_rate": 48000,
            "channels": 2,
            "project_id": self.project_id
        }
        res = self.client.post("/api/v1/online-media/extract-audio", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("analysis", data)
        self.assertIn("waveform_peaks", data["analysis"])
        self.assertIn("integrated_lufs", data["analysis"])

    def test_06_api_reference_analysis_and_inspiration_pipeline(self):
        """Verifies reference deconstruction and AI Director inspired production generation."""
        # 1. Analyze Reference
        res = self.client.post(
            "/api/v1/online-media/analyze-reference",
            json={"asset_id": str(self.sample_asset.asset_id), "name": "Test Documentary Ref"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIn("reference_profile", data)

        # 2. Generate Inspired Production Plan
        inspire_res = self.client.post(
            "/api/v1/online-media/inspire-production",
            json={
                "reference_asset_id": str(self.sample_asset.asset_id),
                "target_topic": "Cephalopod Evolution",
                "target_duration_sec": 45.0
            }
        )
        self.assertEqual(inspire_res.status_code, 200)
        plan_data = inspire_res.json()
        self.assertTrue(plan_data.get("success"))
        self.assertIn("production_plan", plan_data)
        self.assertGreaterEqual(len(plan_data["production_plan"]["planned_scene_structure"]), 3)

    def test_07_api_unified_library_endpoint(self):
        """Verifies GET /api/v1/projects/{project_id}/unified-library."""
        res = self.client.get(f"/api/v1/projects/{self.project_id}/unified-library")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(data["total"], 1)
        self.assertIn("permission_tier", data["assets"][0])


if __name__ == "__main__":
    unittest.main()

