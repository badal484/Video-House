"""
Cinematography and Shot Planning Engine.
Translates narrative scenes into granular, structured PlannedShot lists
specifying lens focal lengths, camera angles, movement vectors, lighting,
depth of field, composition rules, and generation requirements.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.assets.intelligence_models import (
    CameraAngle,
    CameraMotionType,
    ShotScale
)
from core.planning.planning_models import (
    PlannedShot,
    ProductionScript,
    ProductionTaskType,
    ScriptScene
)

logger = logging.getLogger("studio.creative_direction.shots")

class CinematographyShotPlanner:
    def __init__(self):
        pass

    def plan_shots_for_script(
        self,
        script: ProductionScript,
        visual_style: str = "Cinematic Realism"
    ) -> List[PlannedShot]:
        """
        Decomposes all scenes in the script into an ordered sequence of PlannedShot records.
        """
        all_shots: List[PlannedShot] = []
        global_shot_idx = 1

        for scene in script.scenes:
            scene_shots = self.plan_shots_for_scene(
                scene, start_index=global_shot_idx, visual_style=visual_style
            )
            all_shots.extend(scene_shots)
            global_shot_idx += len(scene_shots)

        return all_shots

    def plan_shots_for_scene(
        self,
        scene: ScriptScene,
        start_index: int = 1,
        visual_style: str = "Cinematic Realism"
    ) -> List[PlannedShot]:
        """
        Generates 2 to 4 structured cinematic shots for an individual narrative scene.
        """
        duration = scene.estimated_duration_sec
        # Target 2 to 3 shots per scene
        if duration <= 6.0:
            shot_count = 2
        elif duration <= 12.0:
            shot_count = 3
        else:
            shot_count = max(3, int(duration / 4.0))

        sec_per_shot = round(duration / shot_count, 2)
        shots: List[PlannedShot] = []

        for i in range(shot_count):
            curr_idx = start_index + i
            is_opening = (i == 0)
            is_closing = (i == shot_count - 1)

            # Editorial grammar: Opening shot is typically establishing/wide; middle is medium/close; closing is payoff/hero
            if is_opening:
                scale = ShotScale.WIDE if scene.scene_number > 1 else ShotScale.EXTREME_WIDE
                angle = CameraAngle.LOW_ANGLE if "car" in scene.action_description.lower() else CameraAngle.EYE_LEVEL
                motion = CameraMotionType.DOLLY_IN if hasattr(CameraMotionType, "DOLLY_IN") else CameraMotionType.TRACKING
                lens = "24mm"
                purpose = f"Establish {scene.location} and spatial geography."
                start_st = "Wide environmental vista with subject entering frame"
                end_st = "Subject approaches mid-ground, lighting catches contours"
                task_type = ProductionTaskType.AI_VIDEO_GENERATION
            elif is_closing:
                scale = ShotScale.MEDIUM_CLOSE_UP
                angle = CameraAngle.EYE_LEVEL
                motion = CameraMotionType.STATIC
                lens = "85mm"
                purpose = "Anchor emotional connection and deliver closing focal payoff."
                start_st = "Hero framing of key subject detail or character expression"
                end_st = "Subtle lighting flare sweeps across lens; locks into final pose"
                task_type = ProductionTaskType.MOTION_GRAPHICS_CREATION if "logo" in scene.action_description.lower() else ProductionTaskType.AI_VIDEO_GENERATION
            else:
                scale = ShotScale.MEDIUM
                angle = CameraAngle.LOW_ANGLE
                motion = CameraMotionType.PAN_LEFT
                lens = "50mm"
                purpose = f"Capture active subject movement: {scene.action_description[:60]}"
                start_st = "Profile perspective of subject in dynamic motion"
                end_st = "Subject tracks through camera focal plane"
                task_type = ProductionTaskType.AI_VIDEO_GENERATION

            shot = PlannedShot(
                shot_id=uuid4(),
                scene_id=scene.scene_id,
                shot_number=curr_idx,
                narrative_purpose=purpose,
                shot_scale=scale,
                camera_angle=angle,
                camera_motion=motion,
                lens_focal_length=lens,
                camera_position="Camera positioned 15 degrees off-axis",
                subject_action=scene.action_description[:100],
                environment_description=f"{scene.location} ({scene.time_of_day})",
                lighting_direction="High contrast directional key with subtle ambient fill",
                composition_notes="Subject placed along leading third; golden ratio framing",
                depth_of_field="f/2.0 shallow depth with smooth circular bokeh",
                focus_behavior="Sharp focus tracking subject movement",
                motion_characteristics="Smooth fluid motion without jitter",
                start_state=start_st,
                end_state=end_st,
                estimated_duration_sec=sec_per_shot,
                aspect_ratio="16:9",
                visual_style=visual_style,
                continuity_requirements=[
                    f"Match screen direction from Scene {scene.scene_number}",
                    f"Maintain {scene.time_of_day} lighting continuity"
                ],
                required_source_assets=[],
                generation_requirements=task_type
            )
            shots.append(shot)

        return shots
