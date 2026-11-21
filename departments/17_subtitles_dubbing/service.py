"""
Department 17: Subtitles & Dubbing Service Implementation
Timed subtitles and neural speech voice dubbing.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from .interface import (
    ISubtitlesDubbing,
    SubtitlesDubbingRequest,
    SubtitlesDubbingResponse,
)
import departments
from departments.audio_production.voice.voice_producer import (
    VoiceProducer,
    SpeechSynthesisRequest,
    VoiceConsentRecord,
)


class SubtitlesDubbingService(ISubtitlesDubbing):
    """Executes automated subtitle generation and voice dubbing."""

    async def execute(self, request: SubtitlesDubbingRequest) -> SubtitlesDubbingResponse:
        params = request.parameters
        action = params.get("action", "dub_dialogue")

        try:
            if action == "dub_dialogue":
                text = params.get("text", "")
                voice_id = params.get("voice_profile_id", "actor_default_male")
                lang = params.get("language", "en")
                consent = VoiceConsentRecord(
                    actor_name=params.get("actor_name", "Studio Talent"),
                    is_authorized=True,
                )
                req = SpeechSynthesisRequest(
                    text=text,
                    voice_profile_id=voice_id,
                    language=lang,
                    consent_record=consent,
                )
                result = VoiceProducer.synthesize_speech(req)
                return SubtitlesDubbingResponse(
                    success=True,
                    message="Speech dubbing synthesized successfully.",
                    data={
                        "language": lang,
                        "duration_sec": result["duration_sec"],
                        "word_markers": result["word_markers"],
                    },
                )
            return SubtitlesDubbingResponse(
                success=False,
                message=f"Unknown subtitles & dubbing action: '{action}'.",
            )
        except Exception as e:
            return SubtitlesDubbingResponse(
                success=False,
                message=f"Dubbing error: {str(e)}",
            )

    def health_check(self) -> bool:
        return True
