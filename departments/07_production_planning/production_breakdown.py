"""
Production Breakdown Service.
Transforms planned shots, scripts, and creative briefs into an actionable
dependency DAG of production tasks categorized by department and generation modality.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.planning.planning_models import (
    PlannedShot,
    ProductionBreakdown,
    ProductionScript,
    ProductionTask,
    ProductionTaskType
)

logger = logging.getLogger("studio.production_planning.breakdown")

class ProductionBreakdownService:
    def __init__(self):
        pass

    def build_breakdown(
        self,
        project_id: UUID,
        shots: List[PlannedShot],
        script: Optional[ProductionScript] = None
    ) -> ProductionBreakdown:
        """
        Compiles all planned shots into an execution DAG with explicit departmental ownership.
        """
        tasks: List[ProductionTask] = []
        shots_by_type: Dict[str, int] = {}
        total_estimated_cost = 0.0

        # Phase 1: Voiceover & Audio Recording Task
        vo_task_id = uuid4()
        vo_dur = script.estimated_spoken_duration_sec if script else 10.0
        vo_task = ProductionTask(
            task_id=vo_task_id,
            shot_id=None,
            task_type=ProductionTaskType.VOICEOVER_RECORDING,
            description=f"Record and master scratch voiceover track ({vo_dur:.1f}s)",
            assigned_department="17_subtitles_dubbing",
            status="PLANNED",
            dependencies=[],
            estimated_duration_sec=vo_dur,
            estimated_cost_usd=round(vo_dur * 0.001, 4)
        )
        tasks.append(vo_task)

        # Phase 2: Per-Shot Production Tasks
        for shot in shots:
            t_type = shot.generation_requirements
            type_str = t_type.value
            shots_by_type[type_str] = shots_by_type.get(type_str, 0) + 1

            # Estimate cost based on task type
            if t_type == ProductionTaskType.AI_VIDEO_GENERATION:
                dept = "15_ai_generation"
                cost = round(shot.estimated_duration_sec * 0.04, 3)
            elif t_type == ProductionTaskType.MOTION_GRAPHICS_CREATION:
                dept = "09_motion_graphics"
                cost = 0.0  # Local declarative Motion Canvas render
            elif t_type == ProductionTaskType.EXISTING_FOOTAGE_CONFORMANCE:
                dept = "03_media_ingestion"
                cost = 0.0
            elif t_type == ProductionTaskType.ANIMATION_2D:
                dept = "10_animation_2d"
                cost = 0.0
            elif t_type == ProductionTaskType.ANIMATION_3D:
                dept = "11_animation_3d"
                cost = 0.05
            elif t_type == ProductionTaskType.VFX_COMPOSITING:
                dept = "13_vfx_compositing"
                cost = 0.02
            else:
                dept = "08_video_editing"
                cost = 0.0

            total_estimated_cost += cost
            shot_task = ProductionTask(
                task_id=uuid4(),
                shot_id=shot.shot_id,
                task_type=t_type,
                description=f"Produce Shot {shot.shot_number}: {shot.narrative_purpose}",
                assigned_department=dept,
                status="PLANNED",
                dependencies=[vo_task_id],  # Shot visuals timed to audio
                estimated_duration_sec=shot.estimated_duration_sec,
                estimated_cost_usd=cost
            )
            tasks.append(shot_task)

        # Phase 3: Sound Design & Final Audio Mix
        sound_task = ProductionTask(
            task_id=uuid4(),
            shot_id=None,
            task_type=ProductionTaskType.SOUND_DESIGN,
            description="Sound design: foley, cinematic risers, sub-bass impacts, and EBU R128 mix",
            assigned_department="14_audio_production",
            status="PLANNED",
            dependencies=[t.task_id for t in tasks[1:]],
            estimated_duration_sec=sum(s.estimated_duration_sec for s in shots),
            estimated_cost_usd=0.0
        )
        tasks.append(sound_task)

        # Compile summaries
        required_assets = {
            "total_shots_required": len(shots),
            "voiceover_tracks": 1 if script else 0,
            "music_tracks": 1
        }
        missing_assets = {
            "unassigned_shots": [str(s.shot_id) for s in shots if not s.required_source_assets and s.generation_requirements == ProductionTaskType.EXISTING_FOOTAGE_CONFORMANCE]
        }

        risks = []
        if shots_by_type.get(ProductionTaskType.AI_VIDEO_GENERATION.value, 0) > 8:
            risks.append("High number of AI-generated shots (>8) requires strict character/lighting consistency supervision.")
        if shots_by_type.get(ProductionTaskType.VFX_COMPOSITING.value, 0) > 0:
            risks.append("VFX compositing passes require clean matte segmentation.")

        return ProductionBreakdown(
            breakdown_id=uuid4(),
            project_id=project_id,
            tasks=tasks,
            total_shots=len(shots),
            shots_by_type=shots_by_type,
            required_assets_summary=required_assets,
            missing_assets_summary=missing_assets,
            estimated_cost_usd=round(total_estimated_cost, 2),
            technical_risks=risks
        )

