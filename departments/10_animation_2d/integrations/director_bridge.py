"""
Director Animation Bridge
Translates Department 04 PlannedShot records and storyboards into executable
AnimationScene and AnimationShot specifications.
"""
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..core.models import (
    AnimationScene,
    AnimationShot,
    CharacterInstance,
    AnimationTrack,
    TrackType,
    Camera2D,
)


class DirectorAnimationBridge:
    """
    Bridges AI Director narrative blueprints with 2D animation production tasks.
    """

    @staticmethod
    def compile_planned_shot_to_animation_shot(
        planned_shot: Dict[str, Any],
        fps: float = 24.0,
    ) -> AnimationShot:
        """
        Translates a Part 04 PlannedShot dict into a concrete AnimationShot.
        """
        shot_id = str(planned_shot.get("shot_id", uuid4()))
        name = planned_shot.get("name", f"Shot_{shot_id[:6]}")
        dur_sec = float(planned_shot.get("duration_seconds", 2.0))
        dur_frames = int(round(dur_sec * fps))

        camera_type = planned_shot.get("camera_movement", "STATIC")
        cam = Camera2D(camera_id=f"cam_{shot_id[:6]}")
        if "zoom" in camera_type.lower():
            cam.zoom = 1.25

        tracks = [
            AnimationTrack(
                track_id=str(uuid4()),
                name="Character_Genga",
                track_type=TrackType.DRAWING,
            ),
            AnimationTrack(
                track_id=str(uuid4()),
                name="Background_Layout",
                track_type=TrackType.BACKGROUND,
            ),
        ]

        return AnimationShot(
            shot_id=shot_id,
            name=name,
            duration_frames=dur_frames,
            fps=fps,
            camera=cam,
            tracks=tracks,
            layout_notes=planned_shot.get("visual_prompt", ""),
        )
