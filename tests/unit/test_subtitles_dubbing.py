"""
Unit tests for Department 17: Subtitles, Dubbing & Localization.
Verifies all 28 core acceptance criteria across ASR, translation, dialogue adaptation,
subtitle standards, voice casting, biometric consent, lip-sync licensing, clock sync, and QC.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from uuid import UUID, uuid4

from core.assets.database import AssetDatabase
import departments
from departments.subtitles_dubbing.adaptation.dialogue_adapter import DialogueAdapter
from departments.subtitles_dubbing.core.models import (
    BiometricConsentRecord,
    DubbingJob,
    GlossaryTerm,
    LipSyncJob,
    LocalizationQCReport,
    SpeakerRecord,
    SubtitleCue,
    SubtitleFormat,
    SubtitleStylePreset,
    SubtitleTrack,
    Transcript,
    TranscriptSegment,
    TranslationRecord,
    WordTimestamp,
)
from departments.subtitles_dubbing.dubbing.orchestrator import DubbingOrchestrator
from departments.subtitles_dubbing.integrations.asset_store_bridge import AssetStoreBridge
from departments.subtitles_dubbing.integrations.audio_production_bridge import AudioProductionBridge
from departments.subtitles_dubbing.integrations.director_localization_bridge import DirectorLocalizationBridge
from departments.subtitles_dubbing.integrations.timeline_subtitles_bridge import TimelineSubtitlesBridge
from departments.subtitles_dubbing.lipsync.lipsync_orchestrator import LipSyncOrchestrator
from departments.subtitles_dubbing.lipsync.local_lipsync_adapter import (
    LocalLipSyncAdapter,
    NonCommercialModelRejectedException,
)
from departments.subtitles_dubbing.qc.quality_controller import LocalizationQualityController
from departments.subtitles_dubbing.service import (
    ISubtitlesDubbing,
    SubtitlesDubbingRequest,
    SubtitlesDubbingResponse,
    SubtitlesDubbingService,
)
from departments.subtitles_dubbing.subtitles.generator import SubtitleGenerator
from departments.subtitles_dubbing.subtitles.styler import SubtitleStyler
from departments.subtitles_dubbing.sync.sync_manager import RationalTime, SyncManager
from departments.subtitles_dubbing.transcription.asr_engine import ASREngine
from departments.subtitles_dubbing.transcription.transcript_manager import TranscriptManager
from departments.subtitles_dubbing.translation.glossary import GlossaryManager
from departments.subtitles_dubbing.translation.translator import MultilingualTranslator
from departments.subtitles_dubbing.voice.consent_manager import (
    ConsentAuthorizationException,
    ConsentManager,
)
from departments.subtitles_dubbing.voice.voice_assigner import VoiceAssignmentManager


class TestSubtitlesDubbingStudio(unittest.TestCase):
    """Test suite covering Department 17 Subtitles, Dubbing & Localization."""

    @classmethod
    def setUpClass(cls):
        cls.project_id = uuid4()
        cls.media_asset_id = uuid4()
        cls.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db_path = cls.temp_db_file.name
        cls.temp_db_file.close()
        cls.db = AssetDatabase(db_path=cls.temp_db_path)
        cls.db.create_project(cls.project_id, "Localization Test Project")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_db_path):
            os.remove(cls.temp_db_path)

    # 1. Pydantic Domain Models
    def test_01_pydantic_domain_models(self):
        w = WordTimestamp(word="Studio", start_time=0.0, end_time=0.45, confidence=0.99)
        self.assertEqual(w.word, "Studio")
        seg = TranscriptSegment(
            start_time=0.0, end_time=1.5, text="Studio intro.", words=[w], speaker_id="speaker_0"
        )
        t = Transcript(
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            language_code="en",
            segments=[seg],
        )
        self.assertEqual(len(t.segments), 1)
        self.assertEqual(t.segments[0].words[0].word, "Studio")

    # 2. ASR Engine Word Timestamps
    def test_02_asr_engine_word_timestamps(self):
        asr = ASREngine()
        text = "Universal AI Video Production Studio localization engine initializing."
        transcript = asr.transcribe(
            audio_path_or_bytes="mock.wav",
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            simulated_text=text,
        )
        self.assertEqual(transcript.language_code, "en")
        self.assertTrue(len(transcript.segments) > 0)
        first_seg = transcript.segments[0]
        self.assertTrue(len(first_seg.words) > 0)
        self.assertTrue(first_seg.words[0].end_time > first_seg.words[0].start_time)

    # 3. Language Detection and Indic Support
    def test_03_language_detection_and_indic_support(self):
        asr = ASREngine()
        self.assertEqual(asr.detect_language(None, "Bonjour tout le monde"), "fr")
        self.assertEqual(asr.detect_language(None, "¿Cómo estás hoy?"), "es")
        self.assertEqual(asr.detect_language(None, "नमस्ते, स्टूडियो में आपका स्वागत है"), "hi")
        self.assertEqual(asr.detect_language(None, "வணக்கம், எப்படி இருக்கிறீர்கள்"), "ta")
        self.assertEqual(asr.detect_language(None, "నమస్కారం, ఎలా ఉన్నారు"), "te")

    # 4. Hinglish Code-Switching Detection
    def test_04_hinglish_code_switching_detection(self):
        asr = ASREngine()
        text = "Aap humko call karo jab free ho, yeh accha idea hai"
        detected = asr.detect_language(None, text)
        self.assertEqual(detected, "hi")

    # 5. Transcript Manager Manual Edit
    def test_05_transcript_manager_manual_edit(self):
        asr = ASREngine()
        transcript = asr.transcribe(
            audio_path_or_bytes="mock.wav",
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            simulated_text="Raw uncorrected text from ASR model.",
        )
        seg_id = transcript.segments[0].segment_id
        success = TranscriptManager.edit_segment(transcript, seg_id, "Polished professional text.")
        self.assertTrue(success)
        self.assertEqual(transcript.segments[0].text, "Polished professional text.")
        self.assertEqual(transcript.segments[0].original_text, "Raw uncorrected text from ASR model.")
        self.assertTrue(transcript.segments[0].is_manual_edit)

    # 6. Transcript Manager Split and Merge
    def test_06_transcript_manager_split_and_merge(self):
        asr = ASREngine()
        transcript = asr.transcribe(
            audio_path_or_bytes="mock.wav",
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            simulated_text="One two three four five six seven eight nine ten.",
        )
        seg = transcript.segments[0]
        split_res = TranscriptManager.split_segment(transcript, seg.segment_id, split_at_word_index=4)
        self.assertIsNotNone(split_res)
        seg_a, seg_b = split_res
        self.assertEqual(len(seg_a.words), 4)

        # Merge them back
        merged = TranscriptManager.merge_segments(transcript, seg_a.segment_id, seg_b.segment_id)
        self.assertIsNotNone(merged)
        self.assertEqual(len(merged.words), len(seg.words))

    # 7. Transcript Manager Search
    def test_07_transcript_manager_search(self):
        asr = ASREngine()
        transcript = asr.transcribe(
            audio_path_or_bytes="mock.wav",
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            simulated_text="The cinematography in this scene is remarkable and breathtaking.",
        )
        results = TranscriptManager.search_transcript(transcript, "cinematography")
        self.assertEqual(len(results), 1)
        full_text = TranscriptManager.get_full_text(transcript)
        self.assertIn("cinematography", full_text)

    # 8. Glossary Term Registration and Masking
    def test_08_glossary_term_registration_and_masking(self):
        gm = GlossaryManager()
        term = GlossaryTerm(
            source_term="OpenUSD",
            target_term="OpenUSD",
            target_language="hi",
        )
        gm.register_term(self.project_id, term)
        terms = gm.get_terms(self.project_id, "hi")
        self.assertEqual(len(terms), 1)

        masked, token_map = gm.mask_terms_in_source("Export the scene to OpenUSD format", self.project_id, "hi")
        self.assertIn("__GLOSSARY_TOKEN_0__", masked)
        unmasked = gm.unmask_terms(masked, token_map)
        self.assertIn("OpenUSD", unmasked)

    # 9. Multilingual Translation with Glossary
    def test_09_multilingual_translation_with_glossary(self):
        gm = GlossaryManager()
        gm.register_term(
            self.project_id,
            GlossaryTerm(source_term="Quantum Engine", target_term="क्वांटम इंजन", target_language="hi"),
        )
        translator = MultilingualTranslator(glossary_manager=gm)
        seg = TranscriptSegment(
            start_time=0.0,
            end_time=2.0,
            text="Welcome to the studio Quantum Engine",
        )
        rec = translator.translate_segment(seg, self.project_id, target_language="hi")
        self.assertIn("क्वांटम इंजन", rec.translated_text)
        self.assertIn("क्वांटम इंजन", rec.glossary_terms_preserved)

    # 10. Dialogue Adapter Syllable Estimation
    def test_10_dialogue_adapter_syllable_estimation(self):
        syl_en = DialogueAdapter.estimate_syllables("Universal studio", "en")
        self.assertTrue(syl_en >= 4)
        syl_hi = DialogueAdapter.estimate_syllables("नमस्ते दोस्तों", "hi")
        self.assertTrue(syl_hi >= 3)
        est_sec = DialogueAdapter.calculate_estimated_duration("Quick scene", "en")
        self.assertTrue(est_sec > 0.1)

    # 11. Dialogue Adapter Timing and Tempo Bounds
    def test_11_dialogue_adapter_timing_and_tempo_bounds(self):
        # Long dialogue adapted into short slot
        adapted_text, tempo = DialogueAdapter.adapt_dialogue(
            translated_text="actually you know this is basically a long phrase",
            target_duration_sec=1.5,
            target_language="en",
        )
        self.assertTrue(DialogueAdapter.MIN_TEMPO <= tempo <= DialogueAdapter.MAX_TEMPO)

    # 12. Subtitle Cue Generation and CPL Wrapping
    def test_12_subtitle_cue_generation_and_cpl_wrapping(self):
        asr = ASREngine()
        text = "This is a very long explanatory sentence designed to rigorously test characters per line text wrapping across multiple subtitle lines."
        transcript = asr.transcribe(
            audio_path_or_bytes="mock.wav",
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            simulated_text=text,
        )
        cues = SubtitleGenerator.generate_cues_from_transcript(transcript, max_cpl=35)
        self.assertTrue(len(cues) > 0)
        for c in cues:
            lines = c.text.split("\n")
            self.assertTrue(len(lines) <= 2)
            for line in lines:
                self.assertTrue(len(line) <= 35)

    # 13. Subtitle Min/Max Duration and Frame Gap
    def test_13_subtitle_min_max_duration_and_frame_gap(self):
        asr = ASREngine()
        transcript = asr.transcribe(
            audio_path_or_bytes="mock.wav",
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            simulated_text="Word. Next.",
        )
        cues = SubtitleGenerator.generate_cues_from_transcript(transcript)
        for c in cues:
            dur = c.end_time - c.start_time
            self.assertTrue(dur >= SubtitleGenerator.MIN_DURATION_SEC)
            self.assertTrue(dur <= SubtitleGenerator.MAX_DURATION_SEC)

    # 14. Export SRT Format
    def test_14_export_srt_format(self):
        track = SubtitleTrack(
            project_id=self.project_id,
            language_code="en",
            format=SubtitleFormat.SRT,
            cues=[
                SubtitleCue(cue_index=1, start_time=1.0, end_time=3.5, text="Hello Studio"),
                SubtitleCue(cue_index=2, start_time=4.0, end_time=6.2, text="Second line"),
            ],
        )
        srt_content = SubtitleGenerator.export_srt(track)
        self.assertIn("1\n00:00:01,000 --> 00:00:03,500\nHello Studio", srt_content)
        self.assertIn("2\n00:00:04,000 --> 00:00:06,200\nSecond line", srt_content)

    # 15. Export VTT Format
    def test_15_export_vtt_format(self):
        track = SubtitleTrack(
            project_id=self.project_id,
            language_code="es",
            format=SubtitleFormat.VTT,
            cues=[
                SubtitleCue(cue_index=1, start_time=0.5, end_time=2.8, text="Hola mundo", speaker_id="speaker_0"),
            ],
        )
        vtt_content = SubtitleGenerator.export_vtt(track)
        self.assertTrue(vtt_content.startswith("WEBVTT"))
        self.assertIn("00:00:00.500 --> 00:00:02.800", vtt_content)
        self.assertIn("<v speaker_0>Hola mundo", vtt_content)

    # 16. Export ASS Format
    def test_16_export_ass_format(self):
        track = SubtitleTrack(
            project_id=self.project_id,
            language_code="ja",
            format=SubtitleFormat.ASS,
            cues=[
                SubtitleCue(cue_index=1, start_time=0.0, end_time=2.0, text="こんにちは\n世界"),
            ],
        )
        ass_content = SubtitleGenerator.export_ass(track)
        self.assertIn("[Script Info]", ass_content)
        self.assertIn("[V4+ Styles]", ass_content)
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,こんにちは\\N世界", ass_content)

    # 17. Export TTML Format
    def test_17_export_ttml_format(self):
        track = SubtitleTrack(
            project_id=self.project_id,
            language_code="en",
            format=SubtitleFormat.TTML,
            cues=[
                SubtitleCue(cue_index=1, start_time=1.0, end_time=3.0, text="Standard broadcast caption"),
            ],
        )
        ttml_content = SubtitleGenerator.export_ttml(track)
        self.assertTrue(ttml_content.startswith('<?xml version="1.0" encoding="utf-8"?>'))
        self.assertIn('<tt xmlns="http://www.w3.org/ns/ttml"', ttml_content)
        self.assertIn('begin="00:00:01.000" end="00:00:03.000"', ttml_content)

    # 18. Subtitle Styling Presets
    def test_18_subtitle_styling_presets(self):
        track = SubtitleTrack(
            project_id=self.project_id,
            cues=[SubtitleCue(cue_index=1, start_time=0.0, end_time=2.0, text="Viral reel highlight")],
        )
        SubtitleStyler.apply_style_preset(track, SubtitleStylePreset.SOCIAL_KINETIC)
        self.assertEqual(track.style_preset, SubtitleStylePreset.SOCIAL_KINETIC)
        self.assertEqual(track.cues[0].text, "VIRAL REEL HIGHLIGHT")
        self.assertEqual(track.cues[0].style_override["font"], "Montserrat-Bold")

    # 19. Karaoke ASS Highlight Cue
    def test_19_karaoke_ass_highlight_cue(self):
        words = [
            WordTimestamp(word="Fast", start_time=0.0, end_time=0.3),
            WordTimestamp(word="Paced", start_time=0.3, end_time=0.7),
        ]
        karaoke = SubtitleStyler.generate_karaoke_ass_cue(words)
        self.assertIn(r"{\k30}Fast", karaoke)
        self.assertIn(r"{\k40}Paced", karaoke)

    # 20. Voice Assignment and Casting
    def test_20_voice_assignment_and_casting(self):
        cm = ConsentManager()
        cm.register_consent(BiometricConsentRecord(talent_name="Mateo", voice_profile_id="elevenlabs_mateo"))
        cm.register_consent(BiometricConsentRecord(talent_name="Sofia", voice_profile_id="elevenlabs_sofia"))

        t = Transcript(
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            speakers=[
                SpeakerRecord(speaker_id="speaker_0", gender="male"),
                SpeakerRecord(speaker_id="speaker_1", gender="female"),
            ],
        )
        va = VoiceAssignmentManager(consent_manager=cm)
        mappings = va.assign_voices(t, target_language="es")
        self.assertEqual(mappings["speaker_0"], "elevenlabs_mateo")
        self.assertEqual(mappings["speaker_1"], "elevenlabs_sofia")

    # 21. Biometric Consent Enforcement
    def test_21_biometric_consent_enforcement(self):
        cm = ConsentManager()
        # Not registered
        with self.assertRaises(ConsentAuthorizationException):
            cm.verify_authorization("unauthorized_voice_clone")

        # Registered but revoked
        cm.register_consent(
            BiometricConsentRecord(talent_name="Actor", voice_profile_id="revoked_voice", is_authorized=False)
        )
        with self.assertRaises(ConsentAuthorizationException):
            cm.verify_authorization("revoked_voice")

        # Registered and valid
        cm.register_consent(
            BiometricConsentRecord(talent_name="Actor", voice_profile_id="valid_voice", is_authorized=True)
        )
        self.assertTrue(cm.verify_authorization("valid_voice"))

    # 22. Dubbing Orchestration Workflow
    def test_22_dubbing_orchestration_workflow(self):
        cm = ConsentManager()
        cm.register_consent(BiometricConsentRecord(talent_name="Aarav", voice_profile_id="elevenlabs_aarav"))
        cm.register_consent(BiometricConsentRecord(talent_name="Ananya", voice_profile_id="elevenlabs_ananya"))
        va = VoiceAssignmentManager(consent_manager=cm)
        orchestrator = DubbingOrchestrator(voice_assigner=va)

        asr = ASREngine()
        transcript = asr.transcribe(
            audio_path_or_bytes="mock.wav",
            project_id=self.project_id,
            media_asset_id=self.media_asset_id,
            simulated_text="Welcome to the studio production plan.",
        )
        dubbing_job = orchestrator.execute_dubbing(transcript, target_language="hi")
        self.assertEqual(dubbing_job.status, "completed")
        self.assertIsNotNone(dubbing_job.output_audio_asset_id)
        self.assertEqual(dubbing_job.target_language, "hi")

    # 23. Lip-Sync Orchestration (Sync Labs)
    def test_23_lipsync_orchestration_sync_labs(self):
        orchestrator = LipSyncOrchestrator()
        v_id = uuid4()
        a_id = uuid4()
        job = orchestrator.process_lipsync(self.project_id, v_id, a_id, provider="synclabs")
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.provider, "synclabs")
        self.assertIsNotNone(job.output_video_asset_id)

    # 24. Lip-Sync License Firewall Rejects Wav2Lip
    def test_24_lipsync_license_firewall_rejects_wav2lip(self):
        orchestrator = LipSyncOrchestrator()
        with self.assertRaises(NonCommercialModelRejectedException):
            orchestrator.process_lipsync(self.project_id, uuid4(), uuid4(), provider="wav2lip")

    # 25. Audio-Video Clock Drift Detection
    def test_25_audio_video_clock_drift_detection(self):
        # 48000 samples = 1.0 sec audio
        # 24 frames @ 24fps = 1.0 sec video -> 0ms drift
        drift_0 = SyncManager.calculate_clock_drift_ms(48000, 24, video_fps=24.0, audio_rate=48000)
        self.assertAlmostEqual(drift_0, 0.0)

        # 48240 samples = 1.005 sec audio -> 5ms drift
        drift_5 = SyncManager.calculate_clock_drift_ms(48240, 24, video_fps=24.0, audio_rate=48000)
        self.assertAlmostEqual(drift_5, 5.0, places=2)

        # RationalTime
        rt = RationalTime(24, 24)
        self.assertEqual(rt.to_seconds(), 1.0)
        self.assertEqual(rt.to_timecode(), "00:00:01:00")

    # 26. Shot Boundary Snapping
    def test_26_shot_boundary_snapping(self):
        cuts = [0.0, 4.0, 8.5]
        # Cue at 3.95s is within 0.125s of 4.0s cut -> snap to 4.0
        snapped = SyncManager.snap_cue_to_shot_boundary(3.95, cuts, tolerance_sec=0.125)
        self.assertEqual(snapped, 4.0)

        # Cue at 3.5s is not within tolerance -> remains 3.5
        unsnapped = SyncManager.snap_cue_to_shot_boundary(3.5, cuts, tolerance_sec=0.125)
        self.assertEqual(unsnapped, 3.5)

    # 27. Quality Control Audits
    def test_27_quality_control_audits(self):
        # Track with a reading speed violation (> 17 CPS)
        track = SubtitleTrack(
            project_id=self.project_id,
            cues=[
                SubtitleCue(
                    cue_index=1,
                    start_time=1.0,
                    end_time=1.5,  # 0.5 sec
                    text="This sentence has way too many characters for half a second duration",
                )
            ],
        )
        report = LocalizationQualityController.audit_subtitle_track(track)
        self.assertFalse(report.passed)
        self.assertTrue(report.reading_speed_violations > 0)

        # Audio loudness audit
        loud_report = LocalizationQualityController.audit_audio_loudness(
            self.project_id, measured_lufs=-23.0, true_peak_db=-1.5
        )
        self.assertTrue(loud_report.passed)

        bad_loud_report = LocalizationQualityController.audit_audio_loudness(
            self.project_id, measured_lufs=-18.0, true_peak_db=0.5
        )
        self.assertFalse(bad_loud_report.passed)

    # 28. Database Persistence and Bridges
    def test_28_database_persistence_and_bridges(self):
        # Database CRUD
        job_id = str(uuid4())
        self.db.save_localization_job(
            job_id=job_id,
            project_id=str(self.project_id),
            job_type="dubbing",
            target_language="es",
            status="completed",
        )
        job_rec = self.db.get_localization_job(job_id)
        self.assertIsNotNone(job_rec)
        self.assertEqual(job_rec["target_language"], "es")

        # Consent CRUD
        c_id = str(uuid4())
        self.db.save_biometric_consent(
            consent_id=c_id,
            talent_name="Maria Gomez",
            voice_profile_id="maria_es_01",
            is_authorized=True,
        )
        c_rec = self.db.get_biometric_consent("maria_es_01")
        self.assertIsNotNone(c_rec)
        self.assertEqual(c_rec["talent_name"], "Maria Gomez")

        # Subtitle Track CRUD
        track_id = str(uuid4())
        self.db.save_subtitle_track(
            track_id=track_id,
            project_id=str(self.project_id),
            language_code="es",
            format="srt",
            style_preset="cinematic",
            cues=[{"cue_index": 1, "text": "Hola"}],
        )
        sub_rec = self.db.get_subtitle_track(track_id)
        self.assertIsNotNone(sub_rec)
        self.assertEqual(sub_rec["language_code"], "es")

        # Bridges
        track = SubtitleTrack(
            project_id=self.project_id,
            cues=[SubtitleCue(cue_index=1, start_time=0.0, end_time=2.0, text="Bridge test")],
        )
        otio_track = TimelineSubtitlesBridge.track_to_otio_dict(track)
        self.assertEqual(otio_track["schema"], "Track")
        self.assertEqual(len(otio_track["children"]), 1)

        stems = AudioProductionBridge.separate_dialogue_stem("mix.wav")
        self.assertIn("dialogue_stem", stems)

        context = DirectorLocalizationBridge.get_narrative_context(self.project_id)
        self.assertIn("genre", context)

        store_bridge = AssetStoreBridge(self.db)
        asset_uuid = store_bridge.register_localized_asset(
            self.project_id, self.media_asset_id, "subtitle_srt", "en", "subtitles.srt"
        )
        self.assertIsInstance(asset_uuid, UUID)


if __name__ == "__main__":
    unittest.main()
