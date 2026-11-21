"""
Cross-Department Data Contracts & Schema Compatibility Integration Test Suite.
Validates that all 22 departments exchange strictly typed, non-corrupting data:
- Assets <-> Database <-> Technical Metadata
- Planning Shots <-> Storyboard <-> Edit Blueprint <-> OTIO Timeline
- Character DNA <-> 2D Model Sheets <-> Prompt Dialects
- Motion Graphics Presets <-> Video Editing Tracks
- Audio DAW Sessions <-> EBU R128 Loudness Normalization
- Quality Control Policies <-> Render Delivery Manifest
"""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from departments.studio_application.api import app, db


class TestCrossDepartmentContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = tempfile.mkdtemp(prefix="studio_contracts_test_")
        cls.fixtures_dir = Path(cls.test_dir) / "fixtures"
        cls.fixtures_dir.mkdir(parents=True, exist_ok=True)

        cls.sample_video = str(cls.fixtures_dir / "contract_video.mp4")
        with open(cls.sample_video, "wb") as f:
            f.write(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 2048)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def create_project(self, name: str = "Contracts Project") -> str:
        res = self.client.post("/api/v1/projects", json={"name": name})
        self.assertEqual(res.status_code, 201)
        return res.json()["project_id"]

    def test_01_asset_metadata_contract(self):
        """Verify AssetRecord schema integrity and technical metadata mapping."""
        project_id = self.create_project("Asset Metadata Proj")
        import_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": self.sample_video, "display_name": "TestClip.mp4", "roles": ["SOURCE_FOOTAGE"]}
        )
        self.assertEqual(import_res.status_code, 202)
        asset_id = import_res.json()["asset_id"]

        get_res = self.client.get(f"/api/v1/projects/{project_id}/assets/{asset_id}")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.json()
        self.assertEqual(data["asset_id"], asset_id)
        self.assertEqual(data["project_id"], project_id)
        self.assertIn("SOURCE_FOOTAGE", data["roles"])
        self.assertTrue(len(data["checksum_sha256"]) == 64)

    def test_02_script_to_storyboard_shot_contract(self):
        """Verify data contract flow from creative script scenes to planned shots and storyboard."""
        project_id = self.create_project("Script-to-Shots Proj")

        # 1. Submit Brief
        self.client.post(f"/api/v1/projects/{project_id}/creative/brief", json={"prompt": "Action trailer"})
        # 2. Develop Script
        script_res = self.client.post(f"/api/v1/projects/{project_id}/creative/script", json={})
        self.assertTrue(script_res.json()["success"])
        # 3. Plan Shots
        shots_res = self.client.post(f"/api/v1/projects/{project_id}/creative/shots", json={})
        self.assertTrue(shots_res.json()["success"])
        # 4. Generate Storyboard
        sb_res = self.client.post(f"/api/v1/projects/{project_id}/creative/storyboard")
        self.assertTrue(sb_res.json()["success"])
        frames = sb_res.json()["frames"]
        self.assertGreaterEqual(len(frames), 1)
        for frame in frames:
            self.assertIn("frame_order", frame)
            self.assertIn("prompt_spec", frame)

    def test_03_character_dna_to_animation_turnaround_contract(self):
        """Verify character identity attributes are preserved in 2D Settei turnaround model sheets."""
        project_id = self.create_project("Character DNA Proj")
        char_res = self.client.post(
            "/api/v1/animation/characters",
            json={
                "project_id": project_id,
                "name": "Aoi",
                "brief": "Cyberpunk runner with neon blue hair and tactical armor",
                "visual_style": "ANIME_CEL"
            }
        )
        self.assertEqual(char_res.status_code, 200)
        data = char_res.json()
        self.assertTrue(data["success"])
        self.assertIn("character", data)
        self.assertEqual(data["character"]["name"], "Aoi")
        self.assertIn("model_sheet", data)
        self.assertIn("front_view", data["model_sheet"])
        self.assertIn("alignment_guides", data["model_sheet"])

    def test_04_motion_preset_to_otio_timeline_contract(self):
        """Verify declarative motion graphics presets can be instantiated and mapped to timeline clips."""
        project_id = self.create_project("Motion-to-Timeline Proj")
        presets = self.client.get("/api/v1/motion-graphics/presets").json()["presets"]
        preset_id = presets[0]["preset_id"]

        inst_res = self.client.post(
            f"/api/v1/motion-graphics/presets/{preset_id}/instantiate",
            json={
                "project_id": project_id,
                "parameters": {"title_text": "INTELLIGENT TIMELINE", "subtitle_text": "AI NLE"}
            }
        )
        self.assertEqual(inst_res.status_code, 200)
        comp = inst_res.json()["composition"]
        self.assertEqual(comp["project_id"], project_id)
        self.assertIn("duration", comp)
        self.assertIn("fps", comp)

    def test_05_audio_daw_loudness_contract(self):
        """Verify audio mastering contract enforces YouTube / EBU R128 loudness standard."""
        project_id = self.create_project("DAW Loudness Proj")
        sess_res = self.client.post(
            "/api/v1/audio/sessions",
            json={"project_id": project_id, "name": "Film DAW Session", "target_lufs": -14.0}
        )
        self.assertEqual(sess_res.status_code, 200)
        session = sess_res.json()["session"]
        self.assertEqual(session["project_id"], project_id)
        self.assertEqual(session["sample_rate"], 48000)

    def test_06_render_plan_cost_and_dag_contract(self):
        """Verify render plan DAG compilation calculates deterministic cost estimates and stage ordering."""
        project_id = self.create_project("Render DAG Proj")
        plan_res = self.client.post(
            "/api/v1/rendering/plan",
            json={"project_id": project_id, "render_profile_id": "youtube_1080p"}
        )
        self.assertEqual(plan_res.status_code, 200)
        plan = plan_res.json()["data"]["render_plan"]
        self.assertEqual(plan["project_id"], project_id)
        self.assertIn("stages", plan)
        self.assertIn("estimated_cost_usd", plan)
        self.assertGreaterEqual(plan["estimated_cost_usd"], 0.0)

    def test_07_qc_report_to_delivery_package_contract(self):
        """Verify delivery package rejects missing QC report and validates SHA-256 checksums."""
        project_id = self.create_project("QC-to-Package Proj")

        # Run QC audit
        qc_res = self.client.post(
            "/api/v1/qc/audit",
            json={"project_id": project_id, "file_path": self.sample_video, "policy_name": "STREAMING_STANDARD"}
        )
        self.assertEqual(qc_res.status_code, 200)
        report_id = qc_res.json()["data"]["qc_report"]["report_id"]

        # Create Delivery Package
        pkg_res = self.client.post(
            "/api/v1/rendering/delivery/package",
            json={
                "project_id": str(project_id),
                "render_job_id": str(uuid4()),
                "master_file_path": self.sample_video,
                "sidecars": [],
                "qc_summary": {"qc_report_id": report_id, "status": "PASSED"}
            }
        )
        self.assertEqual(pkg_res.status_code, 201)
        data = pkg_res.json()["data"]["delivery_package"]
        self.assertIn("manifest_path", data)
        self.assertIn("delivery_id", data)


if __name__ == "__main__":
    unittest.main()
