"""
Advanced Easing & Physiological Physics Engine.
Department: 09_motion_graphics/core
Provides natural easing, spring dynamics, and physiological cardiac pulse curves.
"""
import math
from typing import Callable, Dict


class EasingCurves:
    """Library of mathematical easing curves and biological acceleration curves."""

    @staticmethod
    def linear(t: float) -> float:
        return max(0.0, min(1.0, t))

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        t = max(0.0, min(1.0, t))
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        t = max(0.0, min(1.0, t))
        return 1.0 - math.pow(1.0 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        t = max(0.0, min(1.0, t))
        return 4.0 * t * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 3) / 2.0

    @staticmethod
    def spring_damped(t: float, damping: float = 7.0, frequency: float = 14.0) -> float:
        """Simulates physical spring overshoot and natural settle."""
        t = max(0.0, min(1.0, t))
        return 1.0 - math.exp(-damping * t) * math.cos(frequency * t)

    @staticmethod
    def systolic_pulse(phase: float, amplitude: float = 0.45, decay: float = 7.0) -> float:
        """
        Physiological cardiac pulse curve:
        Rapid systolic ejection contraction followed by smooth exponential diastolic filling.
        phase: normalized [0.0, 1.0) cycle time.
        """
        phase = phase % 1.0
        return 1.0 + amplitude * math.exp(-decay * phase)

    @staticmethod
    def dual_systolic_beat(phase: float, amplitude: float = 0.48) -> float:
        """
        Two-stage cephalopod systemic heartbeat:
        Atrial contraction at phase 0.0 followed by vigorous ventricular ejection at phase 0.22.
        """
        phase = phase % 1.0
        atrial = 0.55 * math.exp(-8.0 * phase)
        ventricular = 0.35 * math.exp(-8.0 * max(0.0, phase - 0.22))
        return 1.0 + amplitude * (atrial + ventricular)


class CardiacWaveformGenerator:
    """
    Parametric P-Q-R-S-T Electrocardiogram and Hemodynamic Pressure waveform generator.
    Transitions dynamically between normal 60 BPM rhythm and swimming jet arrest flatline.
    """

    @staticmethod
    def sample_ekg_waveform(
        time_seconds: float,
        is_swimming_jet: bool = False,
        base_bpm: float = 60.0
    ) -> float:
        """
        Returns normalized vertical deflection [-1.0, 1.0] for time_seconds.
        """
        if is_swimming_jet:
            # Jet propulsion: Systemic arrest flatline with subtle micro-tremor
            return 0.03 * math.sin(time_seconds * 24.0)

        # Normal resting rhythm (P-Q-R-S-T)
        cycle_duration = 60.0 / base_bpm
        cycle = (time_seconds / cycle_duration) % 1.0

        if 0.20 <= cycle < 0.24:
            # P wave (atrial depolarization)
            p_t = (cycle - 0.20) / 0.04
            return 0.20 * math.sin(math.pi * p_t)
        elif 0.28 <= cycle < 0.30:
            # Q wave (septal depolarization dip)
            q_t = (cycle - 0.28) / 0.02
            return -0.15 * math.sin(math.pi * q_t)
        elif 0.30 <= cycle <= 0.33:
            # R wave (ventricular depolarization sharp spike)
            r_t = (cycle - 0.30) / 0.03
            return 0.95 * math.sin(math.pi * r_t)
        elif 0.33 < cycle < 0.36:
            # S wave (ventricular terminal dip)
            s_t = (cycle - 0.33) / 0.03
            return -0.28 * math.sin(math.pi * s_t)
        elif 0.42 <= cycle < 0.50:
            # T wave (ventricular repolarization)
            t_t = (cycle - 0.42) / 0.08
            return 0.28 * math.sin(math.pi * t_t)
        else:
            # Baseline isoelectric line
            return 0.0
