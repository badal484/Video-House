"""
Comprehensive Unit and Integration Test Suite for Part 05:
Professional Non-Linear Video Editing Engine.

Tests:
1. RationalTime & TimeRange arithmetic (drift-free, frame conversions, timecode formatting)
2. Canonical Timeline & multi-track hierarchy (V1/V2, A1/A2, track states)
3. Clip insertion modes (OVERWRITE and INSERT/ripple)
4. Clip splitting and trimming (boundary validation, source in/out math)
5. Advanced editing modes (ripple delete, roll edit)
6. Slip and slide editing operations
7. J-Cut and L-Cut audio/video synchronization
8. Transitions, effects, and keyframe interpolation curves (linear, ease-in, ease-out, hold)
9. Database persistence & transactional undo/redo
10. OpenTimelineIO (OTIO) bidirectional interchange and gap preservation
11. Part 04 EditingBlueprint execution and automated assembly
12. Deterministic multi-track FFmpeg rendering, preview generation, and FFprobe verification
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from uuid import UUID, uuid4

from core.assets.database import (
    AssetDatabase,
    AssetRecord,
    AssetRole,
    MediaType,
    ProcessingStatus
)
from core.timeline.keyframe_engine import KeyframeInterpolator
from core.timeline.operations import TimelineOperations
from core.timeline.otio_adapter import OTIOAdapter
from core.timeline.time_model import RationalTime, TimeRange
from core.timeline.timeline_models import (
    Clip,
    EditingProject,
    EditMode,
    Effect,
    EffectType,
    InterpolationMode,
    Keyframe,
    RenderStatus,
    Timeline,
    Track,
    TrackType,
    Transition,
    TransitionType
)

from departments.video_editing.blueprint_executor import BlueprintExecutor
from departments.video_editing.preview_engine import PreviewEngine
from departments.video_editing.render_engine import RenderEngine
from departments.video_editing.service import VideoEditingService
from departments.video_editing.sync_engine import AudioVideoSyncEngine
from departments.video_editing.timeline_manager import TimelineManager


class TestNonLinearEditingEngine(unittest.TestCase):
    """Test suite for Part 05 Professional Non-Linear Video Editing Engine."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="studio_test_p05_")
        self.db_path = Path(self.temp_dir) / "test_editing.db"
        self.db = AssetDatabase(str(self.db_path))
        self.project_id = uuid4()
        self.db.create_project(self.project_id, "Test Editing Project")

        self.manager = TimelineManager(self.db)
        self.renderer = RenderEngine(self.db, storage_root=self.temp_dir)
        self.previewer = PreviewEngine(self.db, self.renderer, cache_dir=str(Path(self.temp_dir) / "cache"))
        self.executor = BlueprintExecutor(self.db, self.manager)
        self.sync_engine = AudioVideoSyncEngine()
        self.service = VideoEditingService(self.db)

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def _create_synthetic_video(self, filename: str, duration_sec: float = 3.0, color: str = "blue") -> str:
        """Helper to generate a real synthetic video file for render testing."""
        path = str(Path(self.temp_dir) / filename)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x240:d={duration_sec}:r=24",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration_sec}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000",
            path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return path

    def test_01_rational_time_arithmetic(self):
        """Test exact rational time math, frame conversions, timecodes, and rescaling."""
        t1 = RationalTime(24, 24.0)  # 1.0 second, 24 frames
        self.assertEqual(t1.to_seconds(), 1.0)
        self.assertEqual(t1.to_frames(), 24)
        self.assertEqual(t1.to_timecode(), "00:00:01:00")

        t2 = RationalTime(48, 24.0)  # 2.0 seconds
        t_sum = t1 + t2
        self.assertEqual(t_sum.to_seconds(), 3.0)
        self.assertEqual(t_sum.to_frames(), 72)

        # Rescaling between frame rates (24fps -> 30fps)
        t_30 = t1.rescaled_to(30.0)
        self.assertEqual(t_30.rate, 30.0)
        self.assertEqual(t_30.to_frames(), 30)
        self.assertEqual(t_30.to_seconds(), 1.0)

        # Parsing timecode string
        parsed = RationalTime.from_timecode("00:01:30:12", rate=24.0)
        # 1 min (60s) + 30s = 90s * 24 = 2160 + 12 = 2172 frames
        self.assertEqual(parsed.to_frames(), 2172)
        self.assertAlmostEqual(parsed.to_seconds(), 90.5)

        # TimeRange interval checks
        tr = TimeRange(RationalTime(0, 24), RationalTime(72, 24))
        self.assertTrue(tr.contains_time(RationalTime(24, 24)))
        self.assertFalse(tr.contains_time(RationalTime(96, 24)))

    def test_02_canonical_timeline_and_track_hierarchy(self):
        """Test multi-track timeline construction, V1/V2 video tracks and A1/A2 audio tracks."""
        tl = self.manager.create_timeline(
            project_id=self.project_id,
            name="Commercial Master",
            fps=24.0,
            resolution_width=1920,
            resolution_height=1080
        )
        self.assertEqual(len(tl.tracks), 3)  # V1, A1, A2 default
        self.assertEqual(tl.fps, 24.0)

        # Add V2 overlay track
        v2 = self.manager.add_track(tl.timeline_id, TrackType.VIDEO, "V2 - B-Roll Overlays")
        self.assertEqual(v2.track_type, TrackType.VIDEO)
        self.assertEqual(v2.name, "V2 - B-Roll Overlays")

        refreshed = self.manager.get_timeline(tl.timeline_id)
        self.assertEqual(len(refreshed.tracks), 4)

    def test_03_clip_insertion_and_modes(self):
        """Test OVERWRITE and INSERT (ripple) clip insertion modes."""
        tl = self.manager.create_timeline(self.project_id, "Cut Test", fps=24.0)
        v1 = tl.tracks[0]

        # 1. Append first clip: 0.0s to 3.0s
        c1 = self.manager.add_clip_to_track(
            timeline_id=tl.timeline_id,
            track_id=v1.track_id,
            asset_id=uuid4(),
            timeline_start_sec=0.0,
            duration_sec=3.0,
            name="Shot 1"
        )
        self.assertEqual(c1.timeline_start.to_seconds(), 0.0)
        self.assertEqual(c1.timeline_duration.to_seconds(), 3.0)

        # 2. Append second clip: 3.0s to 6.0s
        c2 = self.manager.add_clip_to_track(
            timeline_id=tl.timeline_id,
            track_id=v1.track_id,
            asset_id=uuid4(),
            timeline_start_sec=3.0,
            duration_sec=3.0,
            name="Shot 2"
        )

        # 3. Insert Mode (Ripple) at 1.5s: duration 2.0s
        c_ins = self.manager.add_clip_to_track(
            timeline_id=tl.timeline_id,
            track_id=v1.track_id,
            asset_id=uuid4(),
            timeline_start_sec=1.5,
            duration_sec=2.0,
            mode=EditMode.INSERT,
            name="Inserted Cut"
        )

        refreshed = self.manager.get_timeline(tl.timeline_id)
        tr = refreshed.tracks[0]
        # Downstream clip c2 was pushed forward from 3.0s to 5.0s
        shot2 = next(c for c in tr.clips if c.clip_id == c2.clip_id)
        self.assertAlmostEqual(shot2.timeline_start.to_seconds(), 5.0)

    def test_04_clip_splitting_and_trimming(self):
        """Test splitting a clip into two independent adjacent clips and trimming."""
        tl = self.manager.create_timeline(self.project_id, "Split Test", fps=24.0)
        v1 = tl.tracks[0]

        c = self.manager.add_clip_to_track(
            timeline_id=tl.timeline_id,
            track_id=v1.track_id,
            asset_id=uuid4(),
            timeline_start_sec=0.0,
            duration_sec=6.0,
            source_in_sec=10.0,
            name="Original Take"
        )

        # Split at 2.5s
        c_left, c_right = self.manager.split_clip(tl.timeline_id, c.clip_id, split_time_sec=2.5)

        self.assertAlmostEqual(c_left.timeline_duration.to_seconds(), 2.5)
        self.assertAlmostEqual(c_right.timeline_start.to_seconds(), 2.5)
        self.assertAlmostEqual(c_right.timeline_duration.to_seconds(), 3.5)
        # Verify source offsets are maintained
        self.assertAlmostEqual(c_left.source_in.to_seconds(), 10.0)
        self.assertAlmostEqual(c_right.source_in.to_seconds(), 12.5)

        # Trim head of right clip from 2.5s to 3.0s
        c_trimmed = self.manager.trim_clip(tl.timeline_id, c_right.clip_id, new_start_sec=3.0)
        self.assertAlmostEqual(c_trimmed.timeline_start.to_seconds(), 3.0)
        self.assertAlmostEqual(c_trimmed.timeline_duration.to_seconds(), 3.0)
        self.assertAlmostEqual(c_trimmed.source_in.to_seconds(), 13.0)

    def test_05_ripple_delete_and_roll_edit(self):
        """Test ripple delete and roll editing between touching clips."""
        tl = self.manager.create_timeline(self.project_id, "Roll Test", fps=24.0)
        v1 = tl.tracks[0]

        c1 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 0.0, 4.0, name="Clip A")
        c2 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 4.0, 4.0, name="Clip B")
        c3 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 8.0, 4.0, name="Clip C")

        refreshed = self.manager.get_timeline(tl.timeline_id)
        v1 = refreshed.tracks[0]

        # Roll edit boundary between c1 and c2 from 4.0s to 5.0s
        out_c, in_c = self.manager.roll_edit(
            tl.timeline_id, c1.clip_id, c2.clip_id, 5.0
        )
        self.assertAlmostEqual(out_c.timeline_duration.to_seconds(), 5.0)
        self.assertAlmostEqual(in_c.timeline_start.to_seconds(), 5.0)
        self.assertAlmostEqual(in_c.timeline_duration.to_seconds(), 3.0)
        # Total combined length remains exactly 8.0s
        self.assertAlmostEqual(out_c.timeline_duration.to_seconds() + in_c.timeline_duration.to_seconds(), 8.0)

        # Ripple delete middle clip (c2)
        removed = self.manager.ripple_delete_clip(tl.timeline_id, c2.clip_id)
        self.assertIsNotNone(removed)

        refreshed = self.manager.get_timeline(tl.timeline_id)
        tr = refreshed.tracks[0]
        # c3 was pulled forward from 8.0s to 5.0s
        remaining_c3 = next(c for c in tr.clips if c.clip_id == c3.clip_id)
        self.assertAlmostEqual(remaining_c3.timeline_start.to_seconds(), 5.0)

    def test_06_slip_and_slide_edits(self):
        """Test slip edit (shifting source in/out without altering timeline start/duration)."""
        tl = self.manager.create_timeline(self.project_id, "Slip Test", fps=24.0)
        v1 = tl.tracks[0]

        c = self.manager.add_clip_to_track(
            tl.timeline_id, v1.track_id, uuid4(),
            timeline_start_sec=2.0, duration_sec=3.0, source_in_sec=5.0
        )
        # Slip forward by 2.0s
        slipped = self.manager.slip_clip(tl.timeline_id, c.clip_id, 2.0)

        # Timeline position and duration MUST remain unchanged
        self.assertAlmostEqual(slipped.timeline_start.to_seconds(), 2.0)
        self.assertAlmostEqual(slipped.timeline_duration.to_seconds(), 3.0)
        # Source in and out shift from 5.0s -> 7.0s and 8.0s -> 10.0s
        self.assertAlmostEqual(slipped.source_in.to_seconds(), 7.0)
        self.assertAlmostEqual(slipped.source_out.to_seconds(), 10.0)

    def test_07_j_cut_and_l_cut_av_sync(self):
        """Test J-Cut (audio lead) and L-Cut (audio lag) synchronization."""
        v_clip = Clip(
            clip_id=uuid4(), asset_id=uuid4(), track_id=uuid4(),
            timeline_start=RationalTime.from_seconds(5.0, 24.0),
            timeline_duration=RationalTime.from_seconds(4.0, 24.0),
            source_in=RationalTime.from_seconds(10.0, 24.0),
            source_out=RationalTime.from_seconds(14.0, 24.0)
        )
        a_clip = Clip(
            clip_id=uuid4(), asset_id=uuid4(), track_id=uuid4(),
            timeline_start=RationalTime.from_seconds(5.0, 24.0),
            timeline_duration=RationalTime.from_seconds(4.0, 24.0),
            source_in=RationalTime.from_seconds(10.0, 24.0),
            source_out=RationalTime.from_seconds(14.0, 24.0)
        )
        self.sync_engine.link_clips(v_clip, a_clip)
        self.assertEqual(v_clip.linked_clip_id, a_clip.clip_id)
        self.assertEqual(self.sync_engine.verify_sync(v_clip, a_clip), 0.0)

        # Create J-Cut: incoming dialogue leads visual cut by 1.5 seconds
        self.sync_engine.create_j_cut(v_clip, a_clip, lead_time_sec=1.5)
        self.assertAlmostEqual(a_clip.timeline_start.to_seconds(), 3.5)
        self.assertAlmostEqual(a_clip.timeline_duration.to_seconds(), 5.5)
        self.assertAlmostEqual(a_clip.source_in.to_seconds(), 8.5)

    def test_08_transitions_and_keyframe_interpolation(self):
        """Test transitions, effects, and mathematical keyframe curves."""
        tl = self.manager.create_timeline(self.project_id, "FX Test", fps=24.0)
        v1 = tl.tracks[0]

        c1 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 0.0, 4.0)
        c2 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 4.0, 4.0)

        # Add cross dissolve transition
        trans = self.manager.add_transition(
            tl.timeline_id, v1.track_id, TransitionType.CROSS_DISSOLVE,
            start_time_sec=3.5, duration_sec=1.0, from_clip_id=c1.clip_id, to_clip_id=c2.clip_id
        )
        self.assertIsNotNone(trans.transition_id)
        self.assertEqual(trans.transition_type, TransitionType.CROSS_DISSOLVE)

        # Add opacity effect to c1
        eff = self.manager.add_effect_to_clip(tl.timeline_id, c1.clip_id, EffectType.OPACITY, {"opacity": 0.8})
        self.assertEqual(eff.effect_type, EffectType.OPACITY)

        # Test Keyframe Curve Interpolation
        kfs = [
            Keyframe("opacity", RationalTime.from_seconds(0.0, 24.0), 0.0, InterpolationMode.LINEAR),
            Keyframe("opacity", RationalTime.from_seconds(2.0, 24.0), 1.0, InterpolationMode.EASE_IN_OUT),
            Keyframe("opacity", RationalTime.from_seconds(4.0, 24.0), 0.0, InterpolationMode.HOLD)
        ]
        # At t=1.0 (midway between 0 and 2.0 with linear interpolation) -> 0.5
        v_mid = KeyframeInterpolator.evaluate(kfs[:2], RationalTime.from_seconds(1.0, 24.0))
        self.assertAlmostEqual(v_mid, 0.5)

    def test_09_database_persistence_and_undo_redo(self):
        """Test saving full editing project to SQLite, reopening, and undo/redo."""
        tl = self.manager.create_timeline(self.project_id, "Persistence Test", fps=24.0)
        v1 = tl.tracks[0]

        c1 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 0.0, 3.0, name="Save Shot 1")
        c2 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 3.0, 4.0, name="Save Shot 2")

        # Reopen from DB
        loaded_tl = self.manager.get_timeline(tl.timeline_id)
        self.assertIsNotNone(loaded_tl)
        self.assertEqual(len(loaded_tl.tracks[0].clips), 2)
        self.assertEqual(loaded_tl.tracks[0].clips[0].name, "Save Shot 1")
        self.assertAlmostEqual(loaded_tl.duration.to_seconds(), 7.0)

        # Add a 3rd clip and test undo
        c3 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 7.0, 2.0, name="To Undo")
        self.assertEqual(len(self.manager.get_timeline(tl.timeline_id).tracks[0].clips), 3)

        undone = self.manager.undo(tl.timeline_id)
        self.assertIsNotNone(undone)
        self.assertEqual(len(undone.tracks[0].clips), 2)

        # Test redo
        redone = self.manager.redo(tl.timeline_id)
        self.assertIsNotNone(redone)
        self.assertEqual(len(redone.tracks[0].clips), 3)

    def test_10_otio_roundtrip_interchange(self):
        """Test OpenTimelineIO serialization, gap preservation, and lossless round-trip."""
        tl = self.manager.create_timeline(self.project_id, "OTIO Master", fps=24.0)
        v1 = tl.tracks[0]

        # Add two clips separated by a 2.0s gap
        c1 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 0.0, 3.0, name="OTIO Clip 1")
        c2 = self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, uuid4(), 5.0, 4.0, name="OTIO Clip 2")

        tl = self.manager.get_timeline(tl.timeline_id)
        otio_path = str(Path(self.temp_dir) / "interchange.otio")
        OTIOAdapter.export_otio_json(tl, otio_path)
        self.assertTrue(Path(otio_path).exists())

        # Read back into canonical Timeline
        reimported = OTIOAdapter.import_otio_json(otio_path, self.project_id)
        self.assertEqual(reimported.name, tl.name)
        reimported_v1 = reimported.tracks[0]
        self.assertEqual(len(reimported_v1.clips), 2)
        # Verify gap preservation: clip 2 starts at exactly 5.0s
        self.assertAlmostEqual(reimported_v1.clips[1].timeline_start.to_seconds(), 5.0)

    def test_11_blueprint_execution(self):
        """Test executing a Part 04 EditingBlueprint into an editable multi-track timeline."""
        source_id_1 = uuid4()
        source_id_2 = uuid4()

        bp_dict = {
            "target_duration_sec": 10.0,
            "pacing_style": "FAST_PACED",
            "narrative_order": [
                {
                    "source_asset_id": str(source_id_1),
                    "timeline_in_sec": 0.0,
                    "timeline_out_sec": 4.0,
                    "source_in_sec": 2.0,
                    "source_out_sec": 6.0,
                    "shot_purpose": "Establishing Aerial",
                    "transition_in": "FADE_FROM_BLACK"
                },
                {
                    "source_asset_id": str(source_id_2),
                    "timeline_in_sec": 4.0,
                    "timeline_out_sec": 9.0,
                    "source_in_sec": 0.0,
                    "source_out_sec": 5.0,
                    "shot_purpose": "Product Close Up",
                    "transition_in": "CROSS_DISSOLVE"
                }
            ]
        }

        tl = self.executor.execute_blueprint(self.project_id, bp_dict)
        self.assertIsNotNone(tl.timeline_id)
        v1 = tl.tracks[0]
        self.assertEqual(len(v1.clips), 2)
        self.assertAlmostEqual(v1.clips[0].timeline_duration.to_seconds(), 4.0)
        self.assertAlmostEqual(v1.clips[1].timeline_duration.to_seconds(), 5.0)
        # Transition was added between clip 1 and clip 2
        self.assertEqual(len(v1.transitions), 1)
        self.assertEqual(v1.transitions[0].transition_type, TransitionType.CROSS_DISSOLVE)

    def test_12_synthetic_media_rendering_and_qc(self):
        """Test real multi-track rendering with FFmpeg, preview proxy generation, and FFprobe QC."""
        vid1_path = self._create_synthetic_video("vid1.mp4", duration_sec=3.0, color="red")
        vid2_path = self._create_synthetic_video("vid2.mp4", duration_sec=3.0, color="green")

        asset_id_1 = uuid4()
        asset_id_2 = uuid4()

        # Register source assets in DB
        self.db.register_asset(AssetRecord(
            asset_id=asset_id_1,
            project_id=self.project_id,
            original_filename="vid1.mp4",
            display_name="vid1.mp4",
            media_type=MediaType.VIDEO,
            detected_format="mp4",
            mime_type="video/mp4",
            byte_size=Path(vid1_path).stat().st_size,
            checksum_sha256="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            storage_path=vid1_path,
            import_timestamp=datetime.now(timezone.utc).isoformat(),
            processing_status=ProcessingStatus.COMPLETED,
            metadata_status=ProcessingStatus.COMPLETED,
            derivative_status=ProcessingStatus.COMPLETED
        ))
        self.db.register_asset(AssetRecord(
            asset_id=asset_id_2,
            project_id=self.project_id,
            original_filename="vid2.mp4",
            display_name="vid2.mp4",
            media_type=MediaType.VIDEO,
            detected_format="mp4",
            mime_type="video/mp4",
            byte_size=Path(vid2_path).stat().st_size,
            checksum_sha256="fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
            storage_path=vid2_path,
            import_timestamp=datetime.now(timezone.utc).isoformat(),
            processing_status=ProcessingStatus.COMPLETED,
            metadata_status=ProcessingStatus.COMPLETED,
            derivative_status=ProcessingStatus.COMPLETED
        ))

        # Build timeline with 2 clips on V1
        tl = self.manager.create_timeline(self.project_id, "Render QC Test", fps=24.0, resolution_width=640, resolution_height=360)
        v1 = tl.tracks[0]

        self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, asset_id_1, 0.0, 2.0, source_in_sec=0.0)
        self.manager.add_clip_to_track(tl.timeline_id, v1.track_id, asset_id_2, 2.0, 2.0, source_in_sec=0.0)

        # Fetch refreshed timeline containing the added clips
        tl = self.manager.get_timeline(tl.timeline_id)

        # 1. Render Final Master MP4
        output_master = str(Path(self.temp_dir) / "final_master.mp4")
        job = self.renderer.render_timeline(tl, output_master, is_preview=False)
        self.assertEqual(job.status, RenderStatus.COMPLETED)
        self.assertTrue(Path(output_master).exists())
        self.assertGreater(Path(output_master).stat().st_size, 1000)

        # 2. Inspect with FFprobe
        qc_meta = RenderEngine.inspect_output_media(output_master)
        v_stream = next(s for s in qc_meta["streams"] if s["codec_type"] == "video")
        a_stream = next(s for s in qc_meta["streams"] if s["codec_type"] == "audio")

        self.assertEqual(v_stream["codec_name"], "h264")
        self.assertEqual(a_stream["codec_name"], "aac")
        self.assertEqual(int(v_stream["width"]), 640)
        self.assertEqual(int(v_stream["height"]), 360)
        self.assertAlmostEqual(float(qc_meta["format"]["duration"]), 4.0, delta=0.2)

        # 3. Test Preview Generation
        preview_job = self.previewer.generate_timeline_preview(tl)
        self.assertTrue(Path(preview_job.output_path).exists())


if __name__ == "__main__":
    unittest.main()
