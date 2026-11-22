"""
Unit Tests for Professional Animation & Motion Graphics Engine.
Department: 09_motion_graphics & 06_creative_direction
Verifies easing physics, physiological cardiac pulses, EKG waveforms,
vascular streamlines, biometric HUDs/reticles, and AI Motion Design Director.
"""
import math
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from core.timeline.time_model import RationalTime
from departments.motion_graphics.core.composition_models import (
    LayerType,
    HUDType,
    MotionComposition,
    MotionLayer,
)
from departments.motion_graphics.core.easing_physics import (
    CardiacWaveformGenerator,
    EasingCurves,
)
from departments.motion_graphics.core.streamline_engine import (
    BloodParticle,
    StreamlineEngine,
)
from departments.motion_graphics.components.telemetry_hud import (
    TelemetryHUDBuilder,
)
from departments.motion_graphics.components.tracking_reticle import (
    TrackingReticleBuilder,
)
from departments.creative_direction.motion_director import (
    MotionDesignDirector,
    MotionDesignSystemSpec,
)


class TestMotionDesignEngine(unittest.TestCase):

    def test_01_easing_curves_mathematical_properties(self):
        """Verifies boundary conditions, continuity, and overshoot physics of easing curves."""
        # Linear
        self.assertEqual(EasingCurves.linear(0.0), 0.0)
        self.assertEqual(EasingCurves.linear(1.0), 1.0)
        self.assertEqual(EasingCurves.linear(0.5), 0.5)

        # Cubic Curves
        self.assertAlmostEqual(EasingCurves.ease_in_cubic(0.0), 0.0)
        self.assertAlmostEqual(EasingCurves.ease_in_cubic(1.0), 1.0)
        self.assertAlmostEqual(EasingCurves.ease_out_cubic(0.0), 0.0)
        self.assertAlmostEqual(EasingCurves.ease_out_cubic(1.0), 1.0)

        # Spring damped overshoot
        # At t=0, value is 0.0. At t=1.0, settles near 1.0. Intermediate values may exceed 1.0.
        self.assertAlmostEqual(EasingCurves.spring_damped(0.0), 0.0, places=4)
        overshoot = False
        for step in range(1, 100):
            t = step / 100.0
            val = EasingCurves.spring_damped(t)
            if val > 1.0:
                overshoot = True
                break
        self.assertTrue(overshoot, "Spring curve should exhibit natural overshoot.")

        # Systolic pulse: rapid peak at phase=0 then exponential decay
        peak = EasingCurves.systolic_pulse(0.0, amplitude=0.5, decay=7.0)
        trough = EasingCurves.systolic_pulse(0.9, amplitude=0.5, decay=7.0)
        self.assertGreater(peak, trough)
        self.assertAlmostEqual(peak, 1.5, places=2)

    def test_02_cardiac_waveform_generator_ekg_and_arrest(self):
        """Verifies resting P-Q-R-S-T peaks and swimming arrest flatline deflection."""
        # Resting rhythm: sample through one full cycle at 60 BPM (1 second per cycle)
        samples = [CardiacWaveformGenerator.sample_ekg_waveform(t / 1000.0, is_swimming_jet=False) for t in range(1000)]
        max_val = max(samples)
        min_val = min(samples)

        # R wave spike should reach approximately 0.95
        self.assertGreater(max_val, 0.85)
        # S / Q dip should be negative
        self.assertLess(min_val, -0.2)

        # Swimming jet propulsion: systemic arrest flatline with micro-tremor (|val| <= 0.05)
        arrest_samples = [CardiacWaveformGenerator.sample_ekg_waveform(t / 50.0, is_swimming_jet=True) for t in range(50)]
        for s in arrest_samples:
            self.assertLessEqual(abs(s), 0.05, "Arrest waveform must remain near flatline.")

    def test_03_streamline_engine_particles_and_oxygenation_shift(self):
        """Verifies vascular fluid particle movement, curved spline interpolation, and color-shifting."""
        engine = StreamlineEngine()
        p_start = (500, 300)
        p_end = (500, 800)

        # Midpoint on straight line vs with curvature
        pt_straight = engine.interpolate_streamline_point(p_start, p_end, 0.5, curvature=0.0)
        self.assertEqual(pt_straight, (500, 550))

        pt_curved = engine.interpolate_streamline_point(p_start, p_end, 0.5, curvature=120.0)
        self.assertNotEqual(pt_curved[0], 500)  # Displaced along perpendicular axis

        # Oxygenation shift: before threshold (progress=0.1) should be venous cobalt
        c_venous = engine.get_particle_color_bgr(0.1, gill_entry_threshold=0.45)
        # After gill passage (progress=0.8) should shift to oxygenated cyan
        c_oxygenated = engine.get_particle_color_bgr(0.8, gill_entry_threshold=0.45)

        self.assertNotEqual(c_venous, c_oxygenated)
        # Cyan has high green/blue channels (BGR: Blue=255, Green=240)
        self.assertGreater(c_oxygenated[0], 200)  # B
        self.assertGreater(c_oxygenated[1], 200)  # G

        # BloodParticle progress
        particle = BloodParticle(streamline_id=1, offset_t=0.2, speed=2.0)
        prog_0 = particle.get_progress(0.0)
        prog_half = particle.get_progress(0.25)
        self.assertAlmostEqual(prog_0, 0.2)
        self.assertAlmostEqual(prog_half, 0.7)

    def test_04_telemetry_hud_builder_components(self):
        """Verifies construction of cardiac telemetry HUD and oceanographic depth gauge layers."""
        cardiac_layer = TelemetryHUDBuilder.create_cardiac_telemetry_layer(
            heart_type="systemic",
            base_bpm=58.0,
            duration_seconds=5.0,
            fps=30.0
        )
        self.assertEqual(cardiac_layer.layer_type, LayerType.HUD)
        self.assertEqual(cardiac_layer.element.hud_type, HUDType.TELEMETRY)
        self.assertIn("BPM", cardiac_layer.element.telemetry_data)
        self.assertIn("HEMOCYANIN_O2", cardiac_layer.element.telemetry_data)
        self.assertEqual(len(cardiac_layer.animations), 1)

        # Waveform points generation
        pts = TelemetryHUDBuilder.generate_waveform_points(duration_seconds=2.0, fps=30.0, width_px=300.0)
        self.assertEqual(len(pts), 60)
        self.assertEqual(pts[0][0], 0.0)
        self.assertEqual(pts[-1][0], 300.0)

        # Depth gauge
        depth_layer = TelemetryHUDBuilder.create_oceanographic_depth_gauge(depth_meters=55.0)
        self.assertEqual(depth_layer.element.telemetry_data["DEPTH"], "55.0 M")

    def test_05_tracking_reticle_builder_components(self):
        """Verifies construction of biometric tracking reticle and anatomical callout brackets."""
        reticle = TrackingReticleBuilder.create_biometric_reticle_layer(
            label="BRACHIAL_SUCKER_04",
            pos=(540.0, 960.0),
            duration_seconds=4.0,
            fps=30.0
        )
        self.assertEqual(reticle.layer_type, LayerType.HUD)
        self.assertEqual(reticle.element.hud_type, HUDType.RETICLE)
        self.assertEqual(reticle.element.telemetry_data["TARGET"], "BRACHIAL_SUCKER_04")
        self.assertEqual(len(reticle.animations), 2)  # Scale spring + rotation

        callout = TrackingReticleBuilder.create_anatomical_callout_bracket(
            organ_name="Systemic Heart",
            hindi_label="मुख्य दिल",
            pos=(540.0, 1100.0)
        )
        self.assertEqual(callout.element.telemetry_data["ORGAN"], "Systemic Heart")
        self.assertEqual(callout.element.telemetry_data["LABEL_HI"], "मुख्य दिल")

    def test_06_motion_design_director_synthesis(self):
        """Verifies AI Motion Design Director scene motif mapping and composition synthesis."""
        director = MotionDesignDirector()
        scenes = [
            {"title": "Scene 1: Hook", "duration_seconds": 6.0, "narration_hi": "समुद्र में एक ऐसा जीव है..."},
            {"title": "Scene 2: Tentacles", "duration_seconds": 8.0, "narration_hi": "इसके आठ हाथ होते हैं..."},
            {"title": "Scene 3: Gills", "duration_seconds": 11.0, "narration_hi": "दो दिल खून को गलफड़ों तक पहुँचाते हैं..."},
            {"title": "Scene 5: Pause", "duration_seconds": 8.0, "narration_hi": "जब यह तैरता है, तो दिल रुक जाता है..."}
        ]

        direction = director.direct_project_motion(
            project_id=str(uuid4()),
            topic="Octopus 3 Hearts",
            script_scenes=scenes,
            resolution=(1080, 1920),
            fps=30.0
        )

        self.assertEqual(len(direction["scenes"]), 4)
        self.assertEqual(direction["scenes"][0]["motion_motif"], "title_hero")
        self.assertEqual(direction["scenes"][1]["motion_motif"], "macro_biometrics")
        self.assertEqual(direction["scenes"][2]["motion_motif"], "hemodynamics")
        self.assertEqual(direction["scenes"][3]["motion_motif"], "cardiac_arrest")

        # Synthesize into MotionComposition
        comp = director.synthesize_motion_composition("proj_test", direction)
        self.assertIsInstance(comp, MotionComposition)
        self.assertEqual(len(comp.scenes), 4)
        self.assertEqual(comp.resolution, (1080, 1920))
        self.assertEqual(comp.fps, 30.0)
        # Macro biometrics scene must have a reticle layer
        scene_2 = comp.scenes[1]
        self.assertTrue(any(l.element and getattr(l.element, "hud_type", None) == HUDType.RETICLE for l in scene_2.layers))


if __name__ == "__main__":
    unittest.main()
