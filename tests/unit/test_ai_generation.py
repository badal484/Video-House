"""
Comprehensive Unit Test Suite for Department 15: AI Video, Image, Voice & Music Generation Studio
Validates all 20 architectural checkpoints: provider registry, model specs, prompt compiler,
asynchronous job execution, budget firewalls, quality control, character consistency, and pipeline bridges.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import unittest
import uuid
import numpy as np

from core.assets.database import AssetDatabase
import departments
from departments.ai_generation.core.generation_models import (
    GenerationModality,
    GenerationRequest,
    GenerationResult,
    JobStatus,
    ModelSpec,
    ProviderSpec,
    ReferenceAssetBinding,
    ReferenceCategory,
    ValidationStatus,
)
from departments.ai_generation.core.character_profile import (
    CharacterReferenceProfile,
    EnvironmentReferenceProfile,
)
from departments.ai_generation.prompts.prompt_compiler import (
    PromptCompiler,
    StructuredPromptDimensions,
)
from departments.ai_generation.providers.registry import ProviderRegistry
from departments.ai_generation.providers.mock_provider import MockLocalProvider
from departments.ai_generation.providers.runway_adapter import RunwayAdapter
from departments.ai_generation.providers.kling_adapter import KlingAdapter
from departments.ai_generation.providers.flux_adapter import FluxAdapter
from departments.ai_generation.router.generation_router import GenerationRouter
from departments.ai_generation.router.cost_estimator import GenerationBudgetManager
from departments.ai_generation.orchestration.job_queue import GenerationJobQueue
from departments.ai_generation.qc.media_validator import MediaValidator
from departments.ai_generation.approval.approval_gate import (
    ApprovalGateManager,
    ApprovalStatus,
)
from departments.ai_generation.integrations.director_bridge import DirectorGenerationBridge
from departments.ai_generation.integrations.asset_bridge import AssetStoreBridge
from departments.ai_generation.integrations.timeline_bridge import TimelineGenerationBridge
from departments.ai_generation.service import AIGenerationService
from departments.ai_generation.interface import AIGenerationRequest


class TestAIGenerationStudio(unittest.TestCase):
    """Test suite for Department 15 AI Generation Studio."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="ai_gen_test_")
        cls.artifact_dir = "test_artifacts/generation"
        os.makedirs(cls.artifact_dir, exist_ok=True)

        cls.db_path = os.path.join(cls.test_dir, "test_generation.db")
        cls.db = AssetDatabase(cls.db_path)
        cls.project_id = "test_gen_project"
        cls.db.create_project(cls.project_id, "Generation Test Project")

        cls.registry = ProviderRegistry(register_defaults=True)
        cls.router = GenerationRouter(cls.registry)
        cls.budget_mgr = GenerationBudgetManager()
        cls.job_queue = GenerationJobQueue(cls.registry, cls.router, cls.budget_mgr)
        cls.approval_gate = ApprovalGateManager(high_cost_threshold_usd=1.00)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_register_provider(self):
        """1. Register a generation provider and inspect specs."""
        providers = self.registry.list_providers()
        provider_ids = [p.provider_id for p in providers]
        self.assertIn("mock_local_engine", provider_ids)
        self.assertIn("runway_gen3", provider_ids)
        self.assertIn("flux_engine", provider_ids)

    def test_02_register_model_and_capabilities(self):
        """2. Register a model specification and query by modality."""
        spec = ModelSpec(
            model_id="flux_1_pro_v1",
            provider_id="flux_engine",
            name="FLUX.1 Pro",
            version="1.0",
            modality=GenerationModality.TEXT_TO_IMAGE,
            is_commercial_cleared=True,
            pricing_per_call=0.04,
        )
        self.registry.register_model(spec)
        found = self.registry.get_model("flux_1_pro_v1")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "FLUX.1 Pro")
        self.assertTrue(found.is_commercial_cleared)

    def test_03_reject_unsupported_generation_request(self):
        """3. Reject an unsupported generation request."""
        runway = self.registry.get_provider("runway_gen3")
        self.assertIsNotNone(runway)

        # Runway does not support text-to-music
        invalid_req = GenerationRequest(
            project_id=self.project_id,
            modality=GenerationModality.TEXT_TO_MUSIC,
            raw_prompt="Orchestral soundtrack",
        )
        valid, err = runway.validate_request(invalid_req)
        self.assertFalse(valid)
        self.assertIn("does not support modality", err)

        # Runway exceeds max duration (10s limit)
        too_long_req = GenerationRequest(
            project_id=self.project_id,
            modality=GenerationModality.TEXT_TO_VIDEO,
            raw_prompt="Long shot",
            duration_sec=45.0,
        )
        valid_dur, err_dur = runway.validate_request(too_long_req)
        self.assertFalse(valid_dur)
        self.assertIn("exceeds provider limit", err_dur)

    def test_04_structured_prompt_compilation(self):
        """4. Compile a structured prompt into Runway and FLUX specific syntax."""
        dims = StructuredPromptDimensions(
            subject="Cyberpunk detective",
            character_identity="Captain Maya Lin with eye scar",
            action="walking through crowded rain-slicked alley",
            environment="Neo-Tokyo metropolis",
            composition="low angle medium shot",
            camera_movement="slow dolly forward",
            lighting="high contrast neon backlight",
            visual_style="cinematic 35mm film grain",
            aspect_ratio="16:9",
        )

        # Compile for Runway
        runway_pos, runway_neg = PromptCompiler.compile_for_provider(dims, "runway_gen3")
        self.assertIn("[Camera: slow dolly forward, low angle medium shot]", runway_pos)
        self.assertIn("Cyberpunk detective", runway_pos)
        self.assertIn("blurry", runway_neg)

        # Compile for FLUX
        flux_pos, flux_neg = PromptCompiler.compile_for_provider(dims, "flux_engine")
        self.assertIn("A high-fidelity photograph of Cyberpunk detective", flux_pos)
        self.assertIn("high contrast neon backlight", flux_pos)

    def test_05_submit_text_to_image_request(self):
        """5. Submit a text-to-image generation request via mock provider."""
        req = GenerationRequest(
            project_id=self.project_id,
            shot_id="shot_concept_1",
            modality=GenerationModality.TEXT_TO_IMAGE,
            raw_prompt="Futuristic city skyline at sunset",
            aspect_ratio="16:9",
            preferred_provider="mock_local_engine",
        )
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(self.job_queue.submit_request(req))
        loop.close()

        self.assertEqual(res.status, JobStatus.SUCCEEDED)
        self.assertTrue(len(res.output_file_paths) > 0)
        self.assertTrue(os.path.exists(res.output_file_paths[0]))
        # Copy to artifact dir
        dest = os.path.join(self.artifact_dir, "test_generated_image.png")
        shutil.copyfile(res.output_file_paths[0], dest)
        self.assertTrue(os.path.exists(dest))

    def test_06_submit_text_to_video_request(self):
        """6. Submit a text-to-video generation request."""
        req = GenerationRequest(
            project_id=self.project_id,
            shot_id="shot_vid_1",
            modality=GenerationModality.TEXT_TO_VIDEO,
            raw_prompt="Spaceship landing in desert",
            duration_sec=1.0,
            preferred_provider="mock_local_engine",
        )
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(self.job_queue.submit_request(req))
        loop.close()

        self.assertEqual(res.status, JobStatus.SUCCEEDED)
        self.assertTrue(len(res.output_file_paths) > 0)
        self.assertTrue(os.path.exists(res.output_file_paths[0]))
        dest = os.path.join(self.artifact_dir, "test_generated_video.mp4")
        shutil.copyfile(res.output_file_paths[0], dest)

    def test_07_submit_image_to_video_request(self):
        """7. Submit an image-to-video request conditioned on reference asset."""
        ref_image = ReferenceAssetBinding(
            asset_id=str(uuid.uuid4()),
            category=ReferenceCategory.COMPOSITION,
            weight=1.0,
            file_path=os.path.join(self.artifact_dir, "test_generated_image.png"),
        )
        req = GenerationRequest(
            project_id=self.project_id,
            modality=GenerationModality.IMAGE_TO_VIDEO,
            raw_prompt="Camera zooms in smoothly toward the central tower",
            reference_assets=[ref_image],
            preferred_provider="mock_local_engine",
        )
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(self.job_queue.submit_request(req))
        loop.close()

        self.assertEqual(res.status, JobStatus.SUCCEEDED)
        self.assertEqual(res.validation_status, ValidationStatus.PASSED)

    def test_08_async_job_queue_and_idempotency(self):
        """8. Test job queue execution and idempotency caching."""
        req = GenerationRequest(
            project_id=self.project_id,
            shot_id="shot_idemp_1",
            modality=GenerationModality.TEXT_TO_IMAGE,
            raw_prompt="Identical creative prompt test",
            seed=42,
            preferred_provider="mock_local_engine",
        )
        loop = asyncio.new_event_loop()
        res1 = loop.run_until_complete(self.job_queue.submit_request(req))
        # Submit second identical request
        res2 = loop.run_until_complete(self.job_queue.submit_request(req))
        loop.close()

        # Idempotency cache should return the exact same job ID
        self.assertEqual(res1.job_id, res2.job_id)

    def test_09_provider_failure_handling(self):
        """9. Provider failure handling when credentials are missing."""
        # Force Runway adapter with no API key
        runway = RunwayAdapter(api_key=None)
        req = GenerationRequest(
            project_id=self.project_id,
            modality=GenerationModality.TEXT_TO_VIDEO,
            raw_prompt="Cinematic shot requiring commercial key",
        )
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(runway.submit_job(req))
        loop.close()

        self.assertEqual(res.status, JobStatus.FAILED)
        self.assertIn("RUNWAY_API_KEY", res.error_message)

    def test_10_cancel_generation_job(self):
        """10. Job cancellation workflow."""
        mock = MockLocalProvider()
        req = GenerationRequest(
            project_id=self.project_id,
            modality=GenerationModality.TEXT_TO_IMAGE,
            raw_prompt="Job to cancel",
        )
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(mock.submit_job(req))
        cancelled = loop.run_until_complete(mock.cancel_job(res.job_id))
        loop.close()

        self.assertTrue(cancelled)
        self.assertEqual(mock._jobs[res.job_id].status, JobStatus.CANCELLED)

    def test_11_media_quality_control_validation(self):
        """11. Video, Image, and Audio quality control validation."""
        # 1. Video validation
        test_video = os.path.join(self.artifact_dir, "test_generated_video.mp4")
        v_status, v_diag = MediaValidator.validate_video_file(test_video)
        self.assertIn(v_status, (ValidationStatus.PASSED, ValidationStatus.WARNING))
        self.assertIn("resolution", v_diag)

        # 2. Image validation
        test_img = os.path.join(self.artifact_dir, "test_generated_image.png")
        i_status, i_diag = MediaValidator.validate_image_file(test_img)
        self.assertIn(i_status, (ValidationStatus.PASSED, ValidationStatus.WARNING))

        # 3. Audio validation
        mock_audio = os.path.join(self.test_dir, "valid_audio.wav")
        import scipy.io.wavfile
        sr = 48000
        t = np.linspace(0.0, 0.5, sr // 2, endpoint=False)
        tone = (0.2 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        scipy.io.wavfile.write(mock_audio, sr, tone)
        a_status, a_diag = MediaValidator.validate_audio_file(mock_audio)
        self.assertEqual(a_status, ValidationStatus.PASSED)
        self.assertEqual(a_diag["sample_rate"], 48000)

    def test_12_register_output_in_asset_store(self):
        """12. Commit generated output to persistent Central Asset Database."""
        test_audio = os.path.join(self.test_dir, "valid_audio.wav")
        result = GenerationResult(
            request_id=str(uuid.uuid4()),
            project_id=self.project_id,
            status=JobStatus.SUCCEEDED,
            provider_id="mock_local_engine",
            model_id="mock_v1",
            output_asset_ids=[str(uuid.uuid4())],
            output_file_paths=[test_audio],
            validation_status=ValidationStatus.PASSED,
        )
        asset_ids = AssetStoreBridge.register_result_as_asset(self.db, result, "SFX Boom")
        self.assertEqual(len(asset_ids), 1)

    def test_13_cost_estimation_and_budget_tracking(self):
        """13. Cost calculation and budget spending record."""
        bm = GenerationBudgetManager()
        bm.set_project_budget("proj_indie", ceiling_usd=50.0)

        # Check before spend
        status_init = bm.get_budget_status("proj_indie")
        self.assertEqual(status_init["ceiling_usd"], 50.0)
        self.assertEqual(status_init["spent_usd"], 0.0)

        # Record generation expense ($1.50)
        bm.record_spend("proj_indie", 1.50)
        status_after = bm.get_budget_status("proj_indie")
        self.assertEqual(status_after["spent_usd"], 1.50)
        self.assertEqual(status_after["remaining_usd"], 48.50)

    def test_14_budget_ceiling_firewall(self):
        """14. Budget firewall blocks generation when project ceiling exceeded."""
        bm = GenerationBudgetManager()
        bm.set_project_budget("proj_tight", ceiling_usd=2.00)
        bm.record_spend("proj_tight", 1.80)

        # Attempt to spend $0.50 with only $0.20 remaining
        ok, msg = bm.check_budget("proj_tight", 0.50)
        self.assertFalse(ok)
        self.assertIn("exceeds remaining project budget", msg)

    def test_15_human_approval_gate_high_cost(self):
        """15. Human approval gate triggers on high cost generations (> $1.00)."""
        gate = ApprovalGateManager(high_cost_threshold_usd=1.00)
        req_cheap = GenerationRequest(
            project_id=self.project_id,
            raw_prompt="Quick draft",
            estimated_cost_usd=0.25,
        )
        needed_cheap, _ = gate.requires_approval(req_cheap)
        self.assertFalse(needed_cheap)

        req_expensive = GenerationRequest(
            project_id=self.project_id,
            raw_prompt="10-second 4K IMAX cinematic shot",
            estimated_cost_usd=2.50,
        )
        needed_exp, reason = gate.requires_approval(req_expensive)
        self.assertTrue(needed_exp)
        self.assertIn("exceeds high-cost threshold", reason)

        ticket = gate.create_ticket(req_expensive, reason)
        self.assertEqual(ticket.status, ApprovalStatus.PENDING)

        # Director approves
        approved_ticket = gate.approve_ticket(ticket.ticket_id, "Approved by executive producer")
        self.assertEqual(approved_ticket.status, ApprovalStatus.APPROVED)

    def test_16_character_reference_profile_persistence(self):
        """16. Character reference profile creation and database persistence."""
        char = CharacterReferenceProfile(
            project_id=self.project_id,
            name="Commander Jax",
            hairstyle="military buzz cut",
            clothing="tactical exo-rig",
            distinguishing_features=["cybernetic right eye", "chin scar"],
            negative_identity_prompt="long hair, beard, glasses",
        )
        self.db.save_generation_character_profile(char)

        loaded = self.db.get_generation_character_profile(char.character_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["name"], "Commander Jax")
        self.assertIn("cybernetic right eye", loaded["data"]["distinguishing_features"])

    def test_17_environment_reference_profile(self):
        """17. Environment reference profile creation and serialization."""
        env = EnvironmentReferenceProfile(
            project_id=self.project_id,
            name="Subterranean Ice Cavern",
            architecture_style="natural basalt columns coated in glacial ice",
            lighting_profile="bioluminescent cyan crystals",
            color_palette=["#00F0FF", "#0A192F", "#E0F7FA"],
            time_of_day="perpetual dark",
        )
        env_dict = env.to_dict()
        self.assertEqual(env_dict["name"], "Subterranean Ice Cavern")
        self.assertEqual(len(env_dict["color_palette"]), 3)

    def test_18_director_blueprint_to_generation_requests(self):
        """18. AI Director ProductionBlueprint cue parsing and request batch generation."""
        blueprint = {
            "title": "Sci-Fi Short Scene 1",
            "aspect_ratio": "2.39:1",
            "visual_style": "gritty cinematic 35mm",
            "scenes": [
                {
                    "scene_id": "sc_01",
                    "planned_shots": [
                        {
                            "shot_id": "sh_01",
                            "subject": "Armored rover",
                            "environment": "Martian crater",
                            "framing": "extreme wide shot",
                            "camera_movement": "crane down",
                            "duration_sec": 5.0,
                        },
                        {
                            "shot_id": "sh_02",
                            "subject": "Astronaut emerges from airlock",
                            "framing": "medium close up",
                            "camera_movement": "dolly in",
                            "duration_sec": 3.5,
                        },
                    ],
                }
            ],
        }
        requests = DirectorGenerationBridge.compile_planned_shots_to_requests(blueprint, self.project_id)
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].shot_id, "sh_01")
        self.assertEqual(requests[0].aspect_ratio, "2.39:1")
        self.assertIn("Armored rover", requests[0].compiled_prompt)
        self.assertEqual(requests[1].shot_id, "sh_02")
        self.assertAlmostEqual(requests[1].duration_sec, 3.5)

    def test_19_timeline_generation_bridge(self):
        """19. Conforming generated clip manifests for OpenTimelineIO tracks."""
        clip_manifest = TimelineGenerationBridge.format_clip_for_timeline(
            asset_id=str(uuid.uuid4()),
            name="V1_Generated_Shot_01",
            duration_sec=4.0,
            start_time_sec=2.5,
            fps=24,
        )
        self.assertEqual(clip_manifest["name"], "V1_Generated_Shot_01")
        self.assertEqual(clip_manifest["timeline_range"]["duration"].to_seconds(), 4.0)
        self.assertAlmostEqual(clip_manifest["timeline_range"]["start_time"].to_seconds(), 2.5)

    def test_20_service_execution_contract(self):
        """20. Department 15 Service interface execution and health check."""
        svc = AIGenerationService(output_root=os.path.join(self.artifact_dir, "svc_scratch"))
        self.assertTrue(svc.health_check())

        # Submit request through typed service interface
        req = AIGenerationRequest(
            project_id=uuid.uuid4(),
            parameters={
                "action": "submit_job",
                "modality": "TEXT_TO_IMAGE",
                "prompt": "Golden hour mountain panorama",
                "preferred_provider": "mock_local_engine",
            },
        )
        loop = asyncio.new_event_loop()
        resp = loop.run_until_complete(svc.execute(req))
        self.assertTrue(resp.success)
        self.assertIn("job_id", resp.data)

        # Poll job
        poll_req = AIGenerationRequest(
            project_id=uuid.uuid4(),
            parameters={
                "action": "poll_job",
                "job_id": resp.data["job_id"],
            },
        )
        poll_resp = loop.run_until_complete(svc.execute(poll_req))
        self.assertTrue(poll_resp.success)
        self.assertEqual(poll_resp.data["status"], JobStatus.SUCCEEDED.value)

        # Compile prompt action
        compile_req = AIGenerationRequest(
            project_id=uuid.uuid4(),
            parameters={
                "action": "compile_prompt",
                "dimensions": {
                    "subject": "Astronaut on alien planet",
                    "camera_movement": "orbital pan",
                },
                "provider_id": "runway_gen3",
            },
        )
        compile_resp = loop.run_until_complete(svc.execute(compile_req))
        loop.close()
        self.assertTrue(compile_resp.success)
        self.assertIn("Astronaut on alien planet", compile_resp.data["compiled_positive_prompt"])


if __name__ == "__main__":
    unittest.main()
