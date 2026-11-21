"""
Unit and Integration Tests for Part 14: Quality Control, Rendering & Delivery Studio.
Verifies all 35 required acceptance criteria across preflight inspection, render plan compilation,
hardware-accelerated encoding, QC defect detection, recovery, delivery packaging, and source preservation.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from uuid import UUID, uuid4

import numpy as np

from core.assets.database import AssetDatabase
import departments
from departments.quality_control.core.models import (
    QCCheckType,
    QCDefect,
    QCPolicy,
    QCReport,
    QCSeverity,
)
from departments.quality_control.inspectors.audio_validator import AudioValidator
from departments.quality_control.inspectors.color_validator import ColorValidator
from departments.quality_control.inspectors.file_integrity import FileIntegrityInspector
from departments.quality_control.inspectors.subtitle_validator import SubtitleValidator
from departments.quality_control.inspectors.video_validator import VideoValidator
from departments.quality_control.metrics.visual_metrics import VisualQualityAssessor
from departments.quality_control.rules.qc_policy_engine import QCPolicyEngine
from departments.quality_control.service import (
    IQualityControl,
    QualityControlRequest,
    QualityControlResponse,
    QualityControlService,
)
from departments.rendering_delivery.compiler.preflight import PreflightValidator
from departments.rendering_delivery.compiler.render_plan_compiler import RenderPlanCompiler
from departments.rendering_delivery.core.models import (
    DeliveryFile,
    DeliveryManifest,
    DeliveryPackage,
    ProfileCategory,
    RenderJob,
    RenderJobStatus,
    RenderPlan,
    RenderPlanStage,
    RenderProfile,
)
from departments.rendering_delivery.delivery.cost_manager import RenderCostManager
from departments.rendering_delivery.delivery.manifest_generator import DeliveryManifestGenerator
from departments.rendering_delivery.delivery.package_manager import DeliveryPackageManager
from departments.rendering_delivery.encoding.encoding_engine import EncodingEngine
from departments.rendering_delivery.encoding.timeline_adapter import TimelineAdapter
from departments.rendering_delivery.integrations.asset_store_bridge import AssetStoreBridge
from departments.rendering_delivery.integrations.dcc_render_bridge import DCCRenderBridge
from departments.rendering_delivery.integrations.timeline_render_bridge import TimelineRenderBridge
from departments.rendering_delivery.profiles.profile_registry import RenderProfileRegistry
from departments.rendering_delivery.queue.recovery_manager import RenderRecoveryManager
from departments.rendering_delivery.queue.render_queue_manager import RenderQueueManager
from departments.rendering_delivery.service import (
    IRenderingDelivery,
    RenderingDeliveryRequest,
    RenderingDeliveryResponse,
    RenderingDeliveryService,
)
from departments.rendering_delivery.workers.local_worker import LocalRenderWorker
from departments.rendering_delivery.workers.remote_worker import RemoteRenderWorker
from departments.rendering_delivery.workers.worker_manager import WorkerManager


class TestRenderingAndQCStudio(unittest.TestCase):
    """Test suite covering Part 14: Automated Quality Control, Rendering & Delivery."""

    @classmethod
    def setUpClass(cls):
        cls.project_id = uuid4()
        cls.temp_dir = tempfile.mkdtemp(prefix="test_rendering_qc_")
        cls.temp_db_path = os.path.join(cls.temp_dir, "test_render.db")
        cls.db = AssetDatabase(db_path=cls.temp_db_path)
        cls.db.create_project(cls.project_id, "Rendering Delivery Test Project")

        # Create valid source test media
        cls.sample_media_path = os.path.join(cls.temp_dir, "source_footage.mov")
        with open(cls.sample_media_path, "wb") as f:
            f.write(b"ORIGINAL_SOURCE_MEDIA_BYTE_STREAM_EXACT_UNALTERED")
        cls.initial_source_sha256 = FileIntegrityInspector.calculate_sha256(cls.sample_media_path)

        # Create test font and LUT
        cls.sample_font_path = os.path.join(cls.temp_dir, "Montserrat-Bold.ttf")
        with open(cls.sample_font_path, "wb") as f:
            f.write(b"FONT_FILE_DATA")

        cls.sample_lut_path = os.path.join(cls.temp_dir, "TealOrange.cube")
        with open(cls.sample_lut_path, "wb") as f:
            f.write(b"LUT_3D_DATA")

    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    # 1. Validate Complete Production Project
    def test_01_validate_complete_project(self):
        metadata = {
            "media_assets": [{"asset_id": "clip_1", "file_path": self.sample_media_path}],
            "fonts": ["Montserrat-Bold"],
            "font_paths": {"Montserrat-Bold": self.sample_font_path},
            "luts": [{"name": "TealOrange", "file_path": self.sample_lut_path}],
        }
        passed, issues = PreflightValidator.validate_project(metadata)
        self.assertTrue(passed)
        self.assertEqual(len(issues), 0)

    # 2. Detect Missing Source Media
    def test_02_detect_missing_source_media(self):
        metadata = {
            "media_assets": [{"asset_id": "clip_missing", "file_path": "/nonexistent/offline_clip.mp4"}],
        }
        passed, issues = PreflightValidator.validate_project(metadata)
        self.assertFalse(passed)
        self.assertTrue(any(i["category"] == "MEDIA_OFFLINE" for i in issues))

    # 3. Detect Missing Font
    def test_03_detect_missing_font(self):
        metadata = {
            "fonts": ["MissingCustomFont"],
            "font_paths": {"MissingCustomFont": "/nonexistent/font.ttf"},
        }
        passed, issues = PreflightValidator.validate_project(metadata)
        self.assertFalse(passed)
        self.assertTrue(any(i["category"] == "FONT_MISSING" for i in issues))

    # 4. Detect Missing LUT
    def test_04_detect_missing_lut(self):
        metadata = {
            "luts": [{"name": "MissingLUT", "file_path": "/nonexistent/lut.cube"}],
        }
        passed, issues = PreflightValidator.validate_project(metadata)
        self.assertFalse(passed)
        self.assertTrue(any(i["category"] == "LUT_MISSING" for i in issues))

    # 5. Compile Valid Render Plan
    def test_05_compile_valid_render_plan(self):
        metadata = {
            "media_assets": [{"asset_id": "clip_1", "file_path": self.sample_media_path}],
            "dcc_tasks": ["motion_graphics_intro"],
        }
        plan = RenderPlanCompiler.compile_plan(self.project_id, metadata, render_profile_id="youtube_1080p")
        self.assertIsInstance(plan, RenderPlan)
        self.assertTrue(len(plan.stages) >= 4)
        self.assertFalse(plan.requires_approval)

    # 6. Reject Invalid Render Plan
    def test_06_reject_invalid_render_plan(self):
        bad_meta = {
            "media_assets": [{"asset_id": "missing_asset", "file_path": "/bad/path.mov"}],
        }
        with self.assertRaises(ValueError):
            RenderPlanCompiler.compile_plan(self.project_id, bad_meta)

    # 7. Render Simple Video Sequence
    def test_07_render_simple_video_sequence(self):
        profile = RenderProfileRegistry.get_profile("youtube_1080p")
        self.assertIsNotNone(profile)
        output_file = os.path.join(self.temp_dir, "simple_render.mp4")
        res = EncodingEngine.execute_transcode(self.sample_media_path, output_file, profile)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertTrue(os.path.exists(output_file))

    # 8. Render Multitrack Sequence
    def test_08_render_multitrack_sequence(self):
        intermediate = os.path.join(self.temp_dir, "multitrack_intermediate.mov")
        res = TimelineAdapter.rasterize_timeline(self.project_id, {"tracks": 4}, intermediate)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertTrue(os.path.exists(intermediate))

    # 9. Render Sequence with Transitions
    def test_09_render_sequence_with_transitions(self):
        bridge = TimelineRenderBridge.rasterize_timeline_intermediate(
            self.project_id, uuid4(), os.path.join(self.temp_dir, "trans_intermediate.mov")
        )
        self.assertEqual(bridge["status"], "COMPLETED")
        self.assertEqual(bridge["format"], "prores_422_hq")

    # 10. Render Motion Graphics (Dept 09)
    def test_10_render_motion_graphics(self):
        res = DCCRenderBridge.dispatch_dcc_render("09_motion_graphics", self.project_id, {"scene": "intro"})
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["department"], "09_motion_graphics")

    # 11. Render VFX Composition (Dept 13)
    def test_11_render_vfx_composition(self):
        res = DCCRenderBridge.dispatch_dcc_render("13_vfx_compositing", self.project_id, {"shot": "vfx_01"})
        self.assertEqual(res["status"], "COMPLETED")

    # 12. Render 2D Animation Sequence (Dept 10)
    def test_12_render_2d_animation_sequence(self):
        res = DCCRenderBridge.dispatch_dcc_render("10_animation_2d", self.project_id, {"rig": "character_walk"})
        self.assertEqual(res["status"], "COMPLETED")

    # 13. Submit Part 09 3D Rendering Task
    def test_13_submit_3d_rendering_task(self):
        res = DCCRenderBridge.dispatch_dcc_render("11_animation_3d", self.project_id, {"usd_stage": "city.usd"})
        self.assertEqual(res["status"], "COMPLETED")

    # 14. Render Sequence with Graded Footage (Dept 16)
    def test_14_render_sequence_with_graded_footage(self):
        res = DCCRenderBridge.dispatch_dcc_render("16_color_restoration", self.project_id, {"grade": "kodak_2383"})
        self.assertEqual(res["status"], "COMPLETED")

    # 15. Render HDR Workflow Where Supported
    def test_15_render_hdr_workflow(self):
        hdr_profile = RenderProfile(
            profile_id="hdr10_master_4k",
            name="HDR10 Master 4K",
            category=ProfileCategory.MASTER,
            container="mov",
            video_codec="hevc",
            width=3840,
            height=2160,
            color_space="bt2020",
            transfer_characteristic="smpte2084",
            matrix_coefficients="bt2020nc",
        )
        cmd = EncodingEngine.build_ffmpeg_command("in.mov", "out.mov", hdr_profile)
        self.assertIn("smpte2084", cmd)
        self.assertIn("bt2020", cmd)

    # 16. Export Professional Master (ProRes 422 HQ)
    def test_16_export_professional_master(self):
        profile = RenderProfileRegistry.get_profile("prores_422_hq_master")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.container, "mov")
        self.assertEqual(profile.pixel_format, "yuv422p10le")
        cmd = EncodingEngine.build_ffmpeg_command("raw.mov", "master.mov", profile)
        self.assertIn("prores_ks", cmd)

    # 17. Export Social Media Delivery Profile
    def test_17_export_social_media_delivery_profile(self):
        reels_prof = RenderProfileRegistry.get_profile("instagram_reels_9_16")
        self.assertIsNotNone(reels_prof)
        self.assertEqual(reels_prof.width, 1080)
        self.assertEqual(reels_prof.height, 1920)
        self.assertTrue(reels_prof.faststart)

    # 18. Export Subtitles and Multiple Audio Tracks
    def test_18_export_subtitles_and_audio_tracks(self):
        master_file = os.path.join(self.temp_dir, "master_with_subs.mov")
        with open(master_file, "wb") as f:
            f.write(b"MASTER_VIDEO_STREAM")

        sub_file = os.path.join(self.temp_dir, "subtitles.vtt")
        with open(sub_file, "wb") as f:
            f.write(b"WEBVTT\n1\n00:00:00.000 --> 00:00:02.000\nHello")

        pkg = DeliveryPackageManager.assemble_package(
            project_id=self.project_id,
            render_job_id=uuid4(),
            master_file_path=master_file,
            sidecar_file_paths=[{"type": "SUBTITLE", "path": sub_file}],
            output_directory=os.path.join(self.temp_dir, "delivery_pkg"),
        )
        self.assertTrue(len(pkg.sidecar_files) >= 1)
        self.assertTrue(os.path.exists(pkg.manifest_path))

    # 19. Validate Audio Loudness (EBU R128)
    def test_19_validate_audio_loudness(self):
        # Passing loudness: -23.0 LUFS
        defects_pass = AudioValidator.validate_loudness_and_peaks(
            measured_lufs=-23.0, true_peak_db=-1.2, target_lufs=-23.0
        )
        self.assertEqual(len(defects_pass), 0)

        # Failing loudness: -17.0 LUFS (too loud for broadcast)
        defects_fail = AudioValidator.validate_loudness_and_peaks(
            measured_lufs=-17.0, true_peak_db=0.2, target_lufs=-23.0
        )
        self.assertTrue(any(d.rule_name == "loudness_conformance" for d in defects_fail))
        self.assertTrue(any(d.rule_name == "true_peak_limit" for d in defects_fail))

    # 20. Detect Black Frames
    def test_20_detect_black_frames(self):
        intervals = [(10.0, 11.2)]  # 1.2s black frame sequence
        defects = VideoValidator.detect_black_frames(intervals, max_allowed_black_sec=0.25)
        self.assertEqual(len(defects), 1)
        self.assertEqual(defects[0].rule_name, "black_frame_check")

    # 21. Detect Frozen Frames
    def test_21_detect_frozen_frames(self):
        intervals = [(5.0, 8.5)]  # 3.5s freeze
        defects = VideoValidator.detect_freeze_frames(intervals, max_allowed_frozen_sec=1.0)
        self.assertEqual(len(defects), 1)
        self.assertEqual(defects[0].rule_name, "freeze_frame_check")

    # 22. Detect Corrupted Media File
    def test_22_detect_corrupted_media_file(self):
        empty_file = os.path.join(self.temp_dir, "corrupt_empty.mov")
        with open(empty_file, "wb") as f:
            pass  # 0 bytes
        defects = FileIntegrityInspector.inspect_file(empty_file)
        self.assertTrue(any(d.rule_name == "file_not_empty" for d in defects))

    # 23. Detect Incorrect Resolution
    def test_23_detect_incorrect_resolution(self):
        defects = VideoValidator.validate_stream_properties(
            actual_width=1280, actual_height=720, actual_fps=24.0,
            expected_width=1920, expected_height=1080, expected_fps=24.0
        )
        self.assertTrue(any(d.rule_name == "resolution_conformance" for d in defects))

    # 24. Detect Incorrect Frame Rate
    def test_24_detect_incorrect_frame_rate(self):
        defects = VideoValidator.validate_stream_properties(
            actual_width=1920, actual_height=1080, actual_fps=29.97,
            expected_width=1920, expected_height=1080, expected_fps=24.0
        )
        self.assertTrue(any(d.rule_name == "framerate_conformance" for d in defects))

    # 25. Validate Color Metadata (NCLX)
    def test_25_validate_color_metadata(self):
        defects = ColorValidator.validate_color_metadata(
            actual_primaries="bt2020", actual_transfer="smpte2084", actual_matrix="bt2020nc",
            expected_primaries="bt709", expected_transfer="bt709", expected_matrix="bt709"
        )
        self.assertTrue(any(d.rule_name == "color_primaries_conformance" for d in defects))

    # 26. Validate Subtitle Timing
    def test_26_validate_subtitle_timing(self):
        bad_cues = [
            {"cue_index": 1, "start_time": 1.0, "end_time": 3.0, "text": "First cue"},
            {"cue_index": 2, "start_time": 2.5, "end_time": 4.0, "text": "Overlapping second cue"},
        ]
        defects = SubtitleValidator.audit_cues(bad_cues)
        self.assertTrue(any(d.rule_name == "subtitle_overlap" for d in defects))

    # 27. Detect Audio/Video Synchronization Errors
    def test_27_detect_av_sync_errors(self):
        # 100ms drift between video (10.0s) and audio (9.9s)
        defects = AudioValidator.validate_av_sync(video_duration_sec=10.0, audio_duration_sec=9.90, max_drift_sec=0.040)
        self.assertTrue(any(d.rule_name == "av_sync_drift" for d in defects))

    # 28. Generate QC Report
    def test_28_generate_qc_report(self):
        defects = [
            QCDefect(check_type=QCCheckType.VIDEO, severity=QCSeverity.WARNING, rule_name="soft_warning", description="Minor note.")
        ]
        report = QCPolicyEngine.compile_report(self.project_id, uuid4(), defects, policy_name="STREAMING_STANDARD")
        self.assertIsInstance(report, QCReport)
        self.assertTrue(report.passed)
        self.assertEqual(report.warning_count, 1)

    # 29. Fail Job When Critical QC Rule Fails
    def test_29_fail_job_when_critical_qc_rule_fails(self):
        critical_defects = [
            QCDefect(check_type=QCCheckType.VIDEO, severity=QCSeverity.CRITICAL, rule_name="resolution_mismatch", description="Fatal resolution mismatch.")
        ]
        report = QCPolicyEngine.compile_report(self.project_id, uuid4(), critical_defects, policy_name="STRICT_BROADCAST")
        self.assertFalse(report.passed)
        self.assertEqual(report.critical_count, 1)

    # 30. Recover Interrupted Render Job
    def test_30_recover_interrupted_render_job(self):
        recovery = RenderRecoveryManager()
        job = RenderJob(project_id=self.project_id, render_profile_id="youtube_1080p")
        recovery.record_checkpoint(job.job_id, "stage_01_dcc", "dcc_chunk_01.mov")
        self.assertTrue(recovery.can_recover(job.job_id))
        recovered_job = recovery.recover_job(job)
        self.assertEqual(recovered_job.status, RenderJobStatus.RUNNING)
        self.assertTrue(recovered_job.progress > 0.0)

    # 31. Retry Failed Task with Backoff
    def test_31_retry_failed_task_with_backoff(self):
        recovery = RenderRecoveryManager()
        can_retry_1, backoff_1 = recovery.retry_task_with_backoff(attempt=0)
        self.assertTrue(can_retry_1)
        self.assertEqual(backoff_1, 0.5)

        can_retry_2, backoff_2 = recovery.retry_task_with_backoff(attempt=1)
        self.assertTrue(can_retry_2)
        self.assertEqual(backoff_2, 1.0)

        can_retry_max, _ = recovery.retry_task_with_backoff(attempt=3, max_retries=3)
        self.assertFalse(can_retry_max)

    # 32. Validate Final File Checksum
    def test_32_validate_final_file_checksum(self):
        h = FileIntegrityInspector.calculate_sha256(self.sample_media_path)
        self.assertEqual(len(h), 64)
        defects = FileIntegrityInspector.inspect_file(self.sample_media_path, expected_checksum=h)
        self.assertEqual(len(defects), 0)

    # 33. Generate Delivery Manifest
    def test_33_generate_delivery_manifest(self):
        manifest_path = os.path.join(self.temp_dir, "test_manifest.json")
        DeliveryManifestGenerator.write_manifest(
            manifest_path=manifest_path,
            delivery_id="deliv_test_01",
            project_id=self.project_id,
            files=[{"file_path": "master.mov", "sha256": "abc"}],
            technical_specs={"resolution": "1920x1080"},
            qc_summary={"passed": True},
        )
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["delivery_id"], "deliv_test_01")
        self.assertTrue(data["qc_summary"]["passed"])

    # 34. Create Complete Delivery Package
    def test_34_create_complete_delivery_package(self):
        pkg = DeliveryPackageManager.assemble_package(
            project_id=self.project_id,
            render_job_id=uuid4(),
            master_file_path=self.sample_media_path,
            output_directory=os.path.join(self.temp_dir, "pkg_out"),
        )
        self.assertIsInstance(pkg, DeliveryPackage)
        self.assertTrue(os.path.exists(pkg.manifest_path))
        self.assertTrue(pkg.total_size_bytes > 0)

    # 35. Verify Original Source Media Remains Unchanged
    def test_35_verify_original_source_media_unchanged(self):
        current_sha256 = FileIntegrityInspector.calculate_sha256(self.sample_media_path)
        self.assertEqual(
            current_sha256,
            self.initial_source_sha256,
            "Source media was modified! Rendering must strictly preserve source files non-destructively."
        )


if __name__ == "__main__":
    unittest.main()

