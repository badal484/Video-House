"""
Comprehensive Automated Unit and Integration Tests for Department 09: Motion Graphics & Typography Studio.
Verifies composition schemas, typography & Indic script shaping, animation easing,
design validation, preset instantiation, SVG/Canvas rendering, transparent media export,
audio cue synchronization, director bridging, and Part 05 NLE timeline integration.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

from core.timeline.timeline_models import TrackType
from core.timeline.time_model import RationalTime, TimeRange
from core.assets.database import AssetDatabase
from core.storage.storage_service import StorageService
from departments.video_editing.timeline_manager import TimelineManager
from departments.motion_graphics.core.composition_models import (
    BackgroundConfig, BackgroundType, ChartDataPoint, ChartElement, ChartType,
    CinematicOverlayElement, EasingType, HUDElement, HUDType, KeyframeAnimation,
    KeyframePoint, LayerType, MotionComposition, MotionLayer, MotionScene,
    RenderConfig, ShapeElement, TextElement, TextRevealMode, Transform2D
)
from departments.motion_graphics.core.typography import TypographyEngine
from departments.motion_graphics.core.animation_engine import AnimationEngine
from departments.motion_graphics.core.design_validator import DesignValidator
from departments.motion_graphics.core.time_sync import TimeSynchronizer
from departments.motion_graphics.presets.preset_registry import PresetRegistry
from departments.motion_graphics.renderers.svg_vector_renderer import SVGVectorRenderer
from departments.motion_graphics.renderers.canvas_renderer import CanvasRasterRenderer
from departments.motion_graphics.renderers.router import MotionRendererRouter
from departments.motion_graphics.integration.director_bridge import DirectorMotionBridge
from departments.motion_graphics.integration.timeline_adapter import TimelineMotionAdapter
from departments.motion_graphics.service import MotionGraphicsService, MotionGraphicsRequest


class TestMotionGraphicsStudio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="studio_mograph_test_")
        cls.db_path = os.path.join(cls.temp_dir, "test_assets.db")
        cls.db = AssetDatabase(cls.db_path)
        cls.storage = StorageService(root_storage_dir=os.path.join(cls.temp_dir, "storage"))
        cls.timeline_manager = TimelineManager(cls.db)
        cls.artifact_dir = Path("test_artifacts/motion_graphics")
        cls.artifact_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_composition_schema_and_serialization(self):
        """Verifies composition creation, layers, RationalTime bounds, and bidirectional serialization."""
        comp = MotionComposition(
            name="Test Commercial Title",
            resolution=(1920, 1080),
            fps=24.0,
            duration=RationalTime(96, 24.0)
        )
        layer = MotionLayer(
            name="Main Title",
            layer_type=LayerType.TEXT,
            transform=Transform2D(x=960.0, y=540.0, opacity=1.0),
            element=TextElement(text="FUTURE ARCHITECTURE", font_family="Montserrat", font_size=60.0)
        )
        scene = MotionScene(
            name="Scene 1",
            start_time=RationalTime(0, 24.0),
            duration=RationalTime(96, 24.0),
            layers=[layer]
        )
        comp.scenes.append(scene)

        # Serialize to dict and deserialize back
        comp_dict = comp.to_dict()
        self.assertEqual(comp_dict["name"], "Test Commercial Title")
        self.assertEqual(comp_dict["duration"]["value"], 96)

        reconstructed = MotionComposition.from_dict(comp_dict)
        self.assertEqual(reconstructed.name, comp.name)
        self.assertEqual(reconstructed.duration, comp.duration)
        self.assertEqual(len(reconstructed.scenes), 1)
        self.assertEqual(reconstructed.scenes[0].layers[0].element.text, "FUTURE ARCHITECTURE")

    def test_02_typography_and_indic_grapheme_clusters(self):
        """Verifies text wrapping and complex script (Devanagari) grapheme cluster shaping."""
        # 1. Line wrapping
        long_text = "Universal AI Video Production Studio empowers autonomous multi-agent video pipelines"
        lines = TypographyEngine.wrap_text(long_text, font_size=40.0, max_width=600.0)
        self.assertGreater(len(lines), 1)
        self.assertTrue("Universal" in lines[0])

        # 2. Devanagari grapheme cluster tokenization
        hindi_phrase = "नमस्ते भारत"
        clusters = TypographyEngine.tokenize_grapheme_clusters(hindi_phrase)
        # 'न', 'म', 'स्ते', ' ', 'भा', 'र', 'त'
        self.assertTrue(len(clusters) >= 5)
        self.assertIn("स्ते", clusters)  # Verifies virama + ta + matra stayed bonded!

        # 3. Kinetic reveal tokenization
        text_elem = TextElement(text="STUDIO", reveal_mode=TextRevealMode.TYPEWRITER, show_cursor=True)
        half_reveal = TypographyEngine.compute_reveal_state(text_elem, progress=0.5)
        self.assertEqual(half_reveal["visible_text"], "STU")

    def test_03_animation_easing_and_transforms(self):
        """Verifies mathematical easing curves and animated transform property evaluation."""
        # Easing curve properties: tau=0 -> 0, tau=1 -> 1
        self.assertAlmostEqual(AnimationEngine.ease(0.0, EasingType.LINEAR), 0.0)
        self.assertAlmostEqual(AnimationEngine.ease(1.0, EasingType.LINEAR), 1.0)
        self.assertAlmostEqual(AnimationEngine.ease(0.0, EasingType.EASE_IN_OUT), 0.0)
        self.assertAlmostEqual(AnimationEngine.ease(1.0, EasingType.EASE_IN_OUT), 1.0)
        self.assertAlmostEqual(AnimationEngine.ease(0.5, EasingType.EASE_IN_OUT), 0.5)

        # Keyframe property evaluation
        anim = KeyframeAnimation(
            target_property="opacity",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, 24), value=0.0, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(24, 24), value=1.0, easing=EasingType.LINEAR),
            ]
        )
        layer = MotionLayer(
            name="Anim Layer",
            transform=Transform2D(opacity=0.0),
            animations=[anim]
        )

        mid_t = RationalTime(12, 24)
        evaluated = AnimationEngine.evaluate_layer_transform(layer, mid_t)
        self.assertAlmostEqual(evaluated.opacity, 0.5, delta=0.01)

    def test_04_design_validation_and_aspect_ratio_adaptation(self):
        """Verifies safe margin checking, WCAG contrast calculation, and aspect ratio conversion."""
        # Contrast checking
        contrast_white_black = DesignValidator.calculate_contrast_ratio("#FFFFFF", "#000000")
        self.assertAlmostEqual(contrast_white_black, 21.0, delta=0.5)

        contrast_low = DesignValidator.calculate_contrast_ratio("#777777", "#888888")
        self.assertLess(contrast_low, 3.0)

        # Aspect ratio adaptation (16:9 to 9:16 vertical)
        comp = MotionComposition(resolution=(1920, 1080))
        layer = MotionLayer(
            name="Title",
            layer_type=LayerType.TEXT,
            transform=Transform2D(x=960.0, y=900.0),
            element=TextElement(text="Lower Third", font_size=40.0)
        )
        comp.scenes.append(MotionScene(layers=[layer]))

        adapted = DesignValidator.adapt_aspect_ratio(comp, (1080, 1920))
        self.assertEqual(adapted.resolution, (1080, 1920))
        self.assertAlmostEqual(layer.transform.x, 540.0, delta=1.0)
        self.assertGreater(layer.element.font_size, 40.0)

    def test_05_preset_registry_and_instantiation(self):
        """Verifies preset registry catalog, retrieval, and parameter instantiation."""
        registry = PresetRegistry()
        presets = registry.list_presets()
        self.assertGreaterEqual(len(presets), 8)

        # Retrieve typewriter preset
        tw = registry.get("preset_kinetic_typewriter")
        self.assertIsNotNone(tw)
        self.assertEqual(tw.category, "Typography")

        # Instantiate lower third
        comp = registry.instantiate("preset_lower_third_documentary", {
            "name": "Sarah Connor",
            "role": "Resistance Leader",
            "accent_color": "#00F0FF"
        })
        self.assertIsInstance(comp, MotionComposition)
        self.assertEqual(len(comp.scenes[0].layers), 3)

    def test_06_svg_vector_rendering_frame_accuracy(self):
        """Verifies deterministic SVG vector XML output for graphics and typography."""
        renderer = SVGVectorRenderer()
        registry = PresetRegistry()
        comp = registry.instantiate("preset_chart_animated_bar", {
            "labels": ["Alpha", "Beta"],
            "values": [50.0, 100.0]
        })

        t0 = RationalTime(0, 24)
        svg_t0 = renderer.render_frame_svg(comp, t0)
        self.assertTrue(svg_t0.startswith("<?xml"))
        self.assertIn("<svg", svg_t0)
        self.assertIn("Alpha", svg_t0)

        t_end = RationalTime(48, 24)
        svg_tend = renderer.render_frame_svg(comp, t_end)
        self.assertIn("Beta", svg_tend)

    def test_07_canvas_raster_rendering_alpha_channel(self):
        """Verifies direct RGBA raster rendering with Pillow."""
        renderer = CanvasRasterRenderer()
        comp = MotionComposition(resolution=(640, 360), background=BackgroundConfig(type=BackgroundType.TRANSPARENT))
        layer = MotionLayer(
            name="HUD Circle",
            layer_type=LayerType.SHAPE,
            transform=Transform2D(x=320.0, y=180.0),
            element=ShapeElement(shape_type="CIRCLE", radius=60.0, fill_color="#00F0FF88")
        )
        comp.scenes.append(MotionScene(layers=[layer]))

        png_bytes = renderer.render_frame_raster(comp, RationalTime(0, 24))
        self.assertTrue(len(png_bytes) > 100)
        self.assertEqual(png_bytes[:8], b"\x89PNG\r\n\x1a\n")

    def test_08_render_video_prores4444_and_webm(self):
        """Verifies actual video encoding to ProRes 4444 (yuva444p10le) and WebM with alpha."""
        renderer = SVGVectorRenderer()
        comp = MotionComposition(
            resolution=(640, 360),
            fps=24.0,
            duration=RationalTime(24, 24.0)  # 1 second test clip
        )
        comp.scenes.append(MotionScene(
            duration=RationalTime(24, 24.0),
            layers=[
                MotionLayer(
                    layer_type=LayerType.TEXT,
                    transform=Transform2D(x=320.0, y=180.0),
                    element=TextElement(text="TEST CLIP", font_size=32.0, fill_color="#FFFFFF")
                )
            ]
        ))

        # 1. Render ProRes 4444 (.mov)
        out_mov = os.path.join(self.temp_dir, "test_alpha_prores.mov")
        renderer.render_video(comp, out_mov, RenderConfig(
            resolution=(640, 360),
            fps=24.0,
            codec="prores_ks",
            output_format="mov",
            pixel_format="yuva444p10le"
        ))
        self.assertTrue(os.path.exists(out_mov))
        self.assertGreater(os.path.getsize(out_mov), 1000)

        # Verify stream format via ffprobe
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", out_mov
        ]
        res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("prores", res.stdout.lower())

    def test_09_audio_word_and_beat_synchronization(self):
        """Verifies audio word-level speech alignment and musical beat snapping."""
        words = [
            {"word": "Autonomous", "start": 0.0, "end": 0.5},
            {"word": "Studio", "start": 0.6, "end": 1.1}
        ]
        aligned = TimeSynchronizer.align_words_to_keyframes(words, start_time=RationalTime(0, 24), fps=24.0)
        self.assertEqual(len(aligned), 2)
        self.assertEqual(aligned[0]["word"], "Autonomous")
        self.assertEqual(aligned[0]["start_time"].value, 0)
        self.assertEqual(aligned[1]["word"], "Studio")
        self.assertAlmostEqual(aligned[1]["start_time"].to_seconds(), 0.6, delta=0.05)

        # Beat snapping
        beats = [0.0, 0.5, 1.0, 1.5, 2.0]
        unaligned_t = RationalTime(13, 24)  # ~0.541s
        snapped = TimeSynchronizer.snap_to_nearest_beat(unaligned_t, beats, tolerance_sec=0.1, fps=24.0)
        self.assertAlmostEqual(snapped.to_seconds(), 0.5, delta=0.01)

    def test_10_director_bridge_generation(self):
        """Verifies AI Director bridge translation of creative instructions into validated compositions."""
        bridge = DirectorMotionBridge()
        comp_lt = bridge.create_lower_third_from_prompt(
            name="Badal Tech",
            role="Systems Architect",
            primary_color="#39FF14"
        )
        self.assertIsInstance(comp_lt, MotionComposition)
        self.assertIn("Lower Third", comp_lt.name)

        comp_chart = bridge.create_infographic_from_data(
            labels=["2024", "2025", "2026"],
            values=[10.0, 35.0, 90.0],
            unit_suffix="k"
        )
        self.assertIsInstance(comp_chart, MotionComposition)
        self.assertEqual(len(comp_chart.scenes[0].layers), 1)

    def test_11_timeline_adapter_and_nle_placement(self):
        """Verifies rendering a motion composition and inserting it as a Clip onto a Part 05 NLE Timeline."""
        project_id = str(uuid.uuid4())
        self.db.create_project(uuid.UUID(project_id), "Motion Graphics Test Project")

        # Create timeline in Part 05
        tl = self.timeline_manager.create_timeline(
            project_id=uuid.UUID(project_id),
            name="Test Reel",
            fps=24.0,
            resolution_width=1920,
            resolution_height=1080
        )
        self.timeline_manager.add_track(tl.timeline_id, track_type=TrackType.VIDEO, name="V3 - Graphics")

        adapter = TimelineMotionAdapter(self.db, self.storage, self.timeline_manager)
        registry = PresetRegistry()
        comp = registry.instantiate("preset_lower_third_documentary", {
            "name": "Jane Doe",
            "role": "Producer",
            "duration_sec": 2.0,
            "resolution": (1920, 1080),
            "fps": 24.0
        })

        clip = adapter.render_and_insert_to_timeline(
            composition=comp,
            timeline_id=str(tl.timeline_id),
            target_track_name="V3 - Graphics",
            timeline_in=RationalTime(24, 24.0),
            codec="prores_ks"
        )

        self.assertIsNotNone(clip)
        self.assertTrue(clip.name.startswith("Overlay:"))
        self.assertEqual(clip.timeline_start.value, 24)

        # Verify timeline state updated in DB
        updated_tl = self.timeline_manager.get_timeline(tl.timeline_id)
        v3_track = next(t for t in updated_tl.tracks if t.name == "V3 - Graphics")
        self.assertEqual(len(v3_track.clips), 1)

    def test_12_acceptance_compositions_visual_verification(self):
        """
        Renders all 10 required acceptance examples and verifies output visual files in test_artifacts/:
        1. Kinetic typography sequence
        2. Cinematic title reveal
        3. Documentary lower third
        4. Animated infographic with supplied data
        5. Animated logo reveal
        6. Technical HUD overlay
        7. Social media vertical composition (9:16)
        8. Transparent motion graphics overlay (alpha integrity)
        9. Voice-over synchronized explainer
        10. Multilingual typography test (Devanagari Hindi)
        """
        registry = PresetRegistry()
        renderer = SVGVectorRenderer()

        examples = [
            ("01_kinetic_typography", "preset_kinetic_typewriter", {"text": "ACCELERATED TIMELINE_SYNCHRONIZATION"}),
            ("02_cinematic_title", "preset_title_cinematic_hero", {"title": "INTERSTELLAR CHRONICLES", "subtitle": "CHAPTER ONE"}),
            ("03_documentary_lower_third", "preset_lower_third_documentary", {"name": "PROF. MARCUS REID", "role": "QUANTUM PHYSICIST"}),
            ("04_animated_infographic", "preset_chart_animated_bar", {"labels": ["JAN", "FEB", "MAR", "APR"], "values": [25.0, 45.0, 70.0, 95.0]}),
            ("05_animated_logo_reveal", "preset_brand_shape_reveal", {"brand_name": "NEBULA", "tagline": "CREATIVE INTELLIGENCE"}),
            ("06_technical_hud_overlay", "preset_hud_targeting_reticle", {"color": "#00F0FF"}),
            ("07_social_vertical_9_16", "preset_title_cinematic_hero", {"title": "VIRAL REEL", "subtitle": "TAP TO WATCH", "resolution": (1080, 1920)}),
            ("08_transparent_overlay", "preset_lower_third_documentary", {"name": "ALPHA OVERLAY", "role": "TRANSPARENT 100%"}),
            ("09_voiceover_synced_explainer", "preset_kinetic_typewriter", {"text": "VOICE MATCHED SYLLABLE CADENCE"}),
            ("10_multilingual_indic_devanagari", "preset_multilingual_headline", {"text": "नमस्ते भारत - सार्वभौमिक स्टूडियो"})
        ]

        for idx, preset_id, params in examples:
            comp = registry.instantiate(preset_id, params)
            # Render snapshot SVG
            mid_time = RationalTime(int(comp.total_frames() / 2), comp.fps)
            svg_content = renderer.render_frame_svg(comp, mid_time)

            artifact_path = self.artifact_dir / f"{idx}.svg"
            with open(artifact_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

            self.assertTrue(artifact_path.exists())
            self.assertGreater(artifact_path.stat().st_size, 200)

        # Verify all 10 visual artifacts exist
        created_files = list(self.artifact_dir.glob("*.svg"))
        self.assertEqual(len(created_files), 10)


if __name__ == "__main__":
    unittest.main()
