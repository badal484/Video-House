"""
Comprehensive End-to-End Project Lifecycle Integration Test Suite.
Validates the complete 8-stage production pipeline from project creation to final delivery:
- Stage A: Project Creation & Configuration Persistence
- Stage B: Media Ingestion & Asset Manifest Verification
- Stage C: Multimodal Video & Audio Understanding
- Stage D: Reference Video Profiling & Comparative Analysis
- Stage E: AI Director & Creative Production Planning
- Stage F: Generative Asset Compilation & Provenance
- Stage G: Multi-Department Editorial, VFX, Audio & Motion Graphics Assembly
- Stage H: Rendering, Automated QC Audit & Delivery Package Manifest
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from departments.studio_application.api import app, db, video_editor, ingestion_service


class TestEndToEndProjectLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = tempfile.mkdtemp(prefix="studio_e2e_test_")
        cls.fixtures_dir = Path(cls.test_dir) / "fixtures"
        cls.fixtures_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create Synthetic Valid Media Files for Ingestion
        # Valid MP4 video with ftyp box
        cls.video_path = str(cls.fixtures_dir / "camera_a_01.mp4")
        with open(cls.video_path, "wb") as f:
            f.write(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 4096)

        # Valid Reference MP4 video
        cls.ref_video_path = str(cls.fixtures_dir / "cinematic_reference.mp4")
        with open(cls.ref_video_path, "wb") as f:
            f.write(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x01" * 4096)

        # Valid 24-bit 48kHz WAV audio header
        cls.audio_path = str(cls.fixtures_dir / "voiceover.wav")
        with open(cls.audio_path, "wb") as f:
            f.write(b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x80\xbb\x00\x00\x00\xee\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00" + b"\x00" * 2048)

        # Valid PNG graphic image
        cls.image_path = str(cls.fixtures_dir / "title_card.png")
        with open(cls.image_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa" + b"\x00" * 100)

        # Valid SRT subtitle file
        cls.sub_path = str(cls.fixtures_dir / "captions.srt")
        with open(cls.sub_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:01,000 --> 00:00:04,000\nQuantum drive operational.\n\n")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    # =========================================================================
    # STAGE A — Project Creation & Configuration Persistence
    # =========================================================================
    def test_stage_a_project_creation_and_lifecycle(self):
        """Stage A: Create, configure, persist, and retrieve production project."""
        # 1. Verify Application is reachable
        root_res = self.client.get("/")
        self.assertEqual(root_res.status_code, 200)

        # 2. Create New Project
        create_res = self.client.post("/api/v1/projects", json={
            "name": "Hypercar Commercial 30s",
            "settings": {
                "template": "COMMERCIAL_16_9",
                "aspect_ratio": "16:9",
                "resolution_w": 1920,
                "resolution_h": 1080,
                "fps": 24.0,
                "color_space": "rec709",
                "audio_sample_rate": 48000,
                "current_stage": "INGESTION"
            }
        })
        self.assertEqual(create_res.status_code, 201)
        data = create_res.json()
        self.assertIn("project_id", data)
        project_id = data["project_id"]

        # 3. Configure Project Settings
        update_res = self.client.patch(f"/api/v1/projects/{project_id}", json={
            "settings": {
                "color_space": "acescg",
                "current_stage": "PLANNING",
                "metadata": {"director": "AI Executive Director", "client": "Apex Motors"}
            }
        })
        self.assertEqual(update_res.status_code, 200)

        # 4. Close & Re-open Project (Verify Persistence)
        get_res = self.client.get(f"/api/v1/projects/{project_id}")
        self.assertEqual(get_res.status_code, 200)
        proj_data = get_res.json()
        self.assertEqual(proj_data["project_id"], project_id)
        self.assertEqual(proj_data["settings"]["color_space"], "acescg")
        self.assertEqual(proj_data["settings"]["current_stage"], "PLANNING")
        self.assertEqual(proj_data["settings"]["fps"], 24.0)
        self.assertEqual(proj_data["settings"]["resolution_w"], 1920)

    # =========================================================================
    # STAGE B — Media Ingestion & Asset Manifest Verification
    # =========================================================================
    def test_stage_b_media_ingestion_and_manifest(self):
        """Stage B: Ingest multi-modal media assets, compute hashes, preserve originals."""
        # Create Project
        proj_res = self.client.post("/api/v1/projects", json={"name": "Ingestion Test Proj"})
        project_id = proj_res.json()["project_id"]

        # 1. Ingest Video Footage
        v_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": self.video_path, "display_name": "Hypercar_Track_A01.mp4", "roles": ["SOURCE_FOOTAGE"]}
        )
        self.assertEqual(v_res.status_code, 202)
        v_aid = v_res.json()["asset_id"]

        # 2. Ingest Reference Video
        ref_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": self.ref_video_path, "display_name": "Cyberpunk_Look_Ref.mp4", "roles": ["REFERENCE_VIDEO"]}
        )
        self.assertEqual(ref_res.status_code, 202)
        ref_aid = ref_res.json()["asset_id"]

        # 3. Ingest Audio
        a_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": self.audio_path, "display_name": "Narrator_Take01.wav", "roles": ["VOICE_RECORDING"]}
        )
        self.assertEqual(a_res.status_code, 202)

        # 4. Ingest Image
        img_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": self.image_path, "display_name": "Logo_Overlay.png", "roles": ["GENERATED_IMAGE"]}
        )
        self.assertEqual(img_res.status_code, 202)

        # 5. Ingest Subtitle
        sub_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": self.sub_path, "display_name": "Captions_EN.srt", "roles": ["SUBTITLE"]}
        )
        self.assertEqual(sub_res.status_code, 202)

        # 6. Browse Assets & Verify SHA-256 Checksums
        list_res = self.client.get(f"/api/v1/projects/{project_id}/assets")
        self.assertEqual(list_res.status_code, 200)
        assets = list_res.json()["assets"]
        self.assertEqual(len(assets), 5)

        for a in assets:
            self.assertIn("checksum_sha256", a)
            self.assertTrue(len(a["checksum_sha256"]) == 64)
            self.assertEqual(a["project_id"], project_id)

        # 7. Verify Original Files on Disk are preserved and unmodified
        orig_stat = os.stat(self.video_path)
        self.assertGreater(orig_stat.st_size, 0)

    # =========================================================================
    # STAGE C & D — Multimodal Understanding & Reference Profiling
    # =========================================================================
    def test_stage_c_and_d_intelligence_and_reference(self):
        """Stage C & D: Analyze footage, extract shot boundaries, and build reference profile."""
        proj_res = self.client.post("/api/v1/projects", json={"name": "Intelligence Proj"})
        project_id = proj_res.json()["project_id"]

        import_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": self.video_path, "display_name": "Source_Take.mp4", "roles": ["SOURCE_FOOTAGE"]}
        )
        asset_id = import_res.json()["asset_id"]

        # 1. Trigger Multimodal Analysis
        an_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/{asset_id}/analyze",
            json={"profile": "STANDARD"}
        )
        self.assertEqual(an_res.status_code, 200)

        # 2. Query Extracted Shots
        shots_res = self.client.get(f"/api/v1/projects/{project_id}/assets/{asset_id}/shots")
        self.assertEqual(shots_res.status_code, 200)
        self.assertIn("shots", shots_res.json())

        # 3. Query Transcription
        tx_res = self.client.get(f"/api/v1/projects/{project_id}/assets/{asset_id}/transcript")
        self.assertEqual(tx_res.status_code, 200)

        # 4. Generate Reference Profile
        ref_res = self.client.post(f"/api/v1/projects/{project_id}/assets/{asset_id}/reference-profile")
        self.assertEqual(ref_res.status_code, 200)
        self.assertTrue(ref_res.json()["success"])

        # 5. Retrieve Reference Profile
        prof_res = self.client.get(f"/api/v1/projects/{project_id}/assets/{asset_id}/reference-profile")
        self.assertEqual(prof_res.status_code, 200)
        self.assertIn("reference_profile", prof_res.json())

    # =========================================================================
    # STAGE E — AI Production Planning & Blueprint Compilation
    # =========================================================================
    def test_stage_e_production_planning_pipeline(self):
        """Stage E: Natural language brief -> concepts -> script -> shots -> storyboard -> blueprint."""
        proj_res = self.client.post("/api/v1/projects", json={"name": "Planning Proj"})
        project_id = proj_res.json()["project_id"]

        # 1. Submit Creative Brief
        brief_res = self.client.post(
            f"/api/v1/projects/{project_id}/creative/brief",
            json={
                "prompt": "Create a futuristic 15-second hypercar teaser with neon night aesthetic.",
                "genre": "Commercial",
                "visual_style": "High-Contrast Cyberpunk",
                "target_duration_sec": 15.0
            }
        )
        self.assertEqual(brief_res.status_code, 200)
        self.assertTrue(brief_res.json()["success"])

        # 2. Generate Concepts
        conc_res = self.client.post(f"/api/v1/projects/{project_id}/creative/concepts")
        self.assertEqual(conc_res.status_code, 200)
        self.assertGreaterEqual(len(conc_res.json()["concepts"]), 1)

        # 3. Create Script Breakdown
        script_res = self.client.post(f"/api/v1/projects/{project_id}/creative/script", json={})
        self.assertEqual(script_res.status_code, 200)
        self.assertTrue(script_res.json()["success"])

        # 4. Plan Structured Shots
        shots_res = self.client.post(f"/api/v1/projects/{project_id}/creative/shots", json={"visual_style": "Cyberpunk Neon"})
        self.assertEqual(shots_res.status_code, 200)
        self.assertTrue(shots_res.json()["success"])

        # 5. Generate Visual Storyboard Deck
        sb_res = self.client.post(f"/api/v1/projects/{project_id}/creative/storyboard")
        self.assertEqual(sb_res.status_code, 200)
        self.assertTrue(sb_res.json()["success"])
        self.assertIn("frames", sb_res.json())

        # 6. Request Approval & Persist Approved State
        appr_res = self.client.post(
            f"/api/v1/projects/{project_id}/creative/approve",
            json={
                "entity_type": "SCRIPT",
                "entity_id": script_res.json()["script_id"],
                "status": "APPROVED",
                "reviewer_notes": "Director approved final scene rhythm."
            }
        )
        self.assertEqual(appr_res.status_code, 200)
        self.assertTrue(appr_res.json()["success"])

        # 7. Verify Approval History
        hist_res = self.client.get(f"/api/v1/projects/{project_id}/creative/approvals")
        self.assertEqual(hist_res.status_code, 200)
        self.assertGreaterEqual(len(hist_res.json()["approvals"]), 1)

    # =========================================================================
    # STAGE F — Asset & Generative Workflows
    # =========================================================================
    def test_stage_f_generative_workflows_and_character_consistency(self):
        """Stage F: Prompt compiler, character profile consistency, and generative job tracking."""
        proj_res = self.client.post("/api/v1/projects", json={"name": "Gen Proj"})
        project_id = proj_res.json()["project_id"]

        # 1. Compile Structured Prompt
        comp_res = self.client.post("/api/v1/generation/compile-prompt", json={
            "dimensions": {
                "subject": "Electric hypercar with glowing cyan rim lights",
                "action": "accelerating through rainy Tokyo highway",
                "camera": "tracking side profile low angle",
                "lighting": "wet asphalt neon reflections",
                "mood_style": "cinematic hyper-realism"
            },
            "provider_id": "runway_gen3"
        })
        self.assertEqual(comp_res.status_code, 200)
        self.assertTrue(comp_res.json()["success"])
        self.assertIn("compiled_positive_prompt", comp_res.json())

        # 2. Register Character Reference Profile
        char_res = self.client.post("/api/v1/generation/characters", json={
            "project_id": project_id,
            "name": "Kaito",
            "style_description": "Cyberpunk pilot with titanium cybernetic eye",
            "distinguishing_features": ["cyan glow iris", "matte black flight jacket"]
        })
        self.assertEqual(char_res.status_code, 200)
        self.assertTrue(char_res.json()["success"])

    # =========================================================================
    # STAGE G — Production Workflows (Timeline, Motion, VFX, Audio, Color, Subs)
    # =========================================================================
    def test_stage_g_cross_department_production_assembly(self):
        """Stage G: Multi-track OTIO timeline, motion graphics preset, VFX, audio DAW, color, and subtitles."""
        proj_res = self.client.post("/api/v1/projects", json={"name": "Assembly Proj"})
        project_id = proj_res.json()["project_id"]

        # 1. Create OpenTimelineIO Timeline
        tl_res = self.client.post(
            f"/api/v1/editing/projects/{project_id}/timelines",
            json={"name": "Master Sequence", "fps": 24.0}
        )
        self.assertEqual(tl_res.status_code, 200)
        timeline_id = tl_res.json()["timeline"]["timeline_id"]

        # Add Track V1
        track_res = self.client.post(
            f"/api/v1/editing/timelines/{timeline_id}/tracks",
            json={"track_type": "VIDEO", "name": "V1"}
        )
        self.assertEqual(track_res.status_code, 200)
        track_id = track_res.json()["track"]["track_id"]

        # 2. Ingest Footage for Timeline
        v_res = self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": self.video_path, "display_name": "Main_Clip.mp4"}
        )
        asset_id = v_res.json()["asset_id"]

        # 3. Add Video Clip to Timeline V1
        clip_res = self.client.post(
            f"/api/v1/editing/timelines/{timeline_id}/clips",
            json={
                "track_id": track_id,
                "asset_id": asset_id,
                "timeline_start_sec": 0.0,
                "duration_sec": 5.0,
                "name": "Shot 01 Hypercar"
            }
        )
        self.assertEqual(clip_res.status_code, 200)
        clip_id = clip_res.json()["clip"]["clip_id"]

        # 4. Perform Split Cut on Clip
        split_res = self.client.post(
            f"/api/v1/editing/timelines/{timeline_id}/clips/{clip_id}/split",
            json={"split_time_sec": 2.5}
        )
        self.assertEqual(split_res.status_code, 200)
        self.assertTrue(split_res.json()["success"])

        # 5. Instantiate Motion Graphics Title Preset
        presets_res = self.client.get("/api/v1/motion-graphics/presets")
        preset_id = presets_res.json()["presets"][0]["preset_id"]
        mg_res = self.client.post(
            f"/api/v1/motion-graphics/presets/{preset_id}/instantiate",
            json={
                "project_id": project_id,
                "parameters": {"title_text": "APEX HYPERCAR", "subtitle_text": "ZERO EMISSIONS"}
            }
        )
        self.assertEqual(mg_res.status_code, 200)
        self.assertTrue(mg_res.json()["success"])

        # 6. Initialize Multitrack Audio Session & Procedural SFX
        audio_res = self.client.post(
            "/api/v1/audio/sessions",
            json={"project_id": project_id, "name": "DAW Mix", "sample_rate": 48000, "target_lufs": -14.0}
        )
        self.assertEqual(audio_res.status_code, 200)
        session_id = audio_res.json()["session"]["session_id"]

        sfx_res = self.client.post(
            "/api/v1/audio/sfx/generate",
            json={"sfx_type": "whoosh", "duration_sec": 1.5}
        )
        self.assertEqual(sfx_res.status_code, 200)
        self.assertTrue(sfx_res.json()["success"])

        # 7. AI Colorist Recommendation
        color_res = self.client.post(
            "/api/v1/color/recommend-grade",
            json={"project_id": project_id, "asset_id": asset_id, "look_style": "TEAL_AND_ORANGE"}
        )
        self.assertEqual(color_res.status_code, 200)
        self.assertTrue(color_res.json()["success"])

        # 8. Generate Subtitle Track
        sub_res = self.client.post(
            "/api/v1/localization/subtitles",
            json={
                "project_id": project_id,
                "segments": [
                    {"segment_id": "s1", "text": "The future of performance.", "start_time": 0.5, "end_time": 3.0, "speaker_id": "spk_1"}
                ],
                "format": "srt",
                "style_preset": "cinematic"
            }
        )
        self.assertEqual(sub_res.status_code, 200)
        self.assertTrue(sub_res.json()["success"])

    # =========================================================================
    # STAGE H — Rendering, Automated QC Audit & Delivery Manifest
    # =========================================================================
    def test_stage_h_rendering_qc_audit_and_delivery(self):
        """Stage H: Render plan compilation, technical QC audit, and delivery manifest generation."""
        proj_res = self.client.post("/api/v1/projects", json={"name": "Delivery Proj"})
        project_id = proj_res.json()["project_id"]

        # 1. Compile Render Plan DAG
        plan_res = self.client.post(
            "/api/v1/rendering/plan",
            json={"project_id": project_id, "render_profile_id": "youtube_1080p"}
        )
        self.assertEqual(plan_res.status_code, 200)
        self.assertTrue(plan_res.json()["success"])
        self.assertIn("render_plan", plan_res.json()["data"])

        # 2. Execute Technical Quality Control Audit on Rendered Media
        qc_res = self.client.post(
            "/api/v1/qc/audit",
            json={
                "project_id": project_id,
                "file_path": self.video_path,
                "policy_name": "STREAMING_STANDARD"
            }
        )
        self.assertEqual(qc_res.status_code, 200)
        qc_data = qc_res.json()
        self.assertTrue(qc_data["success"])
        self.assertIn("qc_report", qc_data["data"])
        report_id = qc_data["data"]["qc_report"]["report_id"]

        # 3. Create Delivery Package & Delivery Manifest with SHA-256 Checksums
        pkg_res = self.client.post(
            "/api/v1/rendering/delivery/package",
            json={
                "project_id": str(project_id),
                "render_job_id": str(uuid4()),
                "master_file_path": self.video_path,
                "sidecars": [
                    {"path": self.audio_path, "type": "AUDIO_STEM"},
                    {"path": self.sub_path, "type": "SUBTITLE"}
                ],
                "qc_summary": {"qc_report_id": report_id, "status": "PASSED"}
            }
        )
        self.assertEqual(pkg_res.status_code, 201)
        pkg_data = pkg_res.json()
        self.assertTrue(pkg_data["success"])
        self.assertIn("delivery_package", pkg_data["data"])

        pkg = pkg_data["data"]["delivery_package"]
        self.assertEqual(pkg["project_id"], str(project_id))
        self.assertIn("manifest_path", pkg)
        self.assertEqual(len(pkg["sidecar_files"]), 2)


if __name__ == "__main__":
    unittest.main()
