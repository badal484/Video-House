"""
Storyboard Planning Service.
Compiles PlannedShot lists into structured StoryboardFrame specifications
connecting shots, narrative beats, character references, composition guidelines,
and visual prompt generation blueprints for downstream image engines.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.planning.planning_models import (
    ApprovalStatus,
    CharacterProfile,
    EnvironmentProfile,
    PlannedShot,
    StoryboardFrame
)

logger = logging.getLogger("studio.creative_direction.storyboard")

class StoryboardPlanningService:
    def __init__(self):
        pass

    def plan_storyboard(
        self,
        shots: List[PlannedShot],
        characters: Optional[List[CharacterProfile]] = None,
        environments: Optional[List[EnvironmentProfile]] = None
    ) -> List[StoryboardFrame]:
        """
        Synthesizes a storyboard frame specification for each planned shot.
        """
        frames: List[StoryboardFrame] = []
        char_map = {c.name: c for c in (characters or [])}
        env_map = {e.name: e for e in (environments or [])}

        for order, shot in enumerate(shots, start=1):
            # Formulate structured prompt specification for downstream visual generation
            prompt_spec = (
                f"Film still, cinematic {shot.visual_style}. "
                f"{shot.shot_scale.value.lower().replace('_', ' ')}, "
                f"{shot.camera_angle.value.lower().replace('_', ' ')}. "
                f"{shot.subject_action}. {shot.environment_description}. "
                f"{shot.lighting_direction}. Shot on {shot.lens_focal_length} lens, "
                f"{shot.depth_of_field}. 8k resolution, color graded, masterpiece."
            )

            frame = StoryboardFrame(
                frame_id=uuid4(),
                shot_id=shot.shot_id,
                scene_id=shot.scene_id,
                frame_order=order,
                visual_prompt_spec=prompt_spec,
                visual_description=f"Frame {order}: {shot.narrative_purpose} ({shot.start_state} -> {shot.end_state})",
                character_references=[c.name for c in (characters or [])],
                environment_references=[shot.environment_description],
                camera_composition=shot.composition_notes,
                lighting_direction=shot.lighting_direction,
                continuity_notes="; ".join(shot.continuity_requirements),
                approval_status=ApprovalStatus.DRAFT,
                image_asset_id=None
            )
            frames.append(frame)

        return frames

