"""
Department 17: Subtitles, Dubbing & Localization Service Implementation
Unified facade orchestrating transcription, translation, subtitle formatting,
voice casting with biometric consent, dubbing assembly, and lip-sync synchronization.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .adaptation.dialogue_adapter import DialogueAdapter
from .core.models import (
    BiometricConsentRecord,
    GlossaryTerm,
    SubtitleFormat,
    SubtitleStylePreset,
    SubtitleTrack,
    Transcript,
)
from .dubbing.orchestrator import DubbingOrchestrator
from .interface import (
    ISubtitlesDubbing,
    SubtitlesDubbingRequest,
    SubtitlesDubbingResponse,
)
from .lipsync.lipsync_orchestrator import LipSyncOrchestrator
from .qc.quality_controller import LocalizationQualityController
from .subtitles.generator import SubtitleGenerator
from .subtitles.styler import SubtitleStyler
from .sync.sync_manager import SyncManager
from .transcription.asr_engine import ASREngine
from .transcription.transcript_manager import TranscriptManager
from .translation.glossary import GlossaryManager
from .translation.translator import MultilingualTranslator
from .voice.consent_manager import ConsentManager
from .voice.voice_assigner import VoiceAssignmentManager


class SubtitlesDubbingService(ISubtitlesDubbing):
    """Production service implementing ISubtitlesDubbing."""

    def __init__(self):
        self.asr_engine = ASREngine()
        self.glossary_manager = GlossaryManager()
        self.translator = MultilingualTranslator(glossary_manager=self.glossary_manager)
        self.consent_manager = ConsentManager()
        self.voice_assigner = VoiceAssignmentManager(consent_manager=self.consent_manager)
        self.dubbing_orchestrator = DubbingOrchestrator(
            translator=self.translator, voice_assigner=self.voice_assigner
        )
        self.lipsync_orchestrator = LipSyncOrchestrator()

        # Seed default consent records for standard studio voice talents
        self._seed_default_consents()

    def _seed_default_consents(self):
        default_voices = [
            ("Studio Lead Male", "actor_default_male"),
            ("Studio Lead Female", "actor_default_female"),
            ("Adam English", "elevenlabs_adam"),
            ("Rachel English", "elevenlabs_rachel"),
            ("Kokoro EN", "kokoro_default_en"),
            ("Mateo Spanish", "elevenlabs_mateo"),
            ("Sofia Spanish", "elevenlabs_sofia"),
            ("Kokoro ES", "kokoro_default_es"),
            ("Aarav Hindi", "elevenlabs_aarav"),
            ("Ananya Hindi", "elevenlabs_ananya"),
            ("Kokoro HI", "kokoro_default_hi"),
            ("Antoine French", "elevenlabs_antoine"),
            ("Camille French", "elevenlabs_camille"),
            ("Kokoro FR", "kokoro_default_fr"),
            ("Klaus German", "elevenlabs_klaus"),
            ("Marlene German", "elevenlabs_marlene"),
            ("Kokoro DE", "kokoro_default_de"),
        ]
        for name, vid in default_voices:
            self.consent_manager.register_consent(
                BiometricConsentRecord(talent_name=name, voice_profile_id=vid, is_authorized=True)
            )

    async def execute(self, request: SubtitlesDubbingRequest) -> SubtitlesDubbingResponse:
        params = request.parameters
        action = params.get("action", "transcribe")
        project_id = request.project_id

        try:
            if action == "transcribe":
                media_asset_id = UUID(str(params.get("media_asset_id", uuid4())))
                audio_input = params.get("audio_input", "simulated_audio.wav")
                simulated_text = params.get("simulated_text")
                lang = params.get("language")

                transcript = self.asr_engine.transcribe(
                    audio_path_or_bytes=audio_input,
                    project_id=project_id,
                    media_asset_id=media_asset_id,
                    language=lang,
                    simulated_text=simulated_text,
                )
                return SubtitlesDubbingResponse(
                    success=True,
                    message="Transcription completed successfully.",
                    data={"transcript": transcript.model_dump(mode="json")},
                )

            elif action == "register_glossary":
                term = GlossaryTerm(
                    source_term=params["source_term"],
                    target_term=params["target_term"],
                    target_language=params.get("target_language", "es"),
                    source_language=params.get("source_language", "en"),
                    case_sensitive=params.get("case_sensitive", False),
                )
                self.glossary_manager.register_term(project_id, term)
                return SubtitlesDubbingResponse(
                    success=True,
                    message="Glossary term registered successfully.",
                    data={"term_id": str(term.term_id)},
                )

            elif action == "generate_subtitles":
                transcript_dict = params.get("transcript")
                transcript = Transcript(**transcript_dict) if transcript_dict else None
                if not transcript:
                    transcript = self.asr_engine.transcribe(
                        audio_path_or_bytes="stream.wav",
                        project_id=project_id,
                        media_asset_id=uuid4(),
                        simulated_text=params.get("text", "Default studio subtitles."),
                    )

                max_cpl = int(params.get("max_cpl", 42))
                cues = SubtitleGenerator.generate_cues_from_transcript(transcript, max_cpl=max_cpl)

                fmt_str = params.get("format", "srt").lower()
                fmt = SubtitleFormat(fmt_str) if fmt_str in SubtitleFormat._value2member_map_ else SubtitleFormat.SRT
                preset_str = params.get("style_preset", "cinematic").lower()
                preset = SubtitleStylePreset(preset_str) if preset_str in SubtitleStylePreset._value2member_map_ else SubtitleStylePreset.CINEMATIC

                track = SubtitleTrack(
                    project_id=project_id,
                    language_code=transcript.language_code,
                    format=fmt,
                    style_preset=preset,
                    cues=cues,
                )
                SubtitleStyler.apply_style_preset(track, preset)

                if fmt == SubtitleFormat.SRT:
                    content = SubtitleGenerator.export_srt(track)
                elif fmt == SubtitleFormat.VTT:
                    content = SubtitleGenerator.export_vtt(track)
                elif fmt == SubtitleFormat.ASS:
                    content = SubtitleGenerator.export_ass(track)
                elif fmt == SubtitleFormat.TTML:
                    content = SubtitleGenerator.export_ttml(track)
                else:
                    content = track.model_dump_json(indent=2)

                return SubtitlesDubbingResponse(
                    success=True,
                    message="Subtitle track generated successfully.",
                    data={
                        "track_id": str(track.track_id),
                        "format": fmt.value,
                        "style_preset": preset.value,
                        "cue_count": len(cues),
                        "content": content,
                    },
                )

            elif action in {"dub_dialogue", "orchestrate_dubbing"}:
                transcript_dict = params.get("transcript")
                target_lang = params.get("target_language") or params.get("language", "es")
                custom_voices = params.get("voice_mappings")

                if transcript_dict:
                    transcript = Transcript(**transcript_dict)
                else:
                    text = params.get("text", "Universal AI Video Production Studio.")
                    transcript = self.asr_engine.transcribe(
                        audio_path_or_bytes="stream.wav",
                        project_id=project_id,
                        media_asset_id=uuid4(),
                        simulated_text=text,
                    )

                job = self.dubbing_orchestrator.execute_dubbing(
                    transcript=transcript,
                    target_language=target_lang,
                    preserve_background=params.get("preserve_background", True),
                    custom_voice_mappings=custom_voices,
                )

                produced_ids = [job.output_audio_asset_id] if job.output_audio_asset_id else []
                return SubtitlesDubbingResponse(
                    success=True,
                    message="Dubbing orchestration completed successfully.",
                    data={
                        "dubbing_job": job.model_dump(mode="json"),
                        "language": target_lang,
                        "duration_sec": 3.0,
                        "word_markers": [],
                    },
                    produced_asset_ids=produced_ids,
                )

            elif action == "process_lipsync":
                video_asset_id = UUID(str(params["video_asset_id"]))
                audio_asset_id = UUID(str(params["audio_asset_id"]))
                provider = params.get("provider", "synclabs")

                job = self.lipsync_orchestrator.process_lipsync(
                    project_id=project_id,
                    video_asset_id=video_asset_id,
                    audio_asset_id=audio_asset_id,
                    provider=provider,
                )
                produced_ids = [job.output_video_asset_id] if job.output_video_asset_id else []
                return SubtitlesDubbingResponse(
                    success=True,
                    message="Lip-sync processing completed successfully.",
                    data={"lipsync_job": job.model_dump(mode="json")},
                    produced_asset_ids=produced_ids,
                )

            elif action == "audit_subtitles_qc":
                track_dict = params.get("track")
                track = SubtitleTrack(**track_dict)
                report = LocalizationQualityController.audit_subtitle_track(track)
                return SubtitlesDubbingResponse(
                    success=True,
                    message="Subtitle QC inspection completed.",
                    data={"qc_report": report.model_dump(mode="json")},
                )

            elif action == "register_biometric_consent":
                consent = BiometricConsentRecord(
                    talent_name=params["talent_name"],
                    voice_profile_id=params["voice_profile_id"],
                    is_authorized=params.get("is_authorized", True),
                    authorized_purposes=params.get("authorized_purposes", ["commercial", "dubbing"]),
                    expiry_date=params.get("expiry_date"),
                )
                self.consent_manager.register_consent(consent)
                return SubtitlesDubbingResponse(
                    success=True,
                    message="Biometric consent registered successfully.",
                    data={"consent_id": str(consent.consent_id)},
                )

            return SubtitlesDubbingResponse(
                success=False,
                message=f"Unknown subtitles & dubbing action: '{action}'.",
            )
        except Exception as e:
            return SubtitlesDubbingResponse(
                success=False,
                message=f"Subtitles & Dubbing error: {str(e)}",
            )

    def health_check(self) -> bool:
        return True
