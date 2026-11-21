"""
Timeline Manager and Editing Project Lifecycle Service.
Orchestrates projects, multi-track timelines, tracks, clips, transitions,
effects, and in-memory undo/redo transaction history.
"""
import copy
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from core.assets.database import AssetDatabase
from core.timeline.keyframe_engine import KeyframeInterpolator
from core.timeline.operations import TimelineOperations
from core.timeline.time_model import RationalTime
from core.timeline.timeline_models import (
    Clip,
    EditingProject,
    EditMode,
    Effect,
    EffectType,
    InterpolationMode,
    Keyframe,
    Marker,
    Timeline,
    Track,
    TrackType,
    Transition,
    TransitionType
)

logger = logging.getLogger("studio.video_editing.manager")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TimelineManager:
    """
    Manages non-linear editing projects and multi-track timelines.
    """

    def __init__(self, db: Optional[AssetDatabase] = None):
        self.db = db
        # In-memory undo/redo stacks: timeline_id -> (undo_list, redo_list)
        self._undo_stacks: Dict[UUID, List[Timeline]] = {}
        self._redo_stacks: Dict[UUID, List[Timeline]] = {}
        self.max_history: int = 50

    def _push_undo(self, timeline: Timeline) -> None:
        tl_id = timeline.timeline_id
        if tl_id not in self._undo_stacks:
            self._undo_stacks[tl_id] = []
            self._redo_stacks[tl_id] = []

        # Store deep copy of current state
        self._undo_stacks[tl_id].append(copy.deepcopy(timeline))
        if len(self._undo_stacks[tl_id]) > self.max_history:
            self._undo_stacks[tl_id].pop(0)

        # Clear redo stack on new action
        self._redo_stacks[tl_id].clear()

    def undo(self, timeline_id: UUID) -> Optional[Timeline]:
        """Restores timeline to previous state from undo stack."""
        if timeline_id not in self._undo_stacks or not self._undo_stacks[timeline_id]:
            return None

        # Fetch current state from DB or memory
        current = self.get_timeline(timeline_id)
        if current:
            self._redo_stacks[timeline_id].append(copy.deepcopy(current))

        restored = self._undo_stacks[timeline_id].pop()
        restored.updated_at = utc_now_iso()
        restored.version += 1
        if self.db:
            self.db.save_timeline(restored)
        return restored

    def redo(self, timeline_id: UUID) -> Optional[Timeline]:
        """Restores previously undone state from redo stack."""
        if timeline_id not in self._redo_stacks or not self._redo_stacks[timeline_id]:
            return None

        current = self.get_timeline(timeline_id)
        if current:
            self._undo_stacks[timeline_id].append(copy.deepcopy(current))

        restored = self._redo_stacks[timeline_id].pop()
        restored.updated_at = utc_now_iso()
        restored.version += 1
        if self.db:
            self.db.save_timeline(restored)
        return restored

    # -------------------------------------------------------------------------
    # Project Operations
    # -------------------------------------------------------------------------

    def create_project(self, project_id: UUID, name: str, settings: Optional[Dict[str, Any]] = None) -> EditingProject:
        now = utc_now_iso()
        proj = EditingProject(
            project_id=project_id,
            name=name,
            settings=settings or {"color_space": "Rec.709", "proxy_mode": True},
            created_at=now,
            updated_at=now
        )
        if self.db:
            self.db.save_editing_project(proj)
        return proj

    def get_project(self, project_id: UUID) -> Optional[EditingProject]:
        if not self.db:
            return None
        data = self.db.get_editing_project(project_id)
        if not data:
            return None
        return EditingProject(
            project_id=data["project_id"],
            name=data["name"],
            active_timeline_id=data["active_timeline_id"],
            settings=data["settings"],
            revision=data["revision"],
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )

    # -------------------------------------------------------------------------
    # Timeline Operations
    # -------------------------------------------------------------------------

    def create_timeline(
        self,
        project_id: UUID,
        name: str = "Master Timeline",
        fps: float = 24.0,
        resolution_width: int = 1920,
        resolution_height: int = 1080,
        sample_rate: int = 48000
    ) -> Timeline:
        tl_id = uuid4()
        now = utc_now_iso()
        tl = Timeline(
            timeline_id=tl_id,
            project_id=project_id,
            name=name,
            time_base=fps,
            fps=fps,
            resolution_width=resolution_width,
            resolution_height=resolution_height,
            sample_rate=sample_rate,
            created_at=now,
            updated_at=now
        )
        # Add default tracks: V1 (main video), A1 (dialogue), A2 (music)
        t_v1 = Track(track_id=uuid4(), timeline_id=tl_id, track_type=TrackType.VIDEO, name="V1 - Main Video", order_index=0)
        t_a1 = Track(track_id=uuid4(), timeline_id=tl_id, track_type=TrackType.AUDIO, name="A1 - Dialogue / VO", order_index=1)
        t_a2 = Track(track_id=uuid4(), timeline_id=tl_id, track_type=TrackType.AUDIO, name="A2 - Music & SFX", order_index=2)
        tl.tracks.extend([t_v1, t_a1, t_a2])

        if self.db:
            self.db.save_timeline(tl)
            # Update active timeline on project
            proj = self.get_project(project_id)
            if proj:
                proj.active_timeline_id = tl_id
                proj.updated_at = now
                self.db.save_editing_project(proj)

        return tl

    def get_timeline(self, timeline_id: UUID) -> Optional[Timeline]:
        if not self.db:
            return None
        data = self.db.get_timeline(timeline_id)
        if not data:
            return None
        
        # Reconstruct canonical Timeline
        tl = Timeline(
            timeline_id=data["timeline_id"],
            project_id=data["project_id"],
            name=data["name"],
            time_base=data["time_base"],
            fps=data["fps"],
            resolution_width=data["resolution_width"],
            resolution_height=data["resolution_height"],
            sample_rate=data["sample_rate"],
            version=data["version"],
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )

        for tr_data in data["tracks"]:
            track = Track(
                track_id=tr_data["track_id"],
                timeline_id=tr_data["timeline_id"],
                track_type=TrackType(tr_data["track_type"]),
                name=tr_data["name"],
                order_index=tr_data["order_index"],
                is_muted=tr_data["is_muted"],
                is_visible=tr_data["is_visible"],
                is_locked=tr_data["is_locked"],
                is_solo=tr_data["is_solo"],
                gain=tr_data["gain"],
                opacity=tr_data["opacity"]
            )
            for c_data in tr_data["clips"]:
                clip = Clip(
                    clip_id=c_data["clip_id"],
                    asset_id=c_data["asset_id"],
                    track_id=c_data["track_id"],
                    timeline_start=RationalTime.from_seconds(c_data["timeline_start_sec"], tl.fps),
                    timeline_duration=RationalTime.from_seconds(c_data["timeline_dur_sec"], tl.fps),
                    source_in=RationalTime.from_seconds(c_data["source_in_sec"], tl.fps),
                    source_out=RationalTime.from_seconds(c_data["source_out_sec"], tl.fps),
                    speed=c_data["speed"],
                    transform=c_data["transform"],
                    opacity=c_data["opacity"],
                    volume=c_data["volume"],
                    pan=c_data["pan"],
                    enabled=c_data["enabled"],
                    linked_clip_id=c_data["linked_clip_id"],
                    name=c_data["name"]
                )
                for e_data in c_data.get("effects", []):
                    eff = Effect(
                        effect_id=e_data["effect_id"],
                        effect_type=EffectType(e_data["effect_type"]),
                        parameters=e_data["parameters"],
                        enabled=e_data["enabled"],
                        start_time=RationalTime.from_seconds(e_data["start_sec"], tl.fps) if e_data.get("start_sec") is not None else None,
                        duration=RationalTime.from_seconds(e_data["duration_sec"], tl.fps) if e_data.get("duration_sec") is not None else None,
                        processing_order=e_data["processing_order"]
                    )
                    clip.effects.append(eff)
                track.clips.append(clip)

            for t_data in tr_data["transitions"]:
                trans = Transition(
                    transition_id=t_data["transition_id"],
                    transition_type=TransitionType(t_data["transition_type"]),
                    start_time=RationalTime.from_seconds(t_data["start_time_sec"], tl.fps),
                    duration=RationalTime.from_seconds(t_data["duration_sec"], tl.fps),
                    from_clip_id=t_data["from_clip_id"],
                    to_clip_id=t_data["to_clip_id"],
                    parameters=t_data["parameters"],
                    easing=t_data["easing"]
                )
                track.transitions.append(trans)

            tl.tracks.append(track)

        for m_data in data["markers"]:
            marker = Marker(
                marker_id=m_data["marker_id"],
                timeline_id=m_data["timeline_id"],
                time=RationalTime.from_seconds(m_data["time_sec"], tl.fps),
                name=m_data["name"],
                color=m_data["color"],
                comment=m_data["comment"]
            )
            tl.markers.append(marker)

        tl.duration = tl.calculate_total_duration()
        return tl

    def add_track(self, timeline_id: UUID, track_type: TrackType, name: str) -> Track:
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        self._push_undo(tl)
        new_track = Track(
            track_id=uuid4(),
            timeline_id=timeline_id,
            track_type=track_type,
            name=name,
            order_index=len(tl.tracks)
        )
        tl.tracks.append(new_track)
        tl.updated_at = utc_now_iso()
        tl.version += 1
        if self.db:
            self.db.save_timeline(tl)
        return new_track

    def add_clip_to_track(
        self,
        timeline_id: UUID,
        track_id: UUID,
        asset_id: UUID,
        timeline_start_sec: float,
        duration_sec: float,
        source_in_sec: float = 0.0,
        speed: float = 1.0,
        mode: EditMode = EditMode.OVERWRITE,
        name: str = "Clip"
    ) -> Clip:
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        track = next((t for t in tl.tracks if t.track_id == track_id), None)
        if not track:
            raise ValueError(f"Track {track_id} not found on timeline {timeline_id}")

        self._push_undo(tl)
        clip = Clip(
            clip_id=uuid4(),
            asset_id=asset_id,
            track_id=track_id,
            timeline_start=RationalTime.from_seconds(timeline_start_sec, tl.fps),
            timeline_duration=RationalTime.from_seconds(duration_sec, tl.fps),
            source_in=RationalTime.from_seconds(source_in_sec, tl.fps),
            source_out=RationalTime.from_seconds(source_in_sec + (duration_sec * speed), tl.fps),
            speed=speed,
            name=name
        )

        TimelineOperations.insert_clip(track, clip, mode=mode)
        tl.duration = tl.calculate_total_duration()
        tl.updated_at = utc_now_iso()
        tl.version += 1

        if self.db:
            self.db.save_timeline(tl)

        return clip

    def split_clip(self, timeline_id: UUID, clip_id: UUID, split_time_sec: float) -> Tuple[Clip, Clip]:
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        track = next((t for t in tl.tracks if any(c.clip_id == clip_id for c in t.clips)), None)
        if not track:
            raise ValueError(f"Clip {clip_id} not found on timeline {timeline_id}")

        self._push_undo(tl)
        split_rt = RationalTime.from_seconds(split_time_sec, tl.fps)
        c1, c2 = TimelineOperations.split_clip(track, clip_id, split_rt)

        tl.updated_at = utc_now_iso()
        tl.version += 1
        if self.db:
            self.db.save_timeline(tl)

        return (c1, c2)

    def trim_clip(self, timeline_id: UUID, clip_id: UUID, new_start_sec: Optional[float] = None, new_end_sec: Optional[float] = None) -> Clip:
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        track = next((t for t in tl.tracks if any(c.clip_id == clip_id for c in t.clips)), None)
        if not track:
            raise ValueError(f"Clip {clip_id} not found on timeline {timeline_id}")

        self._push_undo(tl)
        clip = next(c for c in track.clips if c.clip_id == clip_id)

        if new_start_sec is not None:
            TimelineOperations.trim_clip_start(track, clip_id, RationalTime.from_seconds(new_start_sec, tl.fps))
        if new_end_sec is not None:
            TimelineOperations.trim_clip_end(track, clip_id, RationalTime.from_seconds(new_end_sec, tl.fps))

        tl.duration = tl.calculate_total_duration()
        tl.updated_at = utc_now_iso()
        tl.version += 1
        if self.db:
            self.db.save_timeline(tl)

        return clip

    def ripple_delete_clip(self, timeline_id: UUID, clip_id: UUID) -> Optional[Clip]:
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        track = next((t for t in tl.tracks if any(c.clip_id == clip_id for c in t.clips)), None)
        if not track:
            raise ValueError(f"Clip {clip_id} not found")

        self._push_undo(tl)
        removed = TimelineOperations.ripple_delete(track, clip_id)
        tl.duration = tl.calculate_total_duration()
        tl.updated_at = utc_now_iso()
        tl.version += 1

        if self.db:
            self.db.save_timeline(tl)

        return removed

    def roll_edit(
        self,
        timeline_id: UUID,
        outgoing_clip_id: UUID,
        incoming_clip_id: UUID,
        new_cut_sec: float
    ) -> Tuple[Clip, Clip]:
        """Roll edit: moves the cut boundary between two adjacent clips, saving state."""
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        track = next((t for t in tl.tracks if any(c.clip_id == outgoing_clip_id for c in t.clips)), None)
        if not track:
            raise ValueError(f"Clip {outgoing_clip_id} not found")

        self._push_undo(tl)
        out_c, in_c = TimelineOperations.roll_edit(
            track, outgoing_clip_id, incoming_clip_id, RationalTime.from_seconds(new_cut_sec, tl.fps)
        )
        tl.updated_at = utc_now_iso()
        tl.version += 1

        if self.db:
            self.db.save_timeline(tl)

        return (out_c, in_c)

    def slip_clip(
        self,
        timeline_id: UUID,
        clip_id: UUID,
        offset_sec: float
    ) -> Clip:
        """Slip edit: shifts source in/out while keeping timeline position/duration fixed."""
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        track = next((t for t in tl.tracks if any(c.clip_id == clip_id for c in t.clips)), None)
        if not track:
            raise ValueError(f"Clip {clip_id} not found")

        self._push_undo(tl)
        slipped = TimelineOperations.slip_clip(track, clip_id, RationalTime.from_seconds(offset_sec, tl.fps))
        tl.updated_at = utc_now_iso()
        tl.version += 1

        if self.db:
            self.db.save_timeline(tl)

        return slipped

    def add_transition(
        self,
        timeline_id: UUID,
        track_id: UUID,
        transition_type: TransitionType,
        start_time_sec: float,
        duration_sec: float = 1.0,
        from_clip_id: Optional[UUID] = None,
        to_clip_id: Optional[UUID] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Transition:
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        track = next((t for t in tl.tracks if t.track_id == track_id), None)
        if not track:
            raise ValueError(f"Track {track_id} not found")

        self._push_undo(tl)
        trans = Transition(
            transition_id=uuid4(),
            transition_type=transition_type,
            start_time=RationalTime.from_seconds(start_time_sec, tl.fps),
            duration=RationalTime.from_seconds(duration_sec, tl.fps),
            from_clip_id=from_clip_id,
            to_clip_id=to_clip_id,
            parameters=parameters or {}
        )
        TimelineOperations.add_transition(track, trans)
        tl.updated_at = utc_now_iso()
        tl.version += 1

        if self.db:
            self.db.save_timeline(tl)

        return trans

    def add_effect_to_clip(
        self,
        timeline_id: UUID,
        clip_id: UUID,
        effect_type: EffectType,
        parameters: Dict[str, Any]
    ) -> Effect:
        tl = self.get_timeline(timeline_id)
        if not tl:
            raise ValueError(f"Timeline {timeline_id} not found")

        track = next((t for t in tl.tracks if any(c.clip_id == clip_id for c in t.clips)), None)
        if not track:
            raise ValueError(f"Clip {clip_id} not found")

        clip = next(c for c in track.clips if c.clip_id == clip_id)
        self._push_undo(tl)

        eff = Effect(
            effect_id=uuid4(),
            effect_type=effect_type,
            parameters=parameters,
            enabled=True,
            processing_order=len(clip.effects)
        )
        TimelineOperations.add_effect(clip, eff)
        tl.updated_at = utc_now_iso()
        tl.version += 1

        if self.db:
            self.db.save_timeline(tl)

        return eff
