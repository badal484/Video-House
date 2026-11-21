"""
Typography and Multilingual Text Engine.
Provides font metrics, dynamic line wrapping, safe-margin enforcement,
and complex script (Devanagari / Indic) grapheme cluster tokenization.
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple
from ..core.composition_models import TextElement, TextRevealMode


class TypographyEngine:
    """
    Handles typography layouts, grapheme cluster segmentation, and kinetic text reveals.
    """

    # Common standard system fonts or bundled fallbacks
    FONT_FALLBACK_STACK = {
        "Inter": ["Inter", "Helvetica Neue", "Arial", "sans-serif"],
        "Montserrat": ["Montserrat", "Arial Black", "sans-serif"],
        "Roboto Mono": ["Roboto Mono", "Courier New", "monospace"],
        "Playfair Display": ["Playfair Display", "Georgia", "serif"],
        "Noto Sans Devanagari": ["Noto Sans Devanagari", "Lohit Devanagari", "Mangal", "sans-serif"],
    }

    @classmethod
    def get_font_family_css(cls, font_family: str) -> str:
        """Returns CSS font-family fallback string with single-quoted family names."""
        stack = cls.FONT_FALLBACK_STACK.get(font_family, [font_family, "sans-serif"])
        return ", ".join([f"'{f}'" if " " in f else f for f in stack])

    @staticmethod
    def tokenize_grapheme_clusters(text: str) -> List[str]:
        """
        Tokenizes text into true grapheme clusters (preserving Indic matras/conjuncts).
        In Devanagari, characters like virama (U+094D) and vowel signs (U+093E-U+094C)
        must remain bonded to the preceding consonant.
        """
        if not text:
            return []

        clusters: List[str] = []
        current_cluster = ""
        prev_was_virama = False

        for char in text:
            cat = unicodedata.category(char)
            is_virama = (char == "\u094d")
            # If previous character was virama, attach the following consonant to form conjunct
            if prev_was_virama:
                current_cluster += char
                prev_was_virama = is_virama
            elif cat in ("Mn", "Mc") or is_virama:
                if not current_cluster:
                    current_cluster = char
                else:
                    current_cluster += char
                prev_was_virama = is_virama
            else:
                if current_cluster:
                    clusters.append(current_cluster)
                current_cluster = char
                prev_was_virama = False

        if current_cluster:
            clusters.append(current_cluster)

        return clusters

    @classmethod
    def wrap_text(
        cls,
        text: str,
        font_size: float,
        max_width: float,
        avg_char_aspect: float = 0.55
    ) -> List[str]:
        """
        Wraps text into lines that do not exceed max_width.
        """
        if not text:
            return []

        words = text.split(" ")
        lines: List[str] = []
        current_line = []
        current_length_px = 0.0
        space_width = font_size * avg_char_aspect

        for word in words:
            word_width = len(word) * font_size * avg_char_aspect
            if current_line and (current_length_px + space_width + word_width) > max_width:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length_px = word_width
            else:
                current_line.append(word)
                current_length_px += (space_width if current_line else 0.0) + word_width

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    @classmethod
    def compute_reveal_state(
        cls,
        element: TextElement,
        progress: float  # 0.0 to 1.0 progress across the reveal animation
    ) -> Dict[str, any]:
        """
        Computes visible text or active opacity for kinetic text reveal modes.
        """
        text = element.text
        mode = element.reveal_mode

        if mode == TextRevealMode.NONE or progress >= 1.0:
            return {
                "visible_text": text,
                "cursor_visible": False,
                "active_index": len(text),
                "total_units": len(text)
            }

        if progress <= 0.0:
            return {
                "visible_text": "" if mode in (TextRevealMode.TYPEWRITER, TextRevealMode.CHAR_BY_CHAR, TextRevealMode.WORD_BY_WORD) else text,
                "cursor_visible": element.show_cursor,
                "active_index": 0,
                "total_units": len(text)
            }

        if mode == TextRevealMode.TYPEWRITER:
            clusters = cls.tokenize_grapheme_clusters(text)
            total = len(clusters)
            count = int(round(progress * total))
            visible_str = "".join(clusters[:count])
            # Blink cursor every 0.25s phase (modeled via progress modulo)
            blink = (int(progress * 20) % 2 == 0) and element.show_cursor
            return {
                "visible_text": visible_str,
                "cursor_visible": blink,
                "active_index": count,
                "total_units": total
            }

        elif mode == TextRevealMode.CHAR_BY_CHAR:
            clusters = cls.tokenize_grapheme_clusters(text)
            total = len(clusters)
            count = int(round(progress * total))
            return {
                "visible_text": "".join(clusters[:count]),
                "cursor_visible": False,
                "active_index": count,
                "total_units": total
            }

        elif mode == TextRevealMode.WORD_BY_WORD:
            words = text.split(" ")
            total = len(words)
            count = int(round(progress * total))
            return {
                "visible_text": " ".join(words[:count]),
                "cursor_visible": False,
                "active_index": count,
                "total_units": total
            }

        elif mode == TextRevealMode.LINE_BY_LINE:
            lines = text.split("\n")
            total = len(lines)
            count = int(round(progress * total))
            return {
                "visible_text": "\n".join(lines[:count]),
                "cursor_visible": False,
                "active_index": count,
                "total_units": total
            }

        return {
            "visible_text": text,
            "cursor_visible": False,
            "active_index": len(text),
            "total_units": len(text)
        }
