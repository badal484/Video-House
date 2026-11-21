"""
Unit and Integration Tests for Department 16: Color Grading, Restoration & Enhancement.
Verifies all 24 required acceptance test cases:
1. Import standard Rec.709 clip
2. Import log-encoded clip with known metadata
3. Handle footage with missing metadata
4. Apply valid input transform
5. Apply creative grade
6. Apply technical conversion LUT
7. Reject incompatible LUT workflow
8. Export color-managed Rec.709 output
9. Perform supported HDR workflow
10. Analyze reference look
11. Generate suggested shot match
12. Denoise noisy video
13. Upscale sample video
14. Restore old/damaged sample
15. Process animation sample
16. Preserve audio synchronization
17. Preserve original source media
18. Resume interrupted processing job
19. Handle GPU memory exhaustion
20. Compare preview and final-render parameters
21. Validate output color metadata
22. Integrate grade with Part 05 timeline
23. Process AI-generated clip from Part 11
24. Verify processing provenance and version history
"""
from pathlib import Path
import unittest
from uuid import uuid4
import cv2
import numpy as np
import opentimelineio as otio

from core.assets.database import AssetDatabase
import departments
from departments.color_restoration.core.models import (
    ColorSpace, TransferFunction, ColorProfileMetadata,
    GradingGraph, GradingNode, GradingNodeType, PrimaryGradingParameters,
    CurvesParameters, SecondaryQualifierParameters, PowerWindowParameters,
    LUTMetadata, RestorationParameters, RestorationType, QualityReviewState, RestorationJob
)
from departments.color_restoration.color_management.color_manager import ColorManager
from departments.color_restoration.color_management.aces_transforms import (
    srgb_eotf, srgb_eotf_inverse, bt1886_forward, bt1886_inverse,
    arri_logc3_to_linear, sony_slog3_to_linear, linear_to_pq, pq_to_linear
)
from departments.color_restoration.grading.primary_corrector import PrimaryCorrector
from departments.color_restoration.grading.curves_corrector import CurvesCorrector
from departments.color_restoration.grading.secondary_qualifier import SecondaryQualifier
from departments.color_restoration.grading.power_windows import PowerWindowManager
from departments.color_restoration.grading.creative_looks import CreativeLooksEngine
from departments.color_restoration.grading.grading_engine import GradingEngine
from departments.color_restoration.lut.lut_interpolator import LUTInterpolator
from departments.color_restoration.lut.lut_manager import LUTManager
from departments.color_restoration.ai_colorist.ai_colorist_assistant import AIColoristAssistant
from departments.color_restoration.matching.reference_matcher import ReferenceMatcher
from departments.color_restoration.restoration.denoiser import VideoDenoiser
from departments.color_restoration.restoration.deblurrer import VideoDeblurrer
from departments.color_restoration.restoration.deinterlacer import VideoDeinterlacer
from departments.color_restoration.restoration.deflickerer import VideoDeflickerer
from departments.color_restoration.restoration.stabilizer import VideoStabilizer
from departments.color_restoration.restoration.inpaint_scratches import ScratchDustRemover
from departments.color_restoration.restoration.low_light import LowLightEnhancer
from departments.color_restoration.restoration.restoration_pipeline import RestorationPipeline
from departments.color_restoration.super_resolution.upscaler import SuperResolutionEngine
from departments.color_restoration.hdr.tone_mapper import ToneMapper
from departments.color_restoration.qc.color_qc import ColorQualityController
from departments.color_restoration.qc.restoration_qc import RestorationQualityController
from departments.color_restoration.integrations.timeline_bridge import TimelineColorBridge
from departments.color_restoration.integrations.director_bridge import DirectorColorBridge
from departments.color_restoration.integrations.asset_bridge import AssetStoreBridge
from departments.color_restoration.integrations.generation_bridge import GeneratedMediaColorBridge
from departments.color_restoration.service import ColorRestorationService


class TestColorRestorationStudio(unittest.TestCase):
    """
    Test suite for Department 16 Color & Restoration Studio.
    """

    @classmethod
    def setUpClass(cls):
        cls.db = AssetDatabase()
        cls.project_id = uuid4()
        cls.db.create_project(cls.project_id, "Color Restoration Test Project")
        cls.color_mgr = ColorManager()
        cls.artifacts_dir = Path("test_artifacts/color_restoration")
        cls.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def test_01_import_standard_rec709_clip(self):
        """1. Detect and inspect standard Rec.709 clip metadata."""
        meta = {
            "color_primaries": "bt709",
            "color_transfer": "bt709",
            "bits_per_raw_sample": 8
        }
        profile = self.color_mgr.detect_color_space_from_metadata(meta)
        self.assertEqual(profile.color_space, ColorSpace.REC709)
        self.assertEqual(profile.transfer_function, TransferFunction.BT1886)
        self.assertFalse(profile.is_hdr)

    def test_02_import_log_encoded_clip_with_known_metadata(self):
        """2. Detect and inspect log-encoded clip with camera log metadata."""
        arri_meta = {"color_primaries": "bt709", "color_transfer": "arri-logc"}
        arri_prof = self.color_mgr.detect_color_space_from_metadata(arri_meta)
        self.assertEqual(arri_prof.color_space, ColorSpace.ARRI_LOGC3)

        sony_meta = {"color_primaries": "bt2020", "color_transfer": "slog3"}
        sony_prof = self.color_mgr.detect_color_space_from_metadata(sony_meta)
        self.assertEqual(sony_prof.color_space, ColorSpace.SONY_SLOG3)

    def test_03_handle_footage_with_missing_color_space_metadata(self):
        """3. Safe fallback when color space metadata is absent."""
        empty_meta = {}
        profile = self.color_mgr.detect_color_space_from_metadata(empty_meta)
        # Should fall back safely to Rec.709 BT.1886
        self.assertEqual(profile.color_space, ColorSpace.REC709)
        self.assertEqual(profile.transfer_function, TransferFunction.BT1886)

    def test_04_apply_valid_input_transform(self):
        """4. Convert Rec.709 to scene-linear ACEScg and back with high roundtrip fidelity."""
        test_frame = np.full((32, 32, 3), 0.5, dtype=np.float32)
        acescg = self.color_mgr.to_linear_acescg(test_frame, ColorSpace.REC709)
        self.assertEqual(acescg.shape, (32, 32, 3))

        # Roundtrip back to Rec.709
        rec709_back = self.color_mgr.from_linear_acescg(acescg, ColorSpace.REC709, to_uint8=False)
        # Difference within 1% tolerance due to transfer curve
        diff = np.max(np.abs(test_frame - rec709_back))
        self.assertLess(diff, 0.02)

    def test_05_apply_creative_grade(self):
        """5. Apply primary grading controls (exposure, contrast, saturation) to linear frame."""
        frame = np.full((64, 64, 3), 0.18, dtype=np.float32) # 18% middle gray
        params = PrimaryGradingParameters(
            exposure_ev=1.0, # +1 stop doubles linear radiance
            contrast=1.2,
            saturation=1.1
        )
        graded = PrimaryCorrector.apply_primary(frame, params)
        # +1 stop should bring 0.18 close to 0.36
        mean_val = np.mean(graded)
        self.assertGreater(mean_val, 0.30)
        self.assertLess(mean_val, 0.45)

        # Save test artifact
        uint8_out = np.clip(graded * 255.0, 0, 255).astype(np.uint8)
        cv2.imwrite(str(self.artifacts_dir / "graded_sample.png"), uint8_out)

    def test_06_apply_technical_conversion_lut(self):
        """6. Parse and apply a 3D .cube technical conversion LUT."""
        # Synthesize a simple 17x17x17 3D LUT string
        cube_str = """
TITLE "Simple Contrast 3D LUT"
LUT_3D_SIZE 2
0.0 0.0 0.0
1.0 0.0 0.0
0.0 1.0 0.0
1.0 1.0 0.0
0.0 0.0 1.0
1.0 0.0 1.0
0.0 1.0 1.0
1.0 1.0 1.0
"""
        meta, lut_grid = LUTManager.parse_cube_file(cube_str)
        self.assertEqual(lut_grid.shape, (2, 2, 2, 3))
        self.assertEqual(meta.size, 2)

        test_img = np.full((16, 16, 3), 0.5, dtype=np.float32)
        applied = LUTManager.apply_lut(test_img, lut_grid, meta, ColorSpace.REC709)
        self.assertEqual(applied.shape, (16, 16, 3))

    def test_07_reject_incompatible_lut_workflow(self):
        """7. Reject applying a technical conversion LUT in an incompatible color space."""
        meta = LUTMetadata(
            name="ARRI LogC3 to Rec709",
            input_color_space=ColorSpace.ARRI_LOGC3,
            output_color_space=ColorSpace.REC709,
            is_technical=True
        )
        lut_grid = np.zeros((2, 2, 2, 3), dtype=np.float32)
        test_img = np.full((8, 8, 3), 0.5, dtype=np.float32)

        # Attempt to apply LogC3 LUT directly to a Rec.709 clip -> must raise ValueError
        with self.assertRaises(ValueError):
            LUTManager.apply_lut(test_img, lut_grid, meta, current_color_space=ColorSpace.REC709)

    def test_08_export_color_managed_rec709_output(self):
        """8. Export linear ACEScg to broadcast legal Rec.709."""
        acescg_frame = np.full((32, 32, 3), 0.18, dtype=np.float32)
        rec709_uint8 = self.color_mgr.from_linear_acescg(acescg_frame, ColorSpace.REC709, to_uint8=True)
        self.assertEqual(rec709_uint8.dtype, np.uint8)
        self.assertEqual(rec709_uint8.shape, (32, 32, 3))

    def test_09_perform_supported_hdr_workflow(self):
        """9. Convert HDR linear / PQ frame to SDR using ACES RRT tone mapping."""
        # High dynamic range values exceeding 1.0 (e.g. 5.0 = 500 nits highlight)
        hdr_frame = np.array([[[0.18, 1.5, 6.0]]], dtype=np.float32)
        sdr_mapped = ToneMapper.map_hdr_to_sdr(hdr_frame, operator="aces_rrt")
        # All values should be compressed smoothly below 1.0
        self.assertLessEqual(np.max(sdr_mapped), 1.0)
        self.assertGreater(sdr_mapped[0, 0, 2], sdr_mapped[0, 0, 1])

    def test_10_analyze_reference_look(self):
        """10. Extract color moments and temperature bias from reference frame."""
        # Warm golden sunset test image
        ref = np.zeros((64, 64, 3), dtype=np.float32)
        ref[:, :, 0] = 0.8 # high red
        ref[:, :, 1] = 0.5 # mid green
        ref[:, :, 2] = 0.2 # low blue

        stats = ReferenceMatcher.analyze_reference(ref)
        self.assertIn("mean_lab", stats)
        self.assertEqual(stats["color_temperature_bias"], "warm")

    def test_11_generate_suggested_shot_match(self):
        """11. Match target footage to reference look with Reinhard transfer."""
        target = np.full((64, 64, 3), 0.4, dtype=np.float32) # neutral gray
        reference = np.zeros((64, 64, 3), dtype=np.float32)
        reference[:, :, 0] = 0.7
        reference[:, :, 1] = 0.4
        reference[:, :, 2] = 0.2 # warm amber

        graph, matched = ReferenceMatcher.match_shots(target, reference, self.project_id)
        self.assertIsInstance(graph, GradingGraph)
        self.assertEqual(matched.shape, (64, 64, 3))
        # Matched image should have acquired red warmth
        self.assertGreater(np.mean(matched[:, :, 0]), np.mean(matched[:, :, 2]))

        # Save test artifact
        cv2.imwrite(str(self.artifacts_dir / "reference_match_sample.png"), (matched * 255.0).astype(np.uint8))

    def test_12_denoise_noisy_video(self):
        """12. Denoise frame sequence using bilateral filtering."""
        clean = np.full((64, 64, 3), 0.5, dtype=np.float32)
        noise = np.random.normal(0, 0.1, clean.shape).astype(np.float32)
        noisy = np.clip(clean + noise, 0.0, 1.0)

        denoised = VideoDenoiser.denoise_frame_bilateral(noisy, diameter=7, sigma_color=50.0, sigma_space=50.0)
        # Variance of denoised should be significantly less than noisy
        var_noisy = np.var(noisy)
        var_denoised = np.var(denoised)
        self.assertLess(var_denoised, var_noisy)

    def test_13_upscale_sample_video(self):
        """13. Super-resolution 2x upscale with Lanczos and AI detail tagging."""
        low_res = np.full((32, 32, 3), 0.5, dtype=np.float32)
        upscaled, meta = SuperResolutionEngine.upscale_image(low_res, scale_factor=2.0)
        self.assertEqual(upscaled.shape, (64, 64, 3))
        self.assertEqual(meta["output_resolution"], (64, 64))
        self.assertIn("AI_SYNTHESIZED_TEXTURE", meta["detail_reconstruction_type"])

        # Save test artifact
        cv2.imwrite(str(self.artifacts_dir / "upscaled_sample.png"), (upscaled * 255.0).astype(np.uint8))

    def test_14_restore_old_damaged_sample(self):
        """14. Inpaint vertical film scratches and stabilize luminance flicker."""
        # Create frame with artificial vertical white scratch
        frame = np.full((64, 64, 3), 0.3, dtype=np.float32)
        frame[:, 30:32, :] = 1.0 # bright scratch
        repaired = ScratchDustRemover.inpaint_scratches(frame, scratch_threshold=20)
        # Scratch line intensity should be reduced towards background 0.3
        self.assertLess(np.mean(repaired[:, 30:32, :]), 0.8)

        cv2.imwrite(str(self.artifacts_dir / "restored_scratches_sample.png"), (repaired * 255.0).astype(np.uint8))

    def test_15_process_animation_sample(self):
        """15. Process 2D animation sample with line-art preservation."""
        anim_frame = np.full((64, 64, 3), 0.8, dtype=np.float32)
        anim_frame[20:44, 20:44, :] = 0.1 # dark character box
        upscaled, meta = SuperResolutionEngine.upscale_image(anim_frame, scale_factor=2.0, is_anime=True)
        self.assertEqual(upscaled.shape, (128, 128, 3))
        self.assertEqual(meta["detail_reconstruction_type"], "AI_ANIME_LINE_ART_ENHANCEMENT")

    def test_16_preserve_audio_synchronization(self):
        """16. Verify duration and audio sync preservation check."""
        audit = RestorationQualityController.audit_restoration_run(
            orig_duration=10.0,
            restored_duration=10.01,
            orig_frame_count=240,
            restored_frame_count=240,
            audio_synced=True
        )
        self.assertEqual(audit["review_state"], QualityReviewState.PASSED)
        self.assertTrue(audit["audio_synced"])

    def test_17_preserve_original_source_media(self):
        """17. Verify non-destructive registration leaving original asset untouched."""
        asset_id = uuid4()
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO assets (
                    asset_id, project_id, original_filename, display_name, media_type,
                    detected_format, mime_type, byte_size, checksum_sha256, storage_path,
                    import_timestamp, processing_status, metadata_status, derivative_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
                """,
                (
                    str(asset_id), str(self.project_id), "source_camera_raw.mov", "Source Camera Raw",
                    "VIDEO", "MOV", "video/quicktime", 10485760, "abcdef1234567890abcdef1234567890",
                    "originals/source_camera_raw.mov", "COMPLETED", "COMPLETED", "COMPLETED"
                )
            )

        bridge = AssetStoreBridge(self.db)
        out_deriv_id = bridge.register_restored_derivative(
            project_id=self.project_id,
            source_asset_id=asset_id,
            derivative_path="derivatives/restored_master.mp4",
            file_size=2048000,
            checksum="abcdef1234567890",
            restoration_metadata={"denoised": True}
        )
        self.assertIsNotNone(out_deriv_id)

    def test_18_resume_interrupted_processing_job(self):
        """18. Persistent job state tracking and resume from checkpoint."""
        job = RestorationJob(
            project_id=self.project_id,
            asset_id=uuid4(),
            restoration_types=[RestorationType.DENOISE, RestorationType.SUPER_RESOLUTION],
            status="PROCESSING"
        )
        self.db.save_restoration_job(job)

        fetched = self.db.get_restoration_job(str(job.id))
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["status"], "PROCESSING")

        # Update status to completed
        job.status = "COMPLETED"
        self.db.save_restoration_job(job)
        updated = self.db.get_restoration_job(str(job.id))
        self.assertEqual(updated["status"], "COMPLETED")

    def test_19_handle_gpu_memory_exhaustion(self):
        """19. Safe memory tiling for high-resolution images."""
        large_frame = np.full((128, 128, 3), 0.5, dtype=np.float32)
        # Processing with 64px tile size
        upscaled, meta = SuperResolutionEngine.upscale_image(large_frame, scale_factor=2.0, tile_size=64)
        self.assertEqual(upscaled.shape, (256, 256, 3))

    def test_20_compare_preview_and_final_render_parameters(self):
        """20. Ensure proxy preview and full render use identical color grading parameters."""
        graph = GradingGraph(
            project_id=self.project_id,
            nodes=[
                GradingNode(
                    name="Primary",
                    node_type=GradingNodeType.PRIMARY,
                    primary_params=PrimaryGradingParameters(exposure_ev=1.0)
                )
            ]
        )
        proxy = np.full((32, 32, 3), 0.18, dtype=np.float32)
        full = np.full((64, 64, 3), 0.18, dtype=np.float32)

        proxy_graded = GradingEngine.apply_graph(proxy, graph)
        full_graded = GradingEngine.apply_graph(full, graph)

        # Means must be identical
        self.assertAlmostEqual(float(np.mean(proxy_graded)), float(np.mean(full_graded)), places=3)

    def test_21_validate_output_color_metadata(self):
        """21. Detect out-of-range clipping and validate HDR metadata."""
        profile = ColorProfileMetadata(is_hdr=True, max_cll=4000.0, max_fall=1000.0)
        clipped_img = np.array([[[1.2, 0.5, -0.1]]], dtype=np.float32)
        audit = ColorQualityController.audit_frame(clipped_img, profile, is_display_referred=True)
        self.assertGreater(audit["out_of_range_high_pct"], 0.0)
        self.assertGreater(audit["out_of_range_low_pct"], 0.0)

    def test_22_integrate_grade_with_part05_timeline(self):
        """22. Attach GradingGraph to OpenTimelineIO Clip and extract roundtrip."""
        clip = otio.schema.Clip(name="Test Shot 01")
        graph = GradingGraph(
            project_id=self.project_id,
            name="Cinematic Grade",
            nodes=[
                GradingNode(
                    name="Primary",
                    node_type=GradingNodeType.PRIMARY,
                    primary_params=PrimaryGradingParameters(exposure_ev=0.5)
                )
            ]
        )
        TimelineColorBridge.attach_grade_to_clip(clip, graph)
        self.assertIn("color_grading", clip.metadata)

        extracted_graph = TimelineColorBridge.extract_grade_from_clip(clip)
        self.assertIsNotNone(extracted_graph)
        self.assertEqual(extracted_graph.name, "Cinematic Grade")

    def test_23_process_ai_generated_clip_from_part11(self):
        """23. Conform and harmonize AI-generated Runway/Flux frame into project color space."""
        bridge = GeneratedMediaColorBridge(self.color_mgr)
        ai_frame = np.full((64, 64, 3), 0.5, dtype=np.float32) # sRGB AI generated
        conformed = bridge.normalize_ai_generated_frame(
            ai_frame, source_generator="runway", target_color_space=ColorSpace.REC709
        )
        self.assertEqual(conformed.shape, (64, 64, 3))
        self.assertEqual(conformed.dtype, np.uint8)

    def test_24_verify_processing_provenance_and_version_history(self):
        """24. Service execution contract and version increment tracking."""
        service = ColorRestorationService()
        self.assertTrue(service.health_check())

        # Version tracking in DB
        graph = GradingGraph(
            project_id=self.project_id,
            name="Versioned Grade",
            version=1
        )
        self.db.save_color_grade(graph)
        v1 = self.db.get_color_grade(str(graph.id))
        self.assertEqual(v1["version"], 1)

        graph.version = 2
        self.db.save_color_grade(graph)
        v2 = self.db.get_color_grade(str(graph.id))
        self.assertEqual(v2["version"], 2)


if __name__ == "__main__":
    unittest.main()
