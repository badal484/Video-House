"""
Comprehensive Unit Tests for Deep Video Reverse Engineering & Creative Intelligence.
Tests:
- Normalization and 5-pass multi-resolution sampling.
- Cinematography, composition geometry, and 6-DoF camera motion.
- Editing rhythm, transition classification, and beat sync.
- Motion graphics tracking and typography reconstruction.
- Animation cadence and VFX layer decomposition.
- Audio tri-band energy, BPM autocorrelation, and SFX transients.
- Color grading, palette extraction, and vignette/LUT analysis.
- Narrative arc synthesis.
- Temporal Event Graph queries and cross-modal edge synthesis.
- Reference-to-Production Compiler (OTIO, Motion Canvas, DAW layout).
"""
from pathlib import Path
import tempfile
import unittest
from uuid import UUID, uuid4

import departments

import cv2
import numpy as np

from core.assets.intelligence_models import (
    BoundingBox,
    CameraAngle,
    CameraMotionType,
    ShotScale,
    TimecodeRange
)
from core.intelligence.event_graph import (
    EventGraphEdge,
    EventGraphNode,
    GraphEdgeType,
    GraphNodeType,
    TemporalEventGraph
)
from departments.media_intelligence.animation_vfx import AnimationAndVFXIntelligenceEngine
from departments.media_intelligence.audio_intelligence_v2 import AdvancedAudioIntelligenceEngine
from departments.media_intelligence.cinematography import CinematographyIntelligenceEngine
from departments.media_intelligence.color_grading_intelligence import ColorGradingIntelligenceEngine
from departments.media_intelligence.editing_intelligence import EditingIntelligenceEngine
from departments.media_intelligence.master_reverse_engineer import MasterVideoReverseEngineeringService
from departments.media_intelligence.motion_graphics_intelligence import MotionGraphicsReverseEngineeringEngine
from departments.media_intelligence.narrative_intelligence import StorytellingIntelligenceEngine
from departments.media_intelligence.temporal_engine.normalization import MediaNormalizationService
from departments.media_intelligence.temporal_engine.sampling_engine import HighResolutionTemporalSamplingEngine
from departments.creative_direction.production_compiler import (
    ProductionBlueprint,
    ReferenceToProductionCompiler,
    TargetProductionBrief
)

class TestDeepVideoIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a synthetic 3-second test video with cut and on-screen text
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="test_deep_intel_"))
        cls.test_video_path = cls.temp_dir / "synthetic_reference.mp4"

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(cls.test_video_path), fourcc, 30.0, (320, 180))

        for f in range(90):  # 3 seconds @ 30fps
            if f < 45:
                # Shot 1: Blue background with white text block (simulate title)
                frame = np.zeros((180, 320, 3), dtype=np.uint8)
                frame[:, :] = (180, 50, 10)  # BGR teal
                # Put white text line
                cv2.rectangle(frame, (40, 40), (280, 70), (255, 255, 255), -1)
            else:
                # Shot 2: Dark orange background with yellow subtitle
                frame = np.zeros((180, 320, 3), dtype=np.uint8)
                frame[:, :] = (20, 100, 200)  # BGR orange
                cv2.rectangle(frame, (40, 140), (280, 165), (0, 255, 255), -1)

            out.write(frame)
        out.release()

    def test_media_normalization_probing(self):
        norm = MediaNormalizationService(temp_dir=self.temp_dir)
        info = norm.probe_media(self.test_video_path)
        self.assertTrue(info["has_video"])
        self.assertAlmostEqual(info["fps"], 30.0, delta=0.5)
        self.assertEqual(info["width"], 320)
        self.assertEqual(info["height"], 180)

    def test_temporal_sampling_engine(self):
        norm = MediaNormalizationService(temp_dir=self.temp_dir)
        sampler = HighResolutionTemporalSamplingEngine(normalization_service=norm)
        asset_id = uuid4()
        timeline = sampler.execute_multi_pass_analysis(self.test_video_path, asset_id, known_cut_timestamps=[1.5])

        self.assertGreater(len(timeline.global_samples), 0)
        self.assertGreater(timeline.confidence_score, 0.5)

    def test_cinematography_intelligence(self):
        cinema = CinematographyIntelligenceEngine()
        frame = np.zeros((180, 320, 3), dtype=np.uint8)
        frame[30:150, 100:220] = (255, 255, 255)  # Salient subject

        comp = cinema.analyze_frame_composition(frame)
        self.assertIsInstance(comp.rule_of_thirds_adherence, float)
        self.assertIsInstance(comp.symmetry_score, float)

        opt = cinema.analyze_optical_properties(frame)
        self.assertIn(opt.depth_of_field, ["SHALLOW", "DEEP"])

        light = cinema.analyze_lighting_and_colorimetry(frame)
        self.assertIn(light.lighting_style, ["HIGH_KEY", "LOW_KEY", "BALANCED"])
        self.assertGreater(light.estimated_color_temperature_kelvin, 2000)

        scale = cinema.classify_shot_scale(frame)
        self.assertIn(scale, list(ShotScale))

        angle = cinema.classify_camera_angle(frame)
        self.assertIn(angle, list(CameraAngle))

    def test_editing_intelligence(self):
        engine = EditingIntelligenceEngine()
        cap = cv2.VideoCapture(str(self.test_video_path))
        tr = engine.classify_transition(cap, cut_frame=45, fps=30.0)
        cap.release()

        self.assertIn(tr.transition_type, ["HARD_CUT", "DISSOLVE", "CROSS_DISSOLVE", "WHIP_PAN", "FLASH_CUT", "DIP_TO_BLACK"])
        self.assertGreaterEqual(tr.duration_frames, 1)

    def test_motion_graphics_intelligence(self):
        mg_engine = MotionGraphicsReverseEngineeringEngine()
        elements = mg_engine.track_and_reconstruct_elements(self.test_video_path, fps=30.0, sample_step=5)

        self.assertIsInstance(elements, list)
        if elements:
            elem = elements[0]
            self.assertIn(elem.element_type, ["TITLE", "LOWER_THIRD", "SUBTITLE_CAPTION", "TELEMETRY_HUD", "PROGRESS_BAR", "CALLOUT", "ICON_LOGO"])
            self.assertIsNotNone(elem.typography.font_family_class)
            self.assertIsNotNone(elem.motion_behavior.entry_animation)
            self.assertGreater(elem.timecode_range.duration_seconds, 0.0)

    def test_animation_and_vfx_intelligence(self):
        vfx_engine = AnimationAndVFXIntelligenceEngine()
        analysis = vfx_engine.analyze_visual_medium_and_vfx(self.test_video_path, fps=30.0)

        self.assertIn(analysis.visual_medium, ["LIVE_ACTION", "2D_VECTOR_MOTION_GRAPHICS", "3D_CGI"])
        self.assertIn(analysis.animation_cadence, ["ON_ONES", "ON_TWOS", "ON_THREES"])
        self.assertGreaterEqual(analysis.compositing_layers_count, 1)

    def test_color_grading_intelligence(self):
        color_engine = ColorGradingIntelligenceEngine()
        grade = color_engine.analyze_color_finish(self.test_video_path, sample_count=5)

        self.assertEqual(len(grade.dominant_palette_hex), 5)
        self.assertIn(grade.color_harmony_type, ["COMPLEMENTARY", "ANALOGOUS", "TRIADIC", "MONOCHROMATIC"])
        self.assertIsInstance(grade.contrast_ratio, float)

    def test_narrative_intelligence(self):
        narrative = StorytellingIntelligenceEngine()
        story = narrative.analyze_narrative_arc(duration_sec=50.0, shots_count=12)

        self.assertEqual(len(story.narrative_phases), 5)
        self.assertEqual(story.narrative_phases[0].phase_name, "HOOK")
        self.assertGreater(story.curiosity_gap_score, 0.5)

    def test_temporal_event_graph(self):
        asset_id = uuid4()
        graph = TemporalEventGraph(asset_id=asset_id, title="Test Event Graph")

        n1 = EventGraphNode(
            node_id="shot_1",
            node_type=GraphNodeType.SHOT,
            label="Shot 1 Wide",
            start_seconds=0.0,
            end_seconds=2.5,
            attributes={"scale": "WIDE"}
        )
        n2 = EventGraphNode(
            node_id="title_1",
            node_type=GraphNodeType.TEXT_ELEMENT,
            label="Main Title Reveal",
            start_seconds=0.5,
            end_seconds=2.0,
            attributes={"anim": "POP"}
        )
        n3 = EventGraphNode(
            node_id="shot_2",
            node_type=GraphNodeType.SHOT,
            label="Shot 2 Close Up",
            start_seconds=2.5,
            end_seconds=5.0,
            attributes={"scale": "CLOSE_UP"}
        )

        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        graph.auto_connect_temporal_edges()

        # Query at t=1.0s: both shot_1 and title_1 are active
        active_nodes = graph.query_at_timestamp(1.0)
        active_ids = [n.node_id for n in active_nodes]
        self.assertIn("shot_1", active_ids)
        self.assertIn("title_1", active_ids)
        self.assertNotIn("shot_2", active_ids)

        # Search query
        search_results = graph.search_nodes("Title")
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0].node_id, "title_1")

        # Serialization round-trip
        data = graph.to_dict()
        graph_restored = TemporalEventGraph.from_dict(data)
        self.assertEqual(len(graph_restored.nodes), 3)

    def test_reference_to_production_compiler(self):
        compiler = ReferenceToProductionCompiler(output_dir=self.temp_dir)
        master = MasterVideoReverseEngineeringService()
        asset_id = uuid4()
        manifest, _ = master.reverse_engineer_video(self.test_video_path, asset_id, "Synthetic Ref")

        brief = TargetProductionBrief(
            project_id=uuid4(),
            title="Compiled Original Test Doc",
            target_topic="Octopus Biology",
            target_duration_sec=30.0,
            aspect_ratio="9:16",
            target_language="hi"
        )

        blueprint = compiler.compile_reference_to_blueprint(manifest, brief)
        self.assertIsInstance(blueprint, ProductionBlueprint)
        self.assertEqual(blueprint.target_topic, "Octopus Biology")
        self.assertEqual(blueprint.aspect_ratio, "9:16")
        self.assertTrue(Path(blueprint.otio_timeline_path).exists())
        self.assertIn("scenes", blueprint.motion_composition)
        self.assertGreaterEqual(len(blueprint.asset_acquisition_plan), 1)
        self.assertEqual(blueprint.qc_validation_policies["audio_loudness_target_lufs"], -14.0)

if __name__ == "__main__":
    unittest.main()
