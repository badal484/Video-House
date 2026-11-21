"""
Voice Assignment Manager for Department 17.
Matches speakers to neural voice profiles based on gender, pitch estimate, and character persona.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from ..core.models import SpeakerRecord, Transcript
from .consent_manager import ConsentManager


class VoiceAssignmentManager:
    """Casts voice profiles for transcript speakers and validates consent."""

    DEFAULT_VOICE_LIBRARY = {
        "en": {
            "male": "elevenlabs_adam",
            "female": "elevenlabs_rachel",
            "neutral": "kokoro_default_en",
        },
        "es": {
            "male": "elevenlabs_mateo",
            "female": "elevenlabs_sofia",
            "neutral": "kokoro_default_es",
        },
        "hi": {
            "male": "elevenlabs_aarav",
            "female": "elevenlabs_ananya",
            "neutral": "kokoro_default_hi",
        },
        "fr": {
            "male": "elevenlabs_antoine",
            "female": "elevenlabs_camille",
            "neutral": "kokoro_default_fr",
        },
        "de": {
            "male": "elevenlabs_klaus",
            "female": "elevenlabs_marlene",
            "neutral": "kokoro_default_de",
        },
    }

    def __init__(self, consent_manager: Optional[ConsentManager] = None):
        self.consent_manager = consent_manager or ConsentManager()

    def assign_voices(
        self,
        transcript: Transcript,
        target_language: str,
        custom_mappings: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Determines voice profile IDs for each speaker in the transcript.
        Validates consent authorization for each mapped voice.
        """
        mappings: Dict[str, str] = {}
        target_lang = target_language.lower()
        library = self.DEFAULT_VOICE_LIBRARY.get(target_lang, self.DEFAULT_VOICE_LIBRARY["en"])

        for speaker in transcript.speakers:
            spk_id = speaker.speaker_id

            if custom_mappings and spk_id in custom_mappings:
                chosen_voice = custom_mappings[spk_id]
            else:
                gender = speaker.gender.lower()
                chosen_voice = library.get(gender, library["neutral"])

            # Verify consent authorization
            self.consent_manager.verify_authorization(chosen_voice)

            speaker.voice_profile_id = chosen_voice
            mappings[spk_id] = chosen_voice

        return mappings
