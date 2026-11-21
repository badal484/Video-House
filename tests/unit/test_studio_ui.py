"""
Unit and integration test suite for Part 15:
Universal AI Video Production Studio User Interface, Creative Workspace & Project Management.
Validates all 35 acceptance requirements across frontend static delivery and backend API integration.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

import departments
from departments.studio_application.api import app, db as api_db, project_manager, studio_app


class TestStudioUI(unittest.TestCase):
    """
    35-checkpoint acceptance test suite for Department 01 (Studio Application)
    and Department 02 (Project Management).
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = tempfile.mkdtemp(prefix="studio_ui_test_")
        cls.db = api_db
        cls.project_service = project_manager
        cls.app_service = studio_app

        # Create dummy media file for upload & import tests
        cls.dummy_video_path = str(Path(cls.test_dir) / "sample_video.mp4")
        with open(cls.dummy_video_path, "wb") as f:
            f.write(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 100)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def create_test_project(self, name="Test Project", template="BLANK"):
        """Helper to create project directly in api.db via endpoint."""
        res = self.client.post("/api/v1/projects", json={
            "name": name,
            "settings": {"template": template, "current_stage": "PLANNING"}
        })
        self.assertEqual(res.status_code, 201)
        return res.json()["project_id"]

    # ---------------- 1. App Launch & Shell Static Delivery ----------------
    def test_01_launch_application_and_root_index(self):
        """1. Launch the application and verify root index.html serves cleanly."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Universal AI Video Production Studio", res.text)
        self.assertIn("data-theme=\"dark\"", res.text)
        self.assertIn("<header class=\"top-bar\">", res.text)

    def test_02_navigate_global_shell_assets(self):
        """2. Verify global shell static assets (CSS tokens, layout, components, JS app)."""
        css_assets = [
            "/ui/css/tokens.css",
            "/ui/css/layout.css",
            "/ui/css/components.css",
            "/ui/css/workspaces.css"
        ]
        for path in css_assets:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed to serve {path}")
            self.assertIn("text/css", res.headers.get("content-type", ""))

        js_assets = [
            "/ui/js/app.js",
            "/ui/js/tokens.js",
            "/ui/js/api_client.js",
            "/ui/js/state.js",
            "/ui/js/shortcuts.js"
        ]
        for path in js_assets:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Failed to serve {path}")
            self.assertIn("application/javascript", res.headers.get("content-type", ""))

    # ---------------- 2. Project Management Workflows ----------------
    def test_03_create_project(self):
        """3. Create a production project via REST endpoint."""
        payload = {
            "name": "Sci-Fi Cyberpunk Pilot",
            "settings": {"aspect_ratio": "16:9", "fps": 24.0, "color_space": "ACEScg"}
        }
        res = self.client.post("/api/v1/projects", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["name"], "Sci-Fi Cyberpunk Pilot")
        self.assertIn("project_id", data)

    def test_04_configure_project_settings(self):
        """4. Configure and update project settings (resolution, stage, color space)."""
        proj_id = self.create_test_project("Settings Test Proj")

        patch_payload = {
            "name": "Updated Title",
            "settings": {"width": 3840, "height": 2160, "fps": 23.976, "current_stage": "GENERATION"}
        }
        res = self.client.patch(f"/api/v1/projects/{proj_id}", json=patch_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "Updated Title")
        self.assertEqual(data["settings"]["fps"], 23.976)
        self.assertEqual(data["settings"]["current_stage"], "GENERATION")

    def test_05_open_existing_project(self):
        """5. Retrieve and open an existing project by UUID."""
        proj_id = self.create_test_project("Open Test Proj")

        res = self.client.get(f"/api/v1/projects/{proj_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["project_id"], proj_id)
        self.assertEqual(data["name"], "Open Test Proj")

    def test_06_list_production_templates(self):
        """6. List all predefined creative production templates."""
        res = self.client.get("/api/v1/projects/templates")
        self.assertEqual(res.status_code, 200)
        templates = res.json().get("templates", [])
        self.assertGreaterEqual(len(templates), 4)
        tmpl_ids = [t["template_id"] for t in templates]
        self.assertIn("YOUTUBE_16_9", tmpl_ids)
        self.assertIn("SOCIAL_VERTICAL_9_16", tmpl_ids)
        self.assertIn("CINEMATIC_2_39", tmpl_ids)
        self.assertIn("ANIME_2D", tmpl_ids)

    # ---------------- 3. Media Ingestion & Asset Browser ----------------
    def test_07_import_local_media_asset(self):
        """7. Import media into project using local file path."""
        proj_id = self.create_test_project("Import Test Proj")

        res = self.client.post(
            f"/api/v1/projects/{proj_id}/assets/import-local",
            json={
                "file_path": self.dummy_video_path,
                "display_name": "Camera_Take_01.mp4",
                "roles": ["SOURCE_FOOTAGE"]
            }
        )
        self.assertEqual(res.status_code, 202)
        data = res.json()
        self.assertIn("asset_id", data)

    def test_08_browse_project_assets(self):
        """8. Browse media assets in project and inspect metadata."""
        proj_id = self.create_test_project("Browse Test Proj")
        self.client.post(
            f"/api/v1/projects/{proj_id}/assets/import-local",
            json={"file_path": self.dummy_video_path, "display_name": "Test_Clip.mp4"}
        )

        res = self.client.get(f"/api/v1/projects/{proj_id}/assets")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("assets", data)
        self.assertGreaterEqual(len(data["assets"]), 1)

    # ---------------- 4. Media Preview & Monitoring ----------------
    def test_09_preview_video_endpoint_handling(self):
        """9. Preview media stream endpoint returns 404 for missing asset."""
        missing_id = uuid4()
        res = self.client.get(f"/api/v1/media/stream/{missing_id}")
        self.assertEqual(res.status_code, 404)

    def test_10_preview_derivative_endpoint_handling(self):
        """10. Preview derivative endpoint returns 404 for missing derivative."""
        missing_id = uuid4()
        res = self.client.get(f"/api/v1/media/derivative/{missing_id}")
        self.assertEqual(res.status_code, 404)

    # ---------------- 5. Editing Workspace & OTIO Timeline ----------------
    def test_11_open_editing_workspace_create_timeline(self):
        """11. Create and initialize an OpenTimelineIO timeline."""
        proj_id = self.create_test_project("Timeline Test Proj")

        res = self.client.post(
            f"/api/v1/editing/projects/{proj_id}/timelines",
            json={"name": "Sequence 01", "fps": 24.0}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("timeline", data)

    def test_12_load_timeline_details(self):
        """12. Retrieve timeline tracks, clips, and duration."""
        proj_id = self.create_test_project("Load TL Proj")
        create_res = self.client.post(
            f"/api/v1/editing/projects/{proj_id}/timelines",
            json={"name": "Master Cut", "fps": 24.0}
        )
        tl_id = create_res.json()["timeline"]["timeline_id"]

        res = self.client.get(f"/api/v1/editing/timelines/{tl_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["timeline"]["timeline_id"], tl_id)

    def test_13_timeline_split_clip_operation(self):
        """13. Perform blade/split cut on timeline clip (404 on missing clip)."""
        missing_tl = uuid4()
        missing_clip = uuid4()
        res = self.client.post(
            f"/api/v1/editing/timelines/{missing_tl}/clips/{missing_clip}/split",
            json={"split_time_sec": 5.0}
        )
        self.assertEqual(res.status_code, 404)

    def test_14_timeline_ripple_delete_operation(self):
        """14. Perform ripple-delete on timeline clip (404 on missing clip)."""
        missing_tl = uuid4()
        missing_clip = uuid4()
        res = self.client.post(f"/api/v1/editing/timelines/{missing_tl}/clips/{missing_clip}/ripple-delete")
        self.assertEqual(res.status_code, 404)

    # ---------------- 6. AI Director & Creative Planning ----------------
    def test_15_ai_director_submit_brief(self):
        """15. Submit natural language creative brief to AI Director."""
        proj_id = self.create_test_project("Director Brief Proj")

        res = self.client.post(
            f"/api/v1/projects/{proj_id}/creative/brief",
            json={
                "prompt": "Create an energetic 30s product commercial for an electric hypercar.",
                "genre": "Commercial",
                "visual_style": "High-Contrast Neon",
                "target_duration_sec": 30.0
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("brief_id", data)

    def test_16_ai_director_generate_concepts(self):
        """16. Generate creative concepts from brief."""
        proj_id = self.create_test_project("Director Concept Proj")
        self.client.post(f"/api/v1/projects/{proj_id}/creative/brief", json={"prompt": "Short film idea"})

        res = self.client.post(f"/api/v1/projects/{proj_id}/creative/concepts")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("concepts", data)
        self.assertGreaterEqual(len(data["concepts"]), 1)

    def test_17_ai_director_create_screenplay_script(self):
        """17. Generate screenplay script breakdown."""
        proj_id = self.create_test_project("Script Proj")
        self.client.post(f"/api/v1/projects/{proj_id}/creative/brief", json={"prompt": "Action film"})

        res = self.client.post(f"/api/v1/projects/{proj_id}/creative/script", json={})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("script_id", data)

    def test_18_ai_director_generate_visual_storyboard(self):
        """18. Generate visual storyboard shot deck."""
        proj_id = self.create_test_project("Storyboard Proj")
        self.client.post(f"/api/v1/projects/{proj_id}/creative/brief", json={"prompt": "Documentary teaser"})
        self.client.post(f"/api/v1/projects/{proj_id}/creative/script", json={})
        self.client.post(f"/api/v1/projects/{proj_id}/creative/shots", json={})

        res = self.client.post(f"/api/v1/projects/{proj_id}/creative/storyboard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("frames", data)

    # ---------------- 7. Agent Control Center & Telemetry ----------------
    def test_19_agent_control_center_telemetry(self):
        """19. Retrieve system telemetry, Apple Silicon status, and disk space."""
        res = self.client.get("/api/v1/system/telemetry")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertIn("storage", data)
        self.assertIn("videotoolbox_acceleration", data)

    def test_20_workspace_layout_persistence(self):
        """20. Save and retrieve customized workspace panel layouts."""
        layout_payload = {
            "layout": {"left_panel_width": 320, "right_panel_width": 380, "bottom_panel_height": 300}
        }
        post_res = self.client.post("/api/v1/system/layout/creative", json=layout_payload)
        self.assertEqual(post_res.status_code, 200)

        get_res = self.client.get("/api/v1/system/layout/creative")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.json()
        self.assertEqual(data["layout"]["left_panel_width"], 320)

    # ---------------- 8. Generative Studio Interface ----------------
    def test_21_generation_prompt_compiler(self):
        """21. Compile multi-dimensional prompt into Runway and FLUX dialects."""
        payload = {
            "dimensions": {
                "subject": "Cyberpunk operative in titanium armor",
                "action": "sprinting through rain",
                "camera": "low angle fast track right",
                "lighting": "neon reflections",
                "mood_style": "cinematic"
            },
            "provider_id": "runway_gen3"
        }
        res = self.client.post("/api/v1/generation/compile-prompt", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("compiled_positive_prompt", data)
        self.assertIn("compiled_negative_prompt", data)

    def test_22_generation_provider_registry(self):
        """22. Query registered multimodal generative providers."""
        res = self.client.get("/api/v1/generation/providers")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("providers", data)
        self.assertGreaterEqual(len(data["providers"]), 1)

    # ---------------- 9. Motion Graphics Workspace ----------------
    def test_23_motion_graphics_preset_library(self):
        """23. Query available declarative motion graphics presets."""
        res = self.client.get("/api/v1/motion-graphics/presets")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("presets", data)
        self.assertGreaterEqual(len(data["presets"]), 1)

    def test_24_motion_graphics_instantiate_preset(self):
        """24. Instantiate a motion preset with dynamic text."""
        proj_id = self.create_test_project("Motion Proj")
        res = self.client.get("/api/v1/motion-graphics/presets")
        presets = res.json().get("presets", [])
        if presets:
            preset_id = presets[0]["preset_id"]
            inst_res = self.client.post(
                f"/api/v1/motion-graphics/presets/{preset_id}/instantiate",
                json={
                    "project_id": proj_id,
                    "parameters": {"title_text": "UNIVERSAL STUDIO", "subtitle_text": "AI NLE"}
                }
            )
            self.assertEqual(inst_res.status_code, 200)
            self.assertIn("composition", inst_res.json())

    # ---------------- 10. VFX Workspace ----------------
    def test_25_vfx_project_creation(self):
        """25. Create VFX project container and verify graph schema."""
        proj_id = self.create_test_project("VFX Test Proj")

        res = self.client.post(
            "/api/v1/vfx/projects",
            json={
                "project_id": proj_id,
                "name": "Compositing Pass",
                "width": 1920,
                "height": 1080,
                "fps": 24.0
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("vfx_project", data)
        self.assertIn("vfx_project_id", data["vfx_project"])

    # ---------------- 11. 2D Animation Workspace ----------------
    def test_26_animation_character_creation(self):
        """26. Create structured character concept for 2D animation."""
        proj_id = self.create_test_project("Anim Test Proj")

        res = self.client.post(
            "/api/v1/animation/characters",
            json={
                "project_id": str(proj_id),
                "name": "Ren",
                "brief": "Cyber Ronin with black spiky hair and amber eyes",
                "visual_style": "ANIME_CEL"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("character", data)
        self.assertIn("character_id", data["character"])

    # ---------------- 12. Audio Workspace ----------------
    def test_27_audio_session_creation(self):
        """27. Create multitrack DAW session with master bus."""
        proj_id = self.create_test_project("Audio Test Proj")

        res = self.client.post(
            "/api/v1/audio/sessions",
            json={
                "project_id": proj_id,
                "name": "Film Audio Session",
                "sample_rate": 48000,
                "target_lufs": -14.0
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("session", data)
        self.assertIn("session_id", data["session"])

    def test_28_audio_procedural_sfx_generation(self):
        """28. Synthesize 100% royalty-free procedural sound effect."""
        res = self.client.post(
            "/api/v1/audio/sfx/generate",
            json={
                "sfx_type": "whoosh",
                "duration_sec": 1.5
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("output_path", data)
        self.assertEqual(data["duration_sec"], 1.5)

    # ---------------- 13. Color Grading Workspace ----------------
    def test_29_color_grading_recommendation(self):
        """29. Get AI Colorist recommendation for shot styling."""
        proj_id = self.create_test_project("Color Test Proj")

        res = self.client.post(
            "/api/v1/color/recommend-grade",
            json={
                "project_id": proj_id,
                "asset_id": str(uuid4()),
                "look_style": "TEAL_AND_ORANGE"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("recommended_graph", data)

    # ---------------- 14. Localization Workspace ----------------
    def test_30_localization_subtitle_generation(self):
        """30. Generate broadcast-compliant subtitle cues (SRT/VTT)."""
        proj_id = self.create_test_project("Subtitles Proj")
        payload = {
            "project_id": proj_id,
            "segments": [
                {
                    "segment_id": "seg_01",
                    "text": "The quantum core is fully operational.",
                    "start_time": 1.0,
                    "end_time": 3.5,
                    "speaker_id": "spk_1"
                }
            ],
            "format": "srt",
            "style_preset": "cinematic"
        }
        res = self.client.post("/api/v1/localization/subtitles", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])

    # ---------------- 15. Rendering, QC & Delivery ----------------
    def test_31_rendering_profiles_list(self):
        """31. List industry-standard render and delivery profiles."""
        res = self.client.get("/api/v1/rendering/profiles")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("profiles", data)
        profile_names = [p["name"] for p in data["profiles"]]
        self.assertTrue(any("ProRes 422 HQ" in name for name in profile_names))
        self.assertTrue(any("YouTube 1080p" in name for name in profile_names))

    def test_32_render_plan_compilation_and_cost(self):
        """32. Compile render plan DAG and calculate compute cost."""
        proj_id = self.create_test_project("Render Plan Proj")

        res = self.client.post(
            "/api/v1/rendering/plan",
            json={
                "project_id": proj_id,
                "render_profile_id": "youtube_1080p"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("render_plan", data["data"])

    def test_33_automated_qc_audit_execution(self):
        """33. Run automated technical quality control audit."""
        proj_id = self.create_test_project("QC Audit Proj")

        res = self.client.post(
            "/api/v1/qc/audit",
            json={
                "project_id": proj_id,
                "file_path": self.dummy_video_path,
                "policy_name": "STREAMING_STANDARD"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])

    # ---------------- 16. Versioning, Recovery & Cleanup ----------------
    def test_34_project_version_snapshot_and_restore(self):
        """34. Create project version milestone and restore previous snapshot."""
        proj_id = self.create_test_project("Version Proj")

        # Save snapshot
        ver_res = self.client.post(
            f"/api/v1/projects/{proj_id}/versions",
            json={"version_name": "Milestone v1.0", "notes": "Initial rough cut"}
        )
        self.assertEqual(ver_res.status_code, 200)
        ver_id = ver_res.json()["version_id"]

        # List versions
        list_res = self.client.get(f"/api/v1/projects/{proj_id}/versions")
        self.assertEqual(list_res.status_code, 200)
        self.assertGreaterEqual(len(list_res.json()["versions"]), 1)

        # Restore snapshot
        restore_res = self.client.post(f"/api/v1/projects/{proj_id}/versions/{ver_id}/restore")
        self.assertEqual(restore_res.status_code, 200)
        self.assertEqual(restore_res.json()["restored_version_id"], ver_id)

    def test_35_project_deletion_cleanup(self):
        """35. Delete project and verify cascade cleanup."""
        proj_id = self.create_test_project("Delete Target Proj")

        del_res = self.client.delete(f"/api/v1/projects/{proj_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # Confirm 404 on subsequent get
        get_res = self.client.get(f"/api/v1/projects/{proj_id}")
        self.assertEqual(get_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
