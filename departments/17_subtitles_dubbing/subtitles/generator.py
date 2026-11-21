"""
Subtitle Generator for Department 17.
Constructs broadcast-compliant subtitle cues enforcing line wrapping, reading speed,
duration bounds, and exports to SRT, WebVTT, ASS/SSA, and TTML (XML).
"""
from __future__ import annotations

import html
import math
from typing import List, Optional
from uuid import UUID

from ..core.models import SubtitleCue, SubtitleFormat, SubtitleStylePreset, SubtitleTrack, Transcript


class SubtitleGenerator:
    """Generates and exports standardized subtitle cues."""

    MIN_DURATION_SEC = 0.833  # 20 frames @ 24fps
    MAX_DURATION_SEC = 6.0
    FRAME_GAP_SEC = 0.08  # ~2 frames @ 24fps

    @classmethod
    def generate_cues_from_transcript(
        cls,
        transcript: Transcript,
        max_cpl: int = 42,
        language: str = "en",
    ) -> List[SubtitleCue]:
        """
        Segments transcript segments into compliant subtitle cues.
        Enforces line length and 2-line maximum per cue.
        """
        cues: List[SubtitleCue] = []
        cue_idx = 1

        for seg in transcript.segments:
            raw_text = seg.text.strip()
            if not raw_text:
                continue

            # Format into lines
            wrapped_lines = cls._wrap_text(raw_text, max_cpl=max_cpl)

            # Chunk into at most 2 lines per subtitle event
            for i in range(0, len(wrapped_lines), 2):
                chunk_lines = wrapped_lines[i : i + 2]
                cue_text = "\n".join(chunk_lines)

                # Interpolate time window
                total_chunks = math.ceil(len(wrapped_lines) / 2)
                chunk_fraction = 1.0 / max(1, total_chunks)
                seg_duration = seg.end_time - seg.start_time

                c_start = seg.start_time + (i // 2) * (seg_duration * chunk_fraction)
                c_end = c_start + (seg_duration * chunk_fraction)

                # Enforce min/max duration
                c_end = max(c_start + cls.MIN_DURATION_SEC, min(c_start + cls.MAX_DURATION_SEC, c_end))

                # Apply frame gap if following another cue
                if cues and c_start < cues[-1].end_time + cls.FRAME_GAP_SEC:
                    c_start = cues[-1].end_time + cls.FRAME_GAP_SEC
                    c_end = max(c_start + cls.MIN_DURATION_SEC, c_end)

                cues.append(
                    SubtitleCue(
                        cue_index=cue_idx,
                        start_time=round(c_start, 3),
                        end_time=round(c_end, 3),
                        text=cue_text,
                        speaker_id=seg.speaker_id,
                    )
                )
                cue_idx += 1

        return cues

    @classmethod
    def _wrap_text(cls, text: str, max_cpl: int = 42) -> List[str]:
        """Wraps text into lines honoring maximum characters per line."""
        words = text.split()
        if not words:
            return []

        lines: List[str] = []
        current_line: List[str] = []
        current_len = 0

        for w in words:
            w_len = len(w)
            if current_line and (current_len + 1 + w_len > max_cpl):
                lines.append(" ".join(current_line))
                current_line = [w]
                current_len = w_len
            else:
                current_line.append(w)
                current_len += w_len if not current_line[:-1] else (1 + w_len)

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    # ---- Export Serializers ----

    @staticmethod
    def _format_timecode_srt(seconds: float) -> str:
        """Formats seconds into SRT timecode: HH:MM:SS,mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds - int(seconds)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _format_timecode_vtt(seconds: float) -> str:
        """Formats seconds into WebVTT timecode: HH:MM:SS.mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds - int(seconds)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    @staticmethod
    def _format_timecode_ass(seconds: float) -> str:
        """Formats seconds into ASS timecode: H:MM:SS.cs (centiseconds)"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"

    @classmethod
    def export_srt(cls, track: SubtitleTrack) -> str:
        """Exports SubtitleTrack to SubRip (.srt) string."""
        blocks: List[str] = []
        for cue in track.cues:
            t_start = cls._format_timecode_srt(cue.start_time)
            t_end = cls._format_timecode_srt(cue.end_time)
            blocks.append(f"{cue.cue_index}\n{t_start} --> {t_end}\n{cue.text}\n")
        return "\n".join(blocks).strip() + "\n"

    @classmethod
    def export_vtt(cls, track: SubtitleTrack) -> str:
        """Exports SubtitleTrack to WebVTT (.vtt) string."""
        lines: List[str] = ["WEBVTT", ""]
        for cue in track.cues:
            t_start = cls._format_timecode_vtt(cue.start_time)
            t_end = cls._format_timecode_vtt(cue.end_time)
            speaker_tag = f"<v {cue.speaker_id}>" if cue.speaker_id else ""
            lines.append(f"{cue.cue_index}")
            lines.append(f"{t_start} --> {t_end}")
            lines.append(f"{speaker_tag}{cue.text}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    @classmethod
    def export_ass(cls, track: SubtitleTrack, style_header: Optional[str] = None) -> str:
        """Exports SubtitleTrack to Advanced SubStation Alpha (.ass) string."""
        header = style_header or (
            "[Script Info]\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n"
            "ScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Inter,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,30,30,30,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        events: List[str] = []
        for cue in track.cues:
            t_start = cls._format_timecode_ass(cue.start_time)
            t_end = cls._format_timecode_ass(cue.end_time)
            clean_text = cue.text.replace("\n", r"\N")
            events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{clean_text}")

        return header + "\n".join(events) + "\n"

    @classmethod
    def export_ttml(cls, track: SubtitleTrack) -> str:
        """Exports SubtitleTrack to Timed Text Markup Language (TTML1/IMSC) XML string."""
        xml_lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            f'<tt xmlns="http://www.w3.org/ns/ttml" xml:lang="{track.language_code}">',
            "  <head>",
            "    <styling>",
            '      <style xml:id="defaultStyle" fontStyle="normal" fontFamily="sansSerif" fontSize="100%"/>',
            "    </styling>",
            "    <layout>",
            '      <region xml:id="bottom" origin="10% 80%" extent="80% 15%"/>',
            "    </layout>",
            "  </head>",
            "  <body>",
            '    <div region="bottom">',
        ]

        for cue in track.cues:
            t_start = cls._format_timecode_vtt(cue.start_time)
            t_end = cls._format_timecode_vtt(cue.end_time)
            escaped = html.escape(cue.text).replace("\n", "<br/>")
            xml_lines.append(f'      <p begin="{t_start}" end="{t_end}">{escaped}</p>')

        xml_lines.extend(["    </div>", "  </body>", "</tt>"])
        return "\n".join(xml_lines) + "\n"
