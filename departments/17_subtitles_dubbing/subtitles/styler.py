"""
Subtitle Styler for Department 17.
Provides styling presets for Cinematic, Social Media / Reels (word-by-word karaoke),
and SDH Accessibility high-contrast captions.
"""
from __future__ import annotations

from typing import List
from ..core.models import SubtitleCue, SubtitleStylePreset, SubtitleTrack, WordTimestamp


class SubtitleStyler:
    """Applies typographical, color, and animation styling presets to subtitle tracks."""

    @classmethod
    def apply_style_preset(cls, track: SubtitleTrack, preset: SubtitleStylePreset) -> None:
        """Updates track styling and cue attributes according to preset."""
        track.style_preset = preset

        for cue in track.cues:
            if preset == SubtitleStylePreset.CINEMATIC:
                cue.style_override = {
                    "font": "Inter",
                    "font_size": 24,
                    "color": "#F0F0F0",
                    "stroke": "#00000080",
                    "placement": "bottom_center",
                }
            elif preset == SubtitleStylePreset.SDH_HIGH_CONTRAST:
                cue.style_override = {
                    "font": "Roboto",
                    "font_size": 26,
                    "color": "#FFFF00" if cue.speaker_id == "speaker_0" else "#00FFFF",
                    "background_box": "#000000CC",
                    "placement": "bottom_center",
                }
            elif preset == SubtitleStylePreset.SOCIAL_KINETIC:
                cue.style_override = {
                    "font": "Montserrat-Bold",
                    "font_size": 36,
                    "color": "#FFDE00",
                    "stroke": "#000000FF",
                    "stroke_width": 4,
                    "placement": "middle_center",
                    "all_caps": True,
                }
                cue.text = cue.text.upper()

    @classmethod
    def generate_karaoke_ass_cue(
        cls,
        words: List[WordTimestamp],
        speaker_id: str = "speaker_0",
    ) -> str:
        """
        Builds an ASS karaoke cue string with word-level highlight tags (\\k<centiseconds>).
        Used for dynamic TikTok/Shorts typography.
        """
        if not words:
            return ""

        parts: List[str] = []
        for w in words:
            duration_cs = max(1, int(round((w.end_time - w.start_time) * 100)))
            parts.append(rf"{{\k{duration_cs}}}{w.word}")

        return " ".join(parts)
