"""
Mastering Engine: Loudness Normalization, True Peak Limiting & Stem Export
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple
import numpy as np
import scipy.io.wavfile

from ..core.session_models import AudioSession, LoudnessStandard
from ..dsp.loudness import LoudnessMeter
from .multitrack_mixer import MultitrackMixer


class MasteringEngine:
    """Mastering and delivery conformance engine."""

    @staticmethod
    def export_wav(audio: np.ndarray, sample_rate: int, output_path: str, bit_depth: int = 24) -> str:
        """Exports stereo or mono float32 array to a compliant WAV file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        clipped = np.clip(audio, -1.0, 1.0)

        if bit_depth == 16:
            int_pcm = (clipped * 32767.0).astype(np.int16)
        else:
            # 24-bit in 32-bit int representation
            int_pcm = (clipped * 8388607.0).astype(np.int32)

        # scipy.io.wavfile expects (samples, channels)
        if int_pcm.ndim > 1:
            scipy.io.wavfile.write(output_path, sample_rate, int_pcm.T)
        else:
            scipy.io.wavfile.write(output_path, sample_rate, int_pcm)
        return output_path

    @classmethod
    def master_session(
        cls,
        session: AudioSession,
        output_dir: str,
        standard: LoudnessStandard = LoudnessStandard.YOUTUBE,
        export_stems: bool = True,
    ) -> Dict[str, Any]:
        """
        Renders, masters, and exports a complete AudioSession to broadcast/streaming targets.
        """
        os.makedirs(output_dir, exist_ok=True)
        sample_rate = session.sample_rate

        # 1. Render multitrack mix
        raw_mix, stems = MultitrackMixer.render_session(session)

        # 2. Loudness normalization to standard
        master_mix, measured = LoudnessMeter.normalize_loudness(raw_mix, sample_rate, standard=standard)

        # 3. Export Master WAV
        master_path = os.path.join(output_dir, f"{session.session_id}_master_{standard.value.lower()}.wav")
        cls.export_wav(master_mix, sample_rate, master_path, bit_depth=24)

        exported_files = {
            "master_wav": master_path,
        }

        # 4. Export Stems if requested
        if export_stems:
            stem_paths = {}
            for stem_name, stem_data in stems.items():
                p = os.path.join(output_dir, f"{session.session_id}_stem_{stem_name}.wav")
                cls.export_wav(stem_data, sample_rate, p, bit_depth=24)
                stem_paths[stem_name] = p
            exported_files["stems"] = stem_paths

        return {
            "session_id": session.session_id,
            "standard": standard.value,
            "target_lufs": standard.target_lufs,
            "integrated_lufs": measured["integrated_lufs"],
            "true_peak_db": measured["true_peak_db"],
            "loudness_range_lu": measured["loudness_range_lu"],
            "exported_files": exported_files,
        }
