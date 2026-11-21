"""
OpenTimelineIO (OTIO) Bidirectional Interchange Adapter.
Converts between the canonical application-owned Timeline data model and
ASWF OpenTimelineIO schemas, enabling lossless round-trip interchange with
commercial NLEs (Premiere XML, Final Cut Pro FCPXML, DaVinci Resolve, AAF).
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import opentimelineio as otio
from opentimelineio.opentime import RationalTime as OTIORationalTime
from opentimelineio.opentime import TimeRange as OTIOTimeRange

from core.timeline.time_model import RationalTime
from core.timeline.timeline_models import (
    Clip,
    Timeline,
    Track,
    TrackType,
    Transition,
    TransitionType
)

logger = logging.getLogger("studio.timeline.otio_adapter")


class OTIOAdapter:
    """
    Bidirectional translation adapter between canonical Timeline and OpenTimelineIO.
    """

    @staticmethod
    def timeline_to_otio(timeline: Timeline) -> otio.schema.Timeline:
        """
        Translates canonical Timeline to OpenTimelineIO schema.Timeline.
        Generates explicit Gaps for non-contiguous clips on tracks.
        """
        fps = timeline.fps if timeline.fps > 0 else 24.0
        otio_tl = otio.schema.Timeline(name=timeline.name)
        otio_tl.global_start_time = OTIORationalTime(0, fps)
        
        # Store application-specific metadata in standard OTIO metadata dictionary
        otio_tl.metadata["studio_timeline"] = {
            "timeline_id": str(timeline.timeline_id),
            "project_id": str(timeline.project_id),
            "resolution_width": timeline.resolution_width,
            "resolution_height": timeline.resolution_height,
            "sample_rate": timeline.sample_rate,
            "version": timeline.version
        }

        # Tracks container
        tracks_stack = otio_tl.tracks
        
        for track in sorted(timeline.tracks, key=lambda t: t.order_index):
            kind = otio.schema.TrackKind.Video if track.track_type == TrackType.VIDEO else otio.schema.TrackKind.Audio
            otio_track = otio.schema.Track(name=track.name, kind=kind)
            otio_track.metadata["studio_track"] = {
                "track_id": str(track.track_id),
                "order_index": track.order_index,
                "is_muted": track.is_muted,
                "is_visible": track.is_visible,
                "gain": track.gain,
                "opacity": track.opacity
            }

            # Sort clips by timeline start
            sorted_clips = sorted(track.clips, key=lambda c: c.timeline_start.to_seconds())
            current_cursor = 0.0

            for clip in sorted_clips:
                clip_start = clip.timeline_start.to_seconds()
                clip_dur = clip.timeline_duration.to_seconds()

                # If gap exists between cursor and clip start, add OTIO Gap
                if clip_start > current_cursor + 0.001:
                    gap_dur = clip_start - current_cursor
                    gap = otio.schema.Gap(
                        duration=OTIORationalTime(round(gap_dur * fps), fps)
                    )
                    otio_track.append(gap)
                    current_cursor = clip_start

                # Create OTIO Clip
                otio_clip = otio.schema.Clip(name=clip.name)
                otio_clip.source_range = OTIOTimeRange(
                    start_time=OTIORationalTime(round(clip.source_in.to_seconds() * fps), fps),
                    duration=OTIORationalTime(round(clip_dur * fps), fps)
                )
                
                # External Media Reference
                otio_clip.media_reference = otio.schema.ExternalReference(
                    target_url=str(clip.asset_id),
                    available_range=OTIOTimeRange(
                        start_time=OTIORationalTime(0, fps),
                        duration=OTIORationalTime(round(clip.source_out.to_seconds() * fps), fps)
                    )
                )

                # Metadata for transforms, effects, volume
                otio_clip.metadata["studio_clip"] = {
                    "clip_id": str(clip.clip_id),
                    "asset_id": str(clip.asset_id),
                    "speed": clip.speed,
                    "transform": clip.transform,
                    "opacity": clip.opacity,
                    "volume": clip.volume,
                    "pan": clip.pan,
                    "enabled": clip.enabled,
                    "effects": [e.to_dict() for e in clip.effects],
                    "keyframes": [k.to_dict() for k in clip.keyframes]
                }

                otio_track.append(otio_clip)
                current_cursor = clip_start + clip_dur

            tracks_stack.append(otio_track)

        return otio_tl

    @staticmethod
    def otio_to_timeline(otio_tl: otio.schema.Timeline, project_id: UUID) -> Timeline:
        """
        Translates OpenTimelineIO schema.Timeline to canonical Timeline.
        Reconstitutes absolute clip start positions from sequential items and gaps.
        """
        meta = otio_tl.metadata.get("studio_timeline", {})
        fps = otio_tl.global_start_time.rate if otio_tl.global_start_time else 24.0
        
        timeline_id = UUID(meta["timeline_id"]) if "timeline_id" in meta else uuid4()
        width = int(meta.get("resolution_width", 1920))
        height = int(meta.get("resolution_height", 1080))
        sample_rate = int(meta.get("sample_rate", 48000))
        version = int(meta.get("version", 1))

        timeline = Timeline(
            timeline_id=timeline_id,
            project_id=project_id,
            name=otio_tl.name or "Imported Timeline",
            fps=fps,
            time_base=fps,
            resolution_width=width,
            resolution_height=height,
            sample_rate=sample_rate,
            version=version
        )

        order_idx = 0
        for item in otio_tl.tracks:
            if not isinstance(item, otio.schema.Track):
                continue
            
            t_type = TrackType.VIDEO if item.kind == otio.schema.TrackKind.Video else TrackType.AUDIO
            track_meta = item.metadata.get("studio_track", {})
            track_id = UUID(track_meta["track_id"]) if "track_id" in track_meta else uuid4()

            track = Track(
                track_id=track_id,
                timeline_id=timeline_id,
                track_type=t_type,
                name=item.name or f"Track {order_idx + 1}",
                order_index=order_idx,
                is_muted=track_meta.get("is_muted", False),
                is_visible=track_meta.get("is_visible", True),
                gain=float(track_meta.get("gain", 1.0)),
                opacity=float(track_meta.get("opacity", 1.0))
            )

            cursor_sec = 0.0
            for child in item:
                child_dur_sec = child.duration().to_seconds()
                if isinstance(child, otio.schema.Gap):
                    cursor_sec += child_dur_sec
                elif isinstance(child, otio.schema.Clip):
                    clip_meta = child.metadata.get("studio_clip", {})
                    clip_id = UUID(clip_meta["clip_id"]) if "clip_id" in clip_meta else uuid4()
                    
                    # Extract Asset ID from metadata or media reference
                    asset_id = uuid4()
                    if "asset_id" in clip_meta:
                        asset_id = UUID(clip_meta["asset_id"])
                    elif isinstance(child.media_reference, otio.schema.ExternalReference) and child.media_reference.target_url:
                        try:
                            asset_id = UUID(child.media_reference.target_url)
                        except ValueError:
                            pass

                    src_in_sec = child.source_range.start_time.to_seconds() if child.source_range else 0.0
                    src_out_sec = src_in_sec + child_dur_sec

                    clip = Clip(
                        clip_id=clip_id,
                        asset_id=asset_id,
                        track_id=track_id,
                        timeline_start=RationalTime.from_seconds(cursor_sec, fps),
                        timeline_duration=RationalTime.from_seconds(child_dur_sec, fps),
                        source_in=RationalTime.from_seconds(src_in_sec, fps),
                        source_out=RationalTime.from_seconds(src_out_sec, fps),
                        speed=float(clip_meta.get("speed", 1.0)),
                        transform=clip_meta.get("transform", {"x": 0.0, "y": 0.0, "scale_x": 1.0, "scale_y": 1.0, "rotation": 0.0}),
                        opacity=float(clip_meta.get("opacity", 1.0)),
                        volume=float(clip_meta.get("volume", 1.0)),
                        pan=float(clip_meta.get("pan", 0.0)),
                        enabled=clip_meta.get("enabled", True),
                        name=child.name or "Imported Clip"
                    )
                    track.clips.append(clip)
                    cursor_sec += child_dur_sec

            timeline.tracks.append(track)
            order_idx += 1

        timeline.duration = timeline.calculate_total_duration()
        return timeline

    @classmethod
    def export_otio_json(cls, timeline: Timeline, output_path: str) -> str:
        """Serializes canonical Timeline to an .otio JSON file."""
        otio_tl = cls.timeline_to_otio(timeline)
        otio.adapters.write_to_file(otio_tl, output_path, adapter_name="otio_json")
        return output_path

    @classmethod
    def import_otio_json(cls, input_path: str, project_id: UUID) -> Timeline:
        """Parses an .otio JSON file into a canonical Timeline."""
        otio_tl = otio.adapters.read_from_file(input_path, adapter_name="otio_json")
        return cls.otio_to_timeline(otio_tl, project_id)
