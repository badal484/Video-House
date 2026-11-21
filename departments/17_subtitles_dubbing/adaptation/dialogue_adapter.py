"""
Dialogue Adapter for Department 17.
Performs syllable counting, speech duration estimation, and isochronic pacing adaptation
to fit target translations into source dialogue time windows without unnatural speedups.
"""
from __future__ import annotations

import re
from typing import Optional


class DialogueAdapter:
    """
    Adapts translated dialogue to match source temporal bounds (isochrony).
    Bounds tempo scaling strictly within [0.90, 1.15] to prevent unnatural chipmunk/dragged speech.
    """

    MIN_TEMPO = 0.90
    MAX_TEMPO = 1.15
    AVG_SYLLABLES_PER_SEC = 4.2  # Standard conversational cadence

    @classmethod
    def estimate_syllables(cls, text: str, language: str = "en") -> int:
        """Estimates syllable count using vowel cluster heuristics."""
        clean_text = text.lower().strip()
        if not clean_text:
            return 1

        # Indic languages (Hindi, etc.): roughly 1 syllable per akshara/vowel sign
        if language in {"hi", "bn", "mr", "gu", "pa"}:
            matras = re.findall(r"[\u0904-\u0914\u093E-\u094C\u0960-\u0963]", clean_text)
            consonants = re.findall(r"[\u0915-\u0939]", clean_text)
            return max(1, len(matras) + (len(consonants) // 2))

        # Japanese: roughly 1 mora per character
        if language == "ja":
            return max(1, len(re.sub(r"\s+", "", clean_text)))

        # Latin languages (English, Spanish, etc.)
        words = re.findall(r"\b[a-záéíóúñäöü]+\b", clean_text)
        total_syllables = 0
        for w in words:
            # Count vowel groups
            vowel_matches = re.findall(r"[aeiouyáéíóúäöü]+", w)
            count = len(vowel_matches)
            # Adjust for silent trailing 'e' in English
            if language == "en" and w.endswith("e") and not w.endswith("le") and count > 1:
                count -= 1
            total_syllables += max(1, count)

        return max(1, total_syllables)

    @classmethod
    def calculate_estimated_duration(cls, text: str, language: str = "en") -> float:
        """Estimates speech duration in seconds at natural conversational cadence."""
        syllables = cls.estimate_syllables(text, language)
        return round(syllables / cls.AVG_SYLLABLES_PER_SEC, 3)

    @classmethod
    def adapt_dialogue(
        cls,
        translated_text: str,
        target_duration_sec: float,
        target_language: str = "es",
    ) -> tuple[str, float]:
        """
        Adapts dialogue to fit target_duration_sec.
        Returns:
            adapted_text (str): Dialogue adjusted for pacing
            tempo_scale (float): Required playback tempo multiplier (bounded in [0.90, 1.15])
        """
        estimated_sec = cls.calculate_estimated_duration(translated_text, target_language)
        ratio = estimated_sec / max(0.5, target_duration_sec)

        # If dialogue fits comfortably within standard tempo bounds
        if cls.MIN_TEMPO <= ratio <= cls.MAX_TEMPO:
            return translated_text, round(ratio, 3)

        adapted = translated_text

        # If dialogue is too long (ratio > 1.15), prune filler words
        if ratio > cls.MAX_TEMPO:
            filler_words = ["pues", "bueno", "en realidad", "de hecho", "sabes", "actually", "you know", "basically", "मतलब", "तो फिर"]
            for filler in filler_words:
                pattern = re.compile(r"\b" + re.escape(filler) + r"\b,?\s*", re.IGNORECASE)
                adapted = pattern.sub("", adapted)

            # Re-estimate after pruning
            new_est = cls.calculate_estimated_duration(adapted, target_language)
            new_ratio = new_est / max(0.5, target_duration_sec)
            tempo = min(cls.MAX_TEMPO, max(cls.MIN_TEMPO, new_ratio))
            return adapted.strip(), round(tempo, 3)

        # If dialogue is too short (ratio < 0.90), tempo slows down slightly
        tempo = max(cls.MIN_TEMPO, ratio)
        return adapted, round(tempo, 3)
