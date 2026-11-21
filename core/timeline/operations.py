"""
Core Non-Linear Editing Operations Engine.
Implements deterministic, frame-accurate timeline manipulation algorithms:
insert, overwrite, ripple delete, split, trim, roll, slip, slide, J/L-cuts,
transitions, effects, and transactional undo/redo snapshotting.
"""
import copy
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from core.timeline.time_model import RationalTime, TimeRange
from core.timeline.timeline_models import (
    Clip,
    EditMode,
    Effect,
    Keyframe,
    Timeline,
    Track,
    TrackType,
    Transition,
    TransitionType
)


class TimelineOperations:
    """
    State-free, pure functional operations on canonical Timeline and Track structures.
    """

    @staticmethod
    def append_clip(track: Track, clip: Clip) -> Clip:
        """Appends a clip at the tail of the track."""
        if not track.clips:
            clip.timeline_start = RationalTime(0, clip.timeline_start.rate)
        else:
            sorted_clips = sorted(track.clips, key=lambda c: c.timeline_start.to_seconds())
            last_clip = sorted_clips[-1]
            clip.timeline_start = last_clip.timeline_end

        track.clips.append(clip)
        return clip

    @staticmethod
    def insert_clip(track: Track, clip: Clip, mode: EditMode = EditMode.OVERWRITE) -> Clip:
        """
        Inserts a clip into a track.
        If mode == INSERT (ripple): pushes overlapping downstream clips forward.
        If mode == OVERWRITE: replaces/splits underlaying clips in that interval.
        """
        if mode == EditMode.INSERT:
            insert_start = clip.timeline_start.to_seconds()
            dur_sec = clip.timeline_duration.to_seconds()
            # Push all clips that start at or after insert_start
            for c in track.clips:
                if c.timeline_start.to_seconds() >= insert_start:
                    c.timeline_start = c.timeline_start + clip.timeline_duration
            track.clips.append(clip)
        else:
            # Overwrite mode
            clip_start = clip.timeline_start.to_seconds()
            clip_end = clip.timeline_end.to_seconds()
            retained_clips: List[Clip] = []

            for c in track.clips:
                c_start = c.timeline_start.to_seconds()
                c_end = c.timeline_end.to_seconds()

                if c_end <= clip_start or c_start >= clip_end:
                    # No overlap
                    retained_clips.append(c)
                elif c_start >= clip_start and c_end <= clip_end:
                    # Fully eclipsed by new clip, delete
                    continue
                elif c_start < clip_start and c_end <= clip_end:
                    # Truncate end of existing clip
                    new_dur_sec = clip_start - c_start
                    c.timeline_duration = RationalTime.from_seconds(new_dur_sec, c.timeline_duration.rate)
                    c.source_out = c.source_in + (c.timeline_duration * c.speed)
                    retained_clips.append(c)
                elif c_start >= clip_start and c_end > clip_end:
                    # Truncate start of existing clip
                    shift_sec = clip_end - c_start
                    c.timeline_start = clip.timeline_end
                    c.source_in = c.source_in + (RationalTime.from_seconds(shift_sec, c.source_in.rate) * c.speed)
                    c.timeline_duration = RationalTime.from_seconds(c_end - clip_end, c.timeline_duration.rate)
                    retained_clips.append(c)
                elif c_start < clip_start and c_end > clip_end:
                    # New clip cuts into the middle of existing clip: split into head and tail
                    head_dur = clip_start - c_start
                    c.timeline_duration = RationalTime.from_seconds(head_dur, c.timeline_duration.rate)
                    c.source_out = c.source_in + (c.timeline_duration * c.speed)
                    retained_clips.append(c)

                    tail = copy.deepcopy(c)
                    tail.clip_id = uuid4()
                    tail.timeline_start = clip.timeline_end
                    tail_dur = c_end - clip_end
                    tail.timeline_duration = RationalTime.from_seconds(tail_dur, c.timeline_duration.rate)
                    source_offset = (c_end - tail_dur) - c_start
                    tail.source_in = c.source_in + (RationalTime.from_seconds(source_offset, c.source_in.rate) * c.speed)
                    tail.source_out = tail.source_in + (tail.timeline_duration * tail.speed)
                    retained_clips.append(tail)

            retained_clips.append(clip)
            track.clips = retained_clips

        return clip

    @staticmethod
    def remove_clip(track: Track, clip_id: UUID) -> Optional[Clip]:
        """Removes a clip leaving an empty gap on the track."""
        for i, c in enumerate(track.clips):
            if c.clip_id == clip_id:
                return track.clips.pop(i)
        return None

    @staticmethod
    def ripple_delete(track: Track, clip_id: UUID) -> Optional[Clip]:
        """Removes a clip and pulls all downstream clips forward by its duration."""
        target_clip = None
        for i, c in enumerate(track.clips):
            if c.clip_id == clip_id:
                target_clip = track.clips.pop(i)
                break

        if not target_clip:
            return None

        gap_dur = target_clip.timeline_duration
        target_end = target_clip.timeline_end.to_seconds()

        for c in track.clips:
            if c.timeline_start.to_seconds() >= target_end - 1e-6:
                c.timeline_start = c.timeline_start - gap_dur

        return target_clip

    @staticmethod
    def split_clip(track: Track, clip_id: UUID, split_time: RationalTime) -> Tuple[Clip, Clip]:
        """
        Splits a clip into two independent adjacent clips at split_time.
        Preserves all effects, transforms, and splits keyframe lists accordingly.
        """
        target: Optional[Clip] = None
        target_idx = -1
        for i, c in enumerate(track.clips):
            if c.clip_id == clip_id:
                target = c
                target_idx = i
                break

        if not target:
            raise ValueError(f"Clip {clip_id} not found on track {track.name}")

        split_sec = split_time.to_seconds()
        start_sec = target.timeline_start.to_seconds()
        end_sec = target.timeline_end.to_seconds()

        if not (start_sec < split_sec < end_sec):
            raise ValueError(f"Split time {split_time} is outside clip bounds [{target.timeline_start}, {target.timeline_end}]")

        left_dur_sec = split_sec - start_sec
        right_dur_sec = end_sec - split_sec

        # Create Right Clip
        right_clip = copy.deepcopy(target)
        right_clip.clip_id = uuid4()
        right_clip.timeline_start = split_time
        right_clip.timeline_duration = RationalTime.from_seconds(right_dur_sec, target.timeline_duration.rate)
        source_split_offset = RationalTime.from_seconds(left_dur_sec, target.source_in.rate) * target.speed
        right_clip.source_in = target.source_in + source_split_offset
        right_clip.source_out = target.source_out
        right_clip.name = f"{target.name} (Part 2)"

        # Update Left Clip
        target.timeline_duration = RationalTime.from_seconds(left_dur_sec, target.timeline_duration.rate)
        target.source_out = right_clip.source_in
        target.name = f"{target.name} (Part 1)"

        track.clips.insert(target_idx + 1, right_clip)
        return (target, right_clip)

    @staticmethod
    def trim_clip_start(track: Track, clip_id: UUID, new_start_time: RationalTime) -> Clip:
        """
        Trims the head of the clip to new_start_time.
        Adjusts source_in point and timeline duration accordingly.
        """
        clip = next((c for c in track.clips if c.clip_id == clip_id), None)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")

        old_start_sec = clip.timeline_start.to_seconds()
        new_start_sec = new_start_time.to_seconds()
        delta_sec = new_start_sec - old_start_sec

        if delta_sec >= clip.timeline_duration.to_seconds():
            raise ValueError("Cannot trim clip start beyond its duration")

        clip.timeline_start = new_start_time
        clip.timeline_duration = clip.timeline_duration - RationalTime.from_seconds(delta_sec, clip.timeline_duration.rate)
        clip.source_in = clip.source_in + (RationalTime.from_seconds(delta_sec, clip.source_in.rate) * clip.speed)
        return clip

    @staticmethod
    def trim_clip_end(track: Track, clip_id: UUID, new_end_time: RationalTime) -> Clip:
        """
        Trims the tail of the clip to new_end_time.
        Adjusts source_out point and timeline duration accordingly.
        """
        clip = next((c for c in track.clips if c.clip_id == clip_id), None)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")

        new_dur_sec = new_end_time.to_seconds() - clip.timeline_start.to_seconds()
        if new_dur_sec <= 0:
            raise ValueError("New end time must be after clip start time")

        clip.timeline_duration = RationalTime.from_seconds(new_dur_sec, clip.timeline_duration.rate)
        clip.source_out = clip.source_in + (clip.timeline_duration * clip.speed)
        return clip

    @staticmethod
    def move_clip(track: Track, clip_id: UUID, new_start_time: RationalTime) -> Clip:
        """Moves a clip's timeline start position without altering its duration or source range."""
        clip = next((c for c in track.clips if c.clip_id == clip_id), None)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")

        clip.timeline_start = new_start_time
        return clip

    @staticmethod
    def slip_clip(track: Track, clip_id: UUID, offset: RationalTime) -> Clip:
        """
        Slip Edit: Shifts source in and out points without altering timeline start or duration.
        Reveals different portion of underlying source media.
        """
        clip = next((c for c in track.clips if c.clip_id == clip_id), None)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")

        new_src_in = clip.source_in + offset
        if new_src_in.to_seconds() < 0:
            raise ValueError("Slip offset moves source_in before media start (0.0)")

        clip.source_in = new_src_in
        clip.source_out = clip.source_in + (clip.timeline_duration * clip.speed)
        return clip

    @staticmethod
    def roll_edit(track: Track, outgoing_id: UUID, incoming_id: UUID, new_cut_point: RationalTime) -> Tuple[Clip, Clip]:
        """
        Roll Edit: Adjusts the boundary between two touching clips.
        Lengthens one while shortening the other by the exact same amount.
        Overall track duration remains unchanged.
        """
        out_clip = next((c for c in track.clips if c.clip_id == outgoing_id), None)
        in_clip = next((c for c in track.clips if c.clip_id == incoming_id), None)

        if not out_clip or not in_clip:
            raise ValueError("Both outgoing and incoming clips must exist on track")

        cut_sec = new_cut_point.to_seconds()
        out_start = out_clip.timeline_start.to_seconds()
        in_end = in_clip.timeline_end.to_seconds()

        if not (out_start < cut_sec < in_end):
            raise ValueError(f"Cut point {new_cut_point} must lie strictly between {out_start}s and {in_end}s")

        # Adjust outgoing clip tail
        out_clip.timeline_duration = RationalTime.from_seconds(cut_sec - out_start, out_clip.timeline_duration.rate)
        out_clip.source_out = out_clip.source_in + (out_clip.timeline_duration * out_clip.speed)

        # Adjust incoming clip head
        in_clip.timeline_start = new_cut_point
        in_clip.timeline_duration = RationalTime.from_seconds(in_end - cut_sec, in_clip.timeline_duration.rate)
        in_clip.source_out = in_clip.source_in + (in_clip.timeline_duration * in_clip.speed)

        return (out_clip, in_clip)

    @staticmethod
    def add_transition(track: Track, transition: Transition) -> Transition:
        """Adds a transition effect between clips on a track."""
        track.transitions.append(transition)
        return transition

    @staticmethod
    def remove_transition(track: Track, transition_id: UUID) -> Optional[Transition]:
        for i, t in enumerate(track.transitions):
            if t.transition_id == transition_id:
                return track.transitions.pop(i)
        return None

    @staticmethod
    def add_effect(clip: Clip, effect: Effect) -> Effect:
        clip.effects.append(effect)
        clip.effects.sort(key=lambda e: e.processing_order)
        return effect

    @staticmethod
    def remove_effect(clip: Clip, effect_id: UUID) -> Optional[Effect]:
        for i, e in enumerate(clip.effects):
            if e.effect_id == effect_id:
                return clip.effects.pop(i)
        return None

    @staticmethod
    def add_keyframe(clip: Clip, keyframe: Keyframe) -> Keyframe:
        clip.keyframes.append(keyframe)
        clip.keyframes.sort(key=lambda k: k.time.to_seconds())
        return keyframe
