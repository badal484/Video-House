"""
Comprehensive Unit Test Suite for Department 14: Audio Production & Sound Design Studio
Validates all 20 architectural checkpoints, DSP pipelines, multitrack mixing,
dialogue cleanup, procedural Foley, stem separation, loudness standards, and asset persistence.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
import uuid
import numpy as np
import scipy.io.wavfile

from core.assets.database import AssetDatabase
from core.timeline.time_model import RationalTime
import departments
from departments.audio_production.core.session_models import (
    AudioSession,
    AudioTrack,
    AudioClip,
    AudioTrackType,
    ChannelLayout,
    FadeCurve,
    LoudnessStandard,
    AutomationPoint,
    AutomationLane,
    AudioEffectConfig,
)
from departments.audio_production.dsp.equalizer import EqualizerEngine
from departments.audio_production.dsp.dynamics import DynamicsEngine
from departments.audio_production.dsp.effects import EffectsEngine
from departments.audio_production.dsp.time_pitch import TimePitchEngine
from departments.audio_production.dsp.loudness import LoudnessMeter
from departments.audio_production.dialogue.dialogue_cleaner import DialogueCleaner
from departments.audio_production.dialogue.de_esser import DeEsser
from departments.audio_production.dialogue.room_tone import RoomToneGenerator
from departments.audio_production.sound_design.sound_library import SoundLibrary, SFXAssetMetadata
from departments.audio_production.sound_design.procedural_sfx import ProceduralSFXEngine
from departments.audio_production.sound_design.music_engine import MusicEngine
from departments.audio_production.separation.source_separator import SourceSeparator
from departments.audio_production.voice.voice_producer import (
    VoiceProducer,
    VoiceConsentRecord,
    SpeechSynthesisRequest,
)
from departments.audio_production.mixing.multitrack_mixer import MultitrackMixer
from departments.audio_production.mixing.mastering_engine import MasteringEngine
from departments.audio_production.integrations.timeline_bridge import TimelineAudioBridge
from departments.audio_production.integrations.director_bridge import DirectorAudioBridge
from departments.audio_production.service import AudioProductionService
from departments.subtitles_dubbing.service import SubtitlesDubbingService


class TestAudioProductionStudio(unittest.TestCase):
    """Test suite for Department 14 Audio Production & Department 17 Subtitles/Dubbing."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="audio_studio_test_")
        cls.artifact_dir = "test_artifacts/audio"
        os.makedirs(cls.artifact_dir, exist_ok=True)
        
        # Dedicated SQLite DB for audio tests
        cls.db_path = os.path.join(cls.test_dir, "test_audio.db")
        cls.db = AssetDatabase(cls.db_path)
        cls.db.create_project("test_proj_audio", "Audio Test Project")

        # Synthesize a clean 1.0s 48kHz test speech-like tone WAV
        cls.sample_rate = 48000
        t = np.linspace(0.0, 1.0, cls.sample_rate, endpoint=False)
        cls.test_audio_wav = os.path.join(cls.test_dir, "test_speech.wav")
        # Dual tone 220Hz + 440Hz
        tone = (0.3 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        stereo_tone = np.vstack([tone, tone])
        MasteringEngine.export_wav(stereo_tone, cls.sample_rate, cls.test_audio_wav)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_session_models_and_routing(self):
        """1. Multitrack session creation and track routing."""
        session = AudioSession(project_id="test_proj_audio", name="Cinematic Session")
        diag_trk = session.add_track("Dialogue A1", AudioTrackType.DIALOGUE, gain_db=0.0)
        music_trk = session.add_track("Music Bed A2", AudioTrackType.MUSIC, gain_db=-6.0)
        sfx_trk = session.add_track("SFX A3", AudioTrackType.SOUND_EFFECTS, gain_db=-3.0)

        self.assertEqual(len(session.tracks), 3)
        self.assertEqual(diag_trk.track_type, AudioTrackType.DIALOGUE)
        self.assertEqual(session.get_track(music_trk.track_id), music_trk)
        self.assertEqual(session.channel_layout, ChannelLayout.STEREO)

    def test_02_non_destructive_clip_editing(self):
        """2. Non-destructive clip trimming and splitting."""
        session = AudioSession(project_id="test_proj_audio")
        trk = session.add_track("Dialogue", AudioTrackType.DIALOGUE)
        clip = AudioClip(
            track_id=trk.track_id,
            name="Actor Take 1",
            start_time_sec=1.0,
            duration_sec=4.0,
            source_in_sec=0.5,
        )
        trk.add_clip(clip)
        self.assertEqual(trk.clips[0].end_time_sec, 5.0)

        # Split at 2.5s (1.5s into clip)
        split_clips = trk.split_clip(clip.clip_id, split_time_sec=2.5)
        self.assertIsNotNone(split_clips)
        self.assertEqual(len(split_clips), 2)
        clip_a, clip_b = split_clips
        self.assertAlmostEqual(clip_a.duration_sec, 1.5)
        self.assertAlmostEqual(clip_b.start_time_sec, 2.5)
        self.assertAlmostEqual(clip_b.duration_sec, 2.5)
        self.assertAlmostEqual(clip_b.source_in_sec, 2.0)
        self.assertEqual(len(trk.clips), 2)

    def test_03_parametric_equalizer(self):
        """3. Parametric EQ high-pass, low-pass, peaking, and notch filtering."""
        sr = 48000
        t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
        # Low rumble (30Hz) + Mid tone (1000Hz) + High hiss (18000Hz)
        sig = (np.sin(2 * np.pi * 30 * t) + np.sin(2 * np.pi * 1000 * t) + np.sin(2 * np.pi * 18000 * t)).astype(np.float32)
        
        # Highpass 80Hz should attenuate 30Hz rumble
        hpf = EqualizerEngine.apply_highpass(sig, sr, cutoff_hz=80.0)
        self.assertLess(np.max(np.abs(hpf[:sr // 4])), np.max(np.abs(sig[:sr // 4])))

        # Lowpass 15kHz should attenuate 18kHz hiss
        lpf = EqualizerEngine.apply_lowpass(sig, sr, cutoff_hz=15000.0)
        self.assertEqual(lpf.shape, sig.shape)

        # Peaking boost at 1kHz
        peaked = EqualizerEngine.apply_peak(sig, sr, center_hz=1000.0, gain_db=6.0, q=1.5)
        self.assertGreater(np.max(np.abs(peaked)), np.max(np.abs(sig)) * 0.9)

        # 50Hz mains hum notch
        hum_sig = (sig + 0.8 * np.sin(2 * np.pi * 50 * t)).astype(np.float32)
        notched = EqualizerEngine.apply_notch(hum_sig, sr, notch_hz=50.0, q=30.0)
        self.assertLess(np.std(notched), np.std(hum_sig))

    def test_04_dynamic_compressor_and_limiter(self):
        """4. Compressor and peak limiter ceiling enforcement."""
        sr = 48000
        t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
        # Hot audio peaking up to +3.0 linear (~9.5 dBFS)
        hot_audio = (2.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

        # Compressor
        compressed = DynamicsEngine.apply_compressor(hot_audio, sr, threshold_db=-12.0, ratio=4.0)
        self.assertLess(np.max(np.abs(compressed)), np.max(np.abs(hot_audio)))

        # Limiter with ceiling at -1.0 dBFS (approx 0.891 linear)
        limited = DynamicsEngine.apply_limiter(hot_audio, sr, threshold_db=-1.0)
        max_peak = np.max(np.abs(limited))
        self.assertLessEqual(max_peak, 0.895)

    def test_05_reverb_and_delay_effects(self):
        """5. Algorithmic reverb and delay line generation."""
        sr = 48000
        impulse = np.zeros(sr // 2, dtype=np.float32)
        impulse[0] = 1.0  # single delta impulse

        # Reverb creates decaying tail
        rev = EffectsEngine.apply_reverb(impulse, sr, room_size=0.7, wet_level=0.5, dry_level=0.5)
        # Check energy exists well after the initial impulse
        tail_energy = np.sum(rev[int(sr * 0.05):] ** 2)
        self.assertGreater(tail_energy, 1e-4)

        # Delay
        delay = EffectsEngine.apply_delay(impulse, sr, delay_seconds=0.1, feedback=0.4, mix=0.5)
        # Delayed echo should appear around sample 4800 (0.1s * 48000)
        delayed_peak_sample = np.argmax(delay[100:]) + 100
        self.assertAlmostEqual(delayed_peak_sample / sr, 0.1, delta=0.02)

    def test_06_time_pitch_manipulation(self):
        """6. Pitch shifting and sample rate conversion."""
        sr = 48000
        t = np.linspace(0.0, 0.25, int(sr * 0.25), endpoint=False)
        sig = np.sin(2 * np.pi * 440 * t).astype(np.float32)

        # Pitch shift up 7 semitones (perfect fifth)
        shifted = TimePitchEngine.apply_pitch_shift(sig, sr, semitones=7.0)
        self.assertEqual(len(shifted), len(sig))

        # Resample 44100 to 48000
        orig_44k = np.zeros(44100, dtype=np.float32)
        resampled_48k = TimePitchEngine.resample_audio(orig_44k, 44100, 48000)
        self.assertEqual(len(resampled_48k), 48000)

    def test_07_itu_loudness_measurement_and_normalization(self):
        """7. ITU-R BS.1770-4 / EBU R128 loudness measurement and normalization."""
        sr = 48000
        t = np.linspace(0.0, 1.0, sr, endpoint=False)
        sig = (0.1 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
        stereo = np.vstack([sig, sig])

        # Measure
        measured = LoudnessMeter.measure_loudness(stereo, sr)
        self.assertIn("integrated_lufs", measured)
        self.assertIn("true_peak_db", measured)

        # Normalize to YouTube standard (-14.0 LUFS)
        norm_yt, m_yt = LoudnessMeter.normalize_loudness(stereo, sr, standard=LoudnessStandard.YOUTUBE)
        self.assertAlmostEqual(m_yt["integrated_lufs"], -14.0, delta=1.5)
        self.assertLessEqual(m_yt["true_peak_db"], -1.0)

        # Normalize to EBU R128 standard (-23.0 LUFS)
        norm_ebu, m_ebu = LoudnessMeter.normalize_loudness(stereo, sr, standard=LoudnessStandard.EBU_R128)
        self.assertAlmostEqual(m_ebu["integrated_lufs"], -23.0, delta=1.5)
        self.assertLessEqual(m_ebu["true_peak_db"], -1.0)

    def test_08_dialogue_cleaning_and_restoration(self):
        """8. Dialogue cleanup with mains hum removal, rumble filter, and spectral subtraction."""
        sr = 48000
        t = np.linspace(0.0, 1.0, sr, endpoint=False)
        speech = (0.4 * np.sin(2 * np.pi * 350 * t)).astype(np.float32)
        noise = (0.08 * np.random.randn(sr)).astype(np.float32)
        hum = (0.15 * np.sin(2 * np.pi * 50 * t)).astype(np.float32)
        rumble = (0.2 * np.sin(2 * np.pi * 25 * t)).astype(np.float32)
        dirty_dialogue = speech + noise + hum + rumble

        cleaned = DialogueCleaner.clean_dialogue(
            dirty_dialogue, sr, mains_freq=50.0, remove_hum=True, remove_rumble=True, denoise=True
        )
        self.assertEqual(cleaned.shape, dirty_dialogue.shape)
        # Verify noise attenuation
        self.assertLess(np.max(np.abs(cleaned - speech)), np.max(np.abs(dirty_dialogue - speech)))

    def test_09_vocal_de_esser(self):
        """9. Sibilance detection and split-band de-essing."""
        sr = 48000
        t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
        vowel = (0.3 * np.sin(2 * np.pi * 400 * t)).astype(np.float32)
        sibilant_s = (0.6 * np.sin(2 * np.pi * 6500 * t)).astype(np.float32)
        vocal = vowel + sibilant_s

        de_essed = DeEsser.apply_de_esser(vocal, sr, sibilance_band=(4500, 8500), threshold_db=-18.0)
        self.assertEqual(de_essed.shape, vocal.shape)
        self.assertLess(np.max(np.abs(de_essed)), np.max(np.abs(vocal)))

    def test_10_room_tone_extraction_and_looping(self):
        """10. Room tone extraction from pause intervals and equal-power continuous looping."""
        sr = 48000
        t = np.linspace(0.0, 2.0, sr * 2, endpoint=False)
        # Dialogue with a quiet pause interval in the middle
        sig = np.sin(2 * np.pi * 300 * t).astype(np.float32)
        sig[sr // 2:sr] = np.random.randn(sr // 2).astype(np.float32) * 0.01  # quiet room tone

        extracted = RoomToneGenerator.extract_quietest_segment(sig, sr, segment_len_sec=0.4)
        self.assertEqual(len(extracted), int(sr * 0.4))
        self.assertLess(np.std(extracted), 0.05)

        # Loop room tone to 3.0s
        continuous = RoomToneGenerator.loop_room_tone(extracted, target_duration_sec=3.0, sample_rate=sr)
        self.assertEqual(len(continuous), sr * 3)

    def test_11_procedural_cinematic_sfx_synthesis(self):
        """11. Procedural Foley and SFX synthesis (impact, whoosh, riser, drone)."""
        sr = 48000
        # Impact
        impact = ProceduralSFXEngine.generate_cinematic_impact(duration_sec=1.5, sample_rate=sr)
        self.assertEqual(impact.shape, (2, int(sr * 1.5)))
        self.assertGreater(np.max(np.abs(impact)), 0.1)

        # Whoosh
        whoosh = ProceduralSFXEngine.generate_whoosh_transition(duration_sec=1.0, sample_rate=sr)
        self.assertEqual(whoosh.shape, (2, sr))

        # Tension riser
        riser = ProceduralSFXEngine.generate_tension_riser(duration_sec=2.0, sample_rate=sr)
        self.assertEqual(riser.shape, (2, sr * 2))

        # Ambient drone
        drone = ProceduralSFXEngine.generate_ambient_drone(duration_sec=2.0, sample_rate=sr)
        self.assertEqual(drone.shape, (2, sr * 2))

        # Save artifacts to test_artifacts/audio/
        MasteringEngine.export_wav(impact, sr, os.path.join(self.artifact_dir, "procedural_impact.wav"))
        MasteringEngine.export_wav(whoosh, sr, os.path.join(self.artifact_dir, "procedural_whoosh.wav"))
        MasteringEngine.export_wav(riser, sr, os.path.join(self.artifact_dir, "procedural_riser.wav"))
        MasteringEngine.export_wav(drone, sr, os.path.join(self.artifact_dir, "procedural_drone.wav"))

    def test_12_beat_grid_and_tempo_detection(self):
        """12. Beat grid alignment and tempo estimation."""
        sr = 48000
        duration_sec = 3.0
        # Synthesize 120 BPM click track (2 beats per second, 0.5s interval)
        click_track = np.zeros(int(sr * duration_sec), dtype=np.float32)
        beat_interval = int(sr * 0.5)
        for b in range(0, len(click_track), beat_interval):
            click_track[b:min(b + 500, len(click_track))] = 1.0

        grid = MusicEngine.detect_tempo_and_beat_grid(click_track, sr)
        self.assertIn("bpm", grid)
        self.assertAlmostEqual(grid["bpm"], 120.0, delta=10.0)
        self.assertTrue(len(grid["beat_times_sec"]) >= 5)

    def test_13_dialogue_sidechain_ducking(self):
        """13. Dynamic dialogue ducking on background music."""
        sr = 48000
        duration = 2.0
        t = np.linspace(0.0, duration, int(sr * duration), endpoint=False)
        music = (0.5 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
        dialogue = np.zeros_like(music)
        # Dialogue active between 0.5s and 1.5s
        dialogue[int(sr * 0.5):int(sr * 1.5)] = 0.4 * np.sin(2 * np.pi * 500 * t[int(sr * 0.5):int(sr * 1.5)])

        ducked_music = MusicEngine.apply_sidechain_ducking(
            music_audio=music,
            dialogue_audio=dialogue,
            sample_rate=sr,
            threshold_db=-24.0,
            duck_depth_db=-14.0,
        )
        # Music during speech (at 1.0s) should be attenuated significantly compared to silence (at 0.2s)
        un_ducked_rms = np.std(ducked_music[:int(sr * 0.3)])
        ducked_rms = np.std(ducked_music[int(sr * 0.7):int(sr * 1.3)])
        self.assertLess(ducked_rms, un_ducked_rms * 0.4)

    def test_14_audio_source_separation_4_stems(self):
        """14. 4-stem source separation (vocals, drums, bass, other)."""
        sr = 48000
        t = np.linspace(0.0, 1.0, sr, endpoint=False)
        # Composite mix: bass (80Hz) + vocals (800Hz) + percussive click burst
        bass = (0.4 * np.sin(2 * np.pi * 80 * t)).astype(np.float32)
        vocal = (0.3 * np.sin(2 * np.pi * 800 * t)).astype(np.float32)
        drums = np.zeros(sr, dtype=np.float32)
        drums[::sr // 4] = 1.0  # rhythmic transients
        composite = bass + vocal + drums

        stems = SourceSeparator.separate(composite, sr)
        self.assertIn("vocals", stems)
        self.assertIn("drums", stems)
        self.assertIn("bass", stems)
        self.assertIn("other", stems)
        self.assertEqual(stems["vocals"].shape[-1], sr)
        self.assertEqual(stems["bass"].shape[-1], sr)

    def test_15_multitrack_mixer_and_equal_power_crossfades(self):
        """15. Multitrack mixdown, automation, and equal-power crossfades."""
        session = AudioSession(project_id="test_proj_audio", name="Mixdown Test")
        trk1 = session.add_track("Lead Dialogue", AudioTrackType.DIALOGUE)
        clip1 = AudioClip(
            track_id=trk1.track_id,
            file_path=self.test_audio_wav,
            start_time_sec=0.0,
            duration_sec=1.0,
            fade_in_sec=0.1,
            fade_out_sec=0.1,
        )
        trk1.add_clip(clip1)

        trk2 = session.add_track("Score Music", AudioTrackType.MUSIC, gain_db=-3.0)
        clip2 = AudioClip(
            track_id=trk2.track_id,
            start_time_sec=0.5,
            duration_sec=1.5,
            gain_db=0.0,
        )
        trk2.add_clip(clip2)

        master_mix, stems = MultitrackMixer.render_session(session, auto_duck_music=True)
        self.assertEqual(master_mix.shape[0], 2)
        self.assertGreater(master_mix.shape[1], int(48000 * 1.5))
        self.assertIn("dialogue", stems)
        self.assertIn("music", stems)
        self.assertIn("effects", stems)

    def test_16_mastering_engine_and_stem_export(self):
        """16. Loudness mastering and multi-stem export."""
        session = AudioSession(project_id="test_proj_audio", name="Mastering Test")
        trk = session.add_track("Vocal", AudioTrackType.DIALOGUE)
        trk.add_clip(AudioClip(track_id=trk.track_id, file_path=self.test_audio_wav, duration_sec=1.0))

        out_dir = os.path.join(self.artifact_dir, "mastered_session")
        res = MasteringEngine.master_session(
            session=session,
            output_dir=out_dir,
            standard=LoudnessStandard.YOUTUBE,
            export_stems=True,
        )
        self.assertIn("master_wav", res["exported_files"])
        self.assertTrue(os.path.exists(res["exported_files"]["master_wav"]))
        self.assertIn("stems", res["exported_files"])
        self.assertTrue(os.path.exists(res["exported_files"]["stems"]["dialogue"]))

    def test_17_voice_authorization_and_synthesis(self):
        """17. Voice talent authorization check and emotional speech synthesis."""
        # Authorized talent
        authorized_consent = VoiceConsentRecord(actor_name="Jane Doe", is_authorized=True)
        req_auth = SpeechSynthesisRequest(
            text="Welcome to the universal AI video production studio.",
            voice_profile_id="voice_jane_female",
            emotion="EXCITED",
            consent_record=authorized_consent,
        )
        res_auth = VoiceProducer.synthesize_speech(req_auth, sample_rate=48000)
        self.assertTrue(res_auth["success"])
        self.assertGreater(len(res_auth["word_markers"]), 5)
        self.assertEqual(res_auth["audio_data"].shape[0], 2)

        # Unauthorized talent should raise PermissionError
        unauthorized_consent = VoiceConsentRecord(actor_name="Unlicensed Actor", is_authorized=False)
        req_unauth = SpeechSynthesisRequest(
            text="Unlicensed speech attempt.",
            voice_profile_id="voice_clone_unauthorized",
            consent_record=unauthorized_consent,
        )
        with self.assertRaises(PermissionError):
            VoiceProducer.synthesize_speech(req_unauth)

    def test_18_timeline_and_director_bridges(self):
        """18. Integration with OpenTimelineIO NLE timeline and AI Director blueprint."""
        # Director Bridge
        blueprint = {
            "title": "Documentary Intro",
            "tempo_bpm": 110.0,
            "audio_cues": [
                {"type": "voice", "start_time_sec": 0.5, "duration_sec": 3.0, "description": "Intro Narration"},
                {"type": "music", "start_time_sec": 0.0, "duration_sec": 10.0, "description": "Atmospheric Score"},
                {"type": "sfx", "start_time_sec": 3.5, "duration_sec": 1.2, "description": "Sub Impact"},
            ],
        }
        session_from_dir = DirectorAudioBridge.blueprint_to_audio_session(blueprint, "proj_doc_01")
        self.assertEqual(len(session_from_dir.tracks), 4)  # Dialogue, Music, SFX, Ambience
        self.assertEqual(session_from_dir.tempo_bpm, 110.0)

        # Timeline Bridge
        class MockTimelineTrack:
            def __init__(self, name, kind, clips):
                self.name = name
                self.kind = kind
                self.clips = clips

        class MockTimelineClip:
            def __init__(self, name, start, dur):
                self.name = name
                self.source_range = type("Range", (), {
                    "start_time": RationalTime(int(start * 24), 24),
                    "duration": RationalTime(int(dur * 24), 24),
                })()

        mock_tl = type("MockTL", (), {
            "name": "NLE Sequence",
            "tracks": [
                MockTimelineTrack("Dialogue A1", "audio", [MockTimelineClip("Actor Line 1", 1.0, 2.0)]),
                MockTimelineTrack("Music A2", "audio", [MockTimelineClip("Background Track", 0.0, 5.0)]),
            ],
        })()
        session_from_tl = TimelineAudioBridge.timeline_to_audio_session(mock_tl, "proj_tl_01")
        self.assertEqual(len(session_from_tl.tracks), 2)
        self.assertEqual(len(session_from_tl.tracks[0].clips), 1)
        self.assertAlmostEqual(session_from_tl.tracks[0].clips[0].start_time_sec, 1.0)

    def test_19_database_persistence(self):
        """19. Database CRUD for AudioSession and AudioAssets."""
        session = AudioSession(project_id="test_proj_audio", name="DB Persisted Session")
        session.add_track("Voice A1", AudioTrackType.VOICE_OVER)
        self.db.save_audio_session(session)

        loaded = self.db.get_audio_session(session.session_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["name"], "DB Persisted Session")
        self.assertEqual(loaded["sample_rate"], 48000)

        # List
        sess_list = self.db.list_audio_sessions("test_proj_audio")
        self.assertTrue(any(s["session_id"] == session.session_id for s in sess_list))

        # Audio Asset CRUD
        sfx_meta = SFXAssetMetadata(
            name="Cinematic Boom",
            category="IMPACT",
            duration_sec=2.5,
            tags=["cinema", "boom", "sub"],
        )
        self.db.save_audio_asset(sfx_meta, project_id="test_proj_audio")
        loaded_asset = self.db.get_audio_asset(sfx_meta.sfx_id)
        self.assertIsNotNone(loaded_asset)
        self.assertEqual(loaded_asset["category"], "IMPACT")

    def test_20_service_execution_and_health_checks(self):
        """20. Department 14 & Department 17 Service interfaces and health checks."""
        import asyncio
        from departments.audio_production.interface import AudioProductionRequest
        from departments.subtitles_dubbing.interface import SubtitlesDubbingRequest

        # Department 14 Service
        audio_svc = AudioProductionService(output_root=os.path.join(self.artifact_dir, "svc_scratch"))
        self.assertTrue(audio_svc.health_check())

        session = AudioSession(project_id="test_proj_audio", name="Service Test Session")
        trk = session.add_track("Narration", AudioTrackType.VOICE_OVER)
        trk.add_clip(AudioClip(track_id=trk.track_id, duration_sec=0.5))

        req = AudioProductionRequest(
            project_id=uuid.uuid4(),
            parameters={
                "action": "master_session",
                "session": session.to_dict(),
                "standard": "YOUTUBE",
            },
        )
        loop = asyncio.new_event_loop()
        resp = loop.run_until_complete(audio_svc.execute(req))
        self.assertTrue(resp.success)
        self.assertIn("master_wav", resp.data["exported_files"])

        # Department 17 Service
        dub_svc = SubtitlesDubbingService()
        self.assertTrue(dub_svc.health_check())
        dub_req = SubtitlesDubbingRequest(
            project_id=uuid.uuid4(),
            parameters={
                "action": "dub_dialogue",
                "text": "Universal video audio dubbing test.",
                "language": "hi",
            },
        )
        dub_resp = loop.run_until_complete(dub_svc.execute(dub_req))
        loop.close()
        self.assertTrue(dub_resp.success)
        self.assertEqual(dub_resp.data["language"], "hi")


if __name__ == "__main__":
    unittest.main()
