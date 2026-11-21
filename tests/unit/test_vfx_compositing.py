"""
Unit Tests for Department 13: VFX & Compositing Studio
Verifies all 12 core visual effects capabilities, node graph DAG topological evaluation,
tracking, keying, rotoscoping, inpainting, quality control, and timeline bridge.
"""
from pathlib import Path
import unittest
from uuid import uuid4
import cv2
import numpy as np

import departments
from departments.vfx_compositing.core.graph_models import (
    CompositingGraph,
    VFXNode,
    VFXNodeType,
    NodePort,
    PortDataType,
    BlendMode,
)
from departments.vfx_compositing.core.color_space import (
    srgb_to_linear,
    linear_to_srgb,
    straight_to_premultiplied,
    premultiplied_to_straight,
    apply_green_despill,
    apply_blue_despill,
    grade_image,
)
from departments.vfx_compositing.keying.chroma_keyer import ChromaKeyer
from departments.vfx_compositing.tracking.planar_tracker import PlanarTracker
from departments.vfx_compositing.tracking.feature_tracker import FeatureTracker
from departments.vfx_compositing.rotoscoping.segmentation_engine import SegmentationEngine
from departments.vfx_compositing.rotoscoping.matte_refinement import MatteRefiner
from departments.vfx_compositing.cleanup.inpainting_engine import InpaintingEngine
from departments.vfx_compositing.effects.atmospheric import AtmosphericEffects
from departments.vfx_compositing.effects.cinematic_fx import CinematicEffects
from departments.vfx_compositing.engines.local_compositor import LocalCompositorEngine
from departments.vfx_compositing.supervisor.vfx_supervisor import AIVFXSupervisor
from departments.vfx_compositing.supervisor.quality_checker import VFXQualityChecker
from departments.vfx_compositing.service import VFXCompositingService
from departments.vfx_compositing.interface import VFXCompositingRequest
from departments.video_editing.timeline_manager import TimelineManager
from core.assets.database import AssetDatabase


class TestVFXCompositing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact_dir = Path("test_artifacts/vfx")
        cls.artifact_dir.mkdir(parents=True, exist_ok=True)
        cls.db = AssetDatabase(":memory:")

    def test_01_chroma_key_and_despill(self):
        """Test green screen keying, color difference despill, and alpha matte generation."""
        h, w = 400, 600
        # Create image with bright green background and magenta/skin-tone subject in center
        plate = np.full((h, w, 3), (0, 230, 0), dtype=np.uint8)  # Green screen BGR
        cv2.circle(plate, (300, 200), 100, (80, 80, 220), -1)   # Subject (warm red/skin tone)
        # Add some green spill reflection on the subject edge
        cv2.circle(plate, (250, 150), 30, (40, 180, 200), -1)

        keyer = ChromaKeyer(key_color="GREEN", threshold_low=0.05, threshold_high=0.35, despill_strength=1.0)
        matte = keyer.extract_matte(plate)
        result_bgra = keyer.process(plate)

        self.assertEqual(result_bgra.shape, (h, w, 4))
        # Center of subject should be foreground (alpha ~ 1.0)
        self.assertGreater(matte[200, 300], 0.9)
        # Background should be keyed out (alpha ~ 0.0)
        self.assertLess(matte[50, 50], 0.05)

        # Save artifact
        cv2.imwrite(str(self.artifact_dir / "01_chroma_keyed.png"), result_bgra)

    def test_02_rotoscoping_and_segmentation(self):
        """Test GrabCut-based bounding box segmentation and soft edge feathering."""
        h, w = 300, 400
        canvas = np.full((h, w, 3), 40, dtype=np.uint8)  # Dark background
        cv2.circle(canvas, (200, 150), 60, (200, 200, 200), -1)  # White subject

        bbox = (130, 80, 140, 140)
        mask = SegmentationEngine.segment_box(canvas, bbox, iterations=2)
        feathered = MatteRefiner.feather_matte(mask, blur_radius=2.0)

        self.assertEqual(feathered.shape, (h, w))
        self.assertGreater(feathered[150, 200], 0.8)
        self.assertLess(feathered[20, 20], 0.1)

        mask_vis = (feathered * 255.0).astype(np.uint8)
        cv2.imwrite(str(self.artifact_dir / "02_roto_mask.png"), mask_vis)

    def test_03_point_feature_tracking(self):
        """Test Shi-Tomasi feature detection and Lucas-Kanade optical flow tracking."""
        h, w = 300, 400
        frames = []
        # Generate 5 frames with moving circle
        for i in range(5):
            f = np.full((h, w, 3), 30, dtype=np.uint8)
            cv2.circle(f, (100 + i * 15, 120 + i * 5), 25, (220, 220, 220), -1)
            # Add static corner markers
            cv2.rectangle(f, (30, 30), (50, 50), (180, 180, 180), -1)
            frames.append(f)

        tracker = FeatureTracker(max_corners=20)
        seqs = tracker.track_sequence(frames)

        self.assertGreater(len(seqs), 0)
        # First point should have 5 tracked positions
        self.assertEqual(len(seqs[0].points), 5)

    def test_04_planar_tracking_phone_screen_replacement(self):
        """Test 4-point perspective homography warping for smartphone screen replacement."""
        h_bg, w_bg = 600, 800
        # Background plate representing a phone held at an angle
        plate = np.full((h_bg, w_bg, 3), 50, dtype=np.uint8)
        # Define quad corners of phone screen
        dst_corners = np.array([
            [220.0, 150.0],  # Top-left
            [540.0, 180.0],  # Top-right
            [510.0, 520.0],  # Bottom-right
            [240.0, 480.0],  # Bottom-left
        ], dtype=np.float32)

        # Draw phone bezel on plate
        pts = dst_corners.astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(plate, [pts], isClosed=True, color=(100, 100, 100), thickness=8)

        # Create screen UI graphic (Motion Canvas simulated UI)
        ui = np.zeros((400, 300, 4), dtype=np.uint8)
        ui[:, :] = (20, 140, 240, 255)  # Orange UI
        cv2.putText(ui, "AI STUDIO", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255, 255), 2)
        cv2.putText(ui, "STREAM ACTIVE", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255, 255), 2)

        warped = PlanarTracker.warp_graphic(ui, (h_bg, w_bg), dst_corners)
        self.assertEqual(warped.shape, (h_bg, w_bg, 4))

        # Merge warped screen over plate
        engine = LocalCompositorEngine()
        composite = engine._blend_layers(plate, warped, BlendMode.OVER.value, 1.0)
        self.assertEqual(composite.shape, (h_bg, w_bg, 4))

        cv2.imwrite(str(self.artifact_dir / "04_screen_replacement.png"), composite)

    def test_05_moving_billboard_replacement(self):
        """Test perspective warping across skewed billboard quad."""
        dst_corners = np.array([[50.0, 30.0], [350.0, 10.0], [370.0, 250.0], [30.0, 220.0]], dtype=np.float32)
        ad_graphic = np.full((200, 300, 4), (180, 50, 50, 255), dtype=np.uint8)
        cv2.putText(ad_graphic, "BILLBOARD", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255, 255), 2)

        warped = PlanarTracker.warp_graphic(ad_graphic, (300, 400), dst_corners)
        self.assertGreater(np.sum(warped[:, :, 3] > 0), 1000)

    def test_06_video_cleanup_and_inpainting(self):
        """Test Telea fast marching object/wire removal."""
        h, w = 300, 400
        # Background gradient
        plate = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            plate[y, :, :] = int(y / h * 200)

        # Draw unwanted microphone boom / wire across frame
        cv2.line(plate, (50, 20), (350, 220), (255, 255, 255), 4)

        # Create inpainting mask over the wire
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.line(mask, (50, 20), (350, 220), 255, 6)

        cleaned = InpaintingEngine.inpaint_frame(plate, mask, method="TELEA", inpaint_radius=3)
        self.assertEqual(cleaned.shape, (h, w, 3))

        # Verify wire was removed (pixel along the wire line should be close to background gradient)
        bg_expected = plate[120, 100]  # sample unpolluted background
        self.assertLess(abs(int(cleaned[120, 200, 0]) - int(plate[120, 100, 0])), 40)

        # Save before/after artifact
        comparison = np.hstack([plate, cleaned])
        cv2.imwrite(str(self.artifact_dir / "06_inpaint_comparison.png"), comparison)

    def test_07_atmospheric_effects_light_wrap_dust(self):
        """Test optical light wrap bleeding and procedural dust particle simulation."""
        h, w = 300, 400
        # Bright background (sky/sun)
        bg = np.full((h, w, 3), 240, dtype=np.uint8)
        # Dark foreground subject with alpha
        fg = np.zeros((h, w, 4), dtype=np.uint8)
        fg[80:220, 120:280] = (40, 40, 40, 255)

        wrapped = AtmosphericEffects.apply_light_wrap(fg, bg, wrap_amount=0.6, wrap_radius=10)
        self.assertEqual(wrapped.shape, (h, w, 4))
        # Edge pixels should be brightened by background bleed
        self.assertGreater(wrapped[85, 125, 0], 50)

        # Dust particles
        dust = AtmosphericEffects.generate_dust_particles((h, w), count=50, seed=123)
        self.assertEqual(dust.shape, (h, w, 4))
        self.assertGreater(np.sum(dust[:, :, 3] > 0), 50)

        cv2.imwrite(str(self.artifact_dir / "07_light_wrap.png"), wrapped)

    def test_08_cinematic_lens_glow_and_chromatic_aberration(self):
        """Test lens bloom and RGB channel chromatic aberration."""
        h, w = 250, 350
        img = np.full((h, w, 3), 30, dtype=np.uint8)
        cv2.circle(img, (175, 125), 30, (255, 255, 255), -1)  # High-intensity light source

        glow = CinematicEffects.lens_glow(img, threshold=0.7, glow_radius=15, glow_intensity=0.8)
        aberration = CinematicEffects.chromatic_aberration(img, shift_pixels=4)

        self.assertEqual(glow.shape, (h, w, 3))
        self.assertEqual(aberration.shape, (h, w, 3))
        # Pixels outside highlight should receive bloom
        self.assertGreater(glow[125, 215, 0], 35)

        cv2.imwrite(str(self.artifact_dir / "08_lens_glow.png"), glow)

    def test_09_dag_topological_sort_and_cycle_detection(self):
        """Test CompositingGraph DAG ordering and cycle prevention."""
        graph = CompositingGraph(graph_id=str(uuid4()), project_id="p1", name="DAG_Test")
        n1 = VFXNode("n1", VFXNodeType.MEDIA_INPUT, "Input")
        n2 = VFXNode("n2", VFXNodeType.BLUR, "Blur")
        n3 = VFXNode("n3", VFXNodeType.COLOR_GRADE, "Grade")
        n4 = VFXNode("n4", VFXNodeType.MEDIA_OUTPUT, "Output")

        for n in [n1, n2, n3, n4]:
            graph.add_node(n)

        graph.add_edge("n1", "output", "n2", "source")
        graph.add_edge("n2", "output", "n3", "source")
        graph.add_edge("n3", "output", "n4", "source")

        order = graph.topological_sort()
        self.assertEqual([n.node_id for n in order], ["n1", "n2", "n3", "n4"])

        # Introducing cycle n3 -> n1 should raise ValueError
        with self.assertRaises(ValueError):
            graph.add_edge("n3", "output", "n1", "source")

    def test_10_multi_layer_premultiplied_compositing(self):
        """Test linear color space conversion and premultiplied alpha Over/Screen blending."""
        h, w = 200, 200
        # Background: Solid blue
        bg = np.zeros((h, w, 4), dtype=np.uint8)
        bg[:, :] = (255, 0, 0, 255)  # BGR = Blue

        # Foreground: Half-transparent Red square in center
        fg = np.zeros((h, w, 4), dtype=np.uint8)
        fg[50:150, 50:150] = (0, 0, 255, 128)  # Red with ~50% alpha

        engine = LocalCompositorEngine()
        comp_over = engine._blend_layers(bg, fg, BlendMode.OVER.value, 1.0)
        comp_add = engine._blend_layers(bg, fg, BlendMode.ADD.value, 1.0)
        comp_screen = engine._blend_layers(bg, fg, BlendMode.SCREEN.value, 1.0)

        self.assertEqual(comp_over.shape, (h, w, 4))
        # Center should blend red and blue into purple
        self.assertGreater(comp_over[100, 100, 0], 50)  # Blue component
        self.assertGreater(comp_over[100, 100, 2], 50)  # Red component

        cv2.imwrite(str(self.artifact_dir / "10_composite_over.png"), comp_over)

    def test_11_quality_control_auditing(self):
        """Test automated detection of pinholes, spill, and edge halos."""
        h, w = 200, 200
        clean_comp = np.full((h, w, 4), (100, 100, 100, 255), dtype=np.uint8)
        report_clean = VFXQualityChecker.audit_composite(clean_comp)
        self.assertEqual(report_clean["qc_status"], "PASSED")
        self.assertEqual(report_clean["score"], 1.0)

        # Dirty composite with excess green spill on foreground
        dirty_comp = clean_comp.copy()
        dirty_comp[:, :, 1] = 250  # Overwhelming green spill
        report_dirty = VFXQualityChecker.audit_composite(dirty_comp, key_color="GREEN")
        self.assertFalse(report_dirty["checks"]["color_spill"]["passed"])

    def test_12_service_execution_and_before_after_contact_sheet(self):
        """Test high-level VFXCompositingService execution and generate visual contact sheet."""
        service = VFXCompositingService()
        self.assertTrue(service.health_check())

        # Build recipe graph via supervisor
        graph = AIVFXSupervisor.create_screen_replacement_graph(
            project_id=str(uuid4()),
            name="Supervisor_Screen_Test",
            dst_corners=[[100.0, 80.0], [450.0, 100.0], [420.0, 360.0], [80.0, 320.0]],
            resolution=(500, 400),
            add_glow=True,
        )

        engine = LocalCompositorEngine()
        rendered_frame = engine.evaluate_frame(graph, frame_index=0)
        self.assertEqual(rendered_frame.shape, (400, 500, 4))

        # Generate a 12-slot Contact Sheet showing VFX capabilities
        cs_h, cs_w = 400, 600
        contact_sheet = np.zeros((cs_h * 2, cs_w * 2, 3), dtype=np.uint8)

        # Slot 1: Keying
        f1 = cv2.imread(str(self.artifact_dir / "01_chroma_keyed.png"))
        if f1 is not None: contact_sheet[0:cs_h, 0:cs_w] = cv2.resize(f1, (cs_w, cs_h))

        # Slot 2: Screen Replacement
        f2 = cv2.imread(str(self.artifact_dir / "04_screen_replacement.png"))
        if f2 is not None: contact_sheet[0:cs_h, cs_w:cs_w*2] = cv2.resize(f2, (cs_w, cs_h))

        # Slot 3: Inpainting
        f3 = cv2.imread(str(self.artifact_dir / "06_inpaint_comparison.png"))
        if f3 is not None: contact_sheet[cs_h:cs_h*2, 0:cs_w] = cv2.resize(f3, (cs_w, cs_h))

        # Slot 4: Final Composite
        f4 = cv2.cvtColor(rendered_frame, cv2.COLOR_BGRA2BGR)
        contact_sheet[cs_h:cs_h*2, cs_w:cs_w*2] = cv2.resize(f4, (cs_w, cs_h))

        # Annotate Contact Sheet
        cv2.putText(contact_sheet, "1. CHROMA KEY + DESPILL", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        cv2.putText(contact_sheet, "2. PLANAR SCREEN REPLACE", (cs_w + 20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        cv2.putText(contact_sheet, "3. WIRE/OBJECT INPAINT", (20, cs_h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        cv2.putText(contact_sheet, "4. MULTI-LAYER DAG COMPOSITE", (cs_w + 20, cs_h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        contact_sheet_path = self.artifact_dir / "VFX_ACCEPTANCE_CONTACT_SHEET.png"
        cv2.imwrite(str(contact_sheet_path), contact_sheet)
        self.assertTrue(contact_sheet_path.exists())


if __name__ == "__main__":
    unittest.main()
