"""
Render Plan Compiler for Department 19.
Transforms approved creative timelines into ordered execution DAGs,
resolving stage dependencies and estimating duration and compute costs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..core.models import RenderPlan, RenderPlanStage
from .preflight import PreflightValidator


class RenderPlanCompiler:
    """Compiles project timelines and creative operations into executable RenderPlans."""

    @classmethod
    def compile_plan(
        cls,
        project_id: UUID,
        project_metadata: Dict[str, Any],
        render_profile_id: str = "youtube_1080p",
        timeline_id: Optional[UUID] = None,
    ) -> RenderPlan:
        """
        Validates project preflight and builds the stage execution DAG.
        Raises ValueError if preflight contains blocking errors.
        """
        # Step 1: Preflight inspection
        passed, issues = PreflightValidator.validate_project(project_metadata)
        if not passed:
            blocking_descs = [i["description"] for i in issues if i["is_blocking"]]
            raise ValueError(
                f"Render plan compilation rejected due to preflight errors: {'; '.join(blocking_descs)}"
            )

        stages: List[RenderPlanStage] = []
        total_duration = 0.0
        total_cost = 0.0

        # Stage 1: DCC Creative Renders (Motion Canvas, 3D, VFX) if present
        dcc_tasks = project_metadata.get("dcc_tasks", [])
        if dcc_tasks:
            stage_dcc = RenderPlanStage(
                stage_id="stage_01_dcc",
                name="DCC Motion Graphics, 3D & VFX Rendering",
                stage_type="DCC",
                dependencies=[],
                estimated_duration_sec=len(dcc_tasks) * 2.5,
                estimated_cost_usd=0.0,
            )
            stages.append(stage_dcc)
            total_duration += stage_dcc.estimated_duration_sec

        # Stage 2: Audio Production & DSP Mastering
        stage_audio = RenderPlanStage(
            stage_id="stage_02_audio",
            name="Audio Stems Separation & EBU R128 Master Mix",
            stage_type="AUDIO",
            dependencies=["stage_01_dcc"] if dcc_tasks else [],
            estimated_duration_sec=3.0,
            estimated_cost_usd=0.0,
        )
        stages.append(stage_audio)
        total_duration += stage_audio.estimated_duration_sec

        # Stage 3: Timeline Intermediate Master Rasterization
        stage_timeline = RenderPlanStage(
            stage_id="stage_03_timeline",
            name="OpenTimelineIO Intermediate Frame Rasterization",
            stage_type="TIMELINE",
            dependencies=[s.stage_id for s in stages],
            estimated_duration_sec=4.0,
            estimated_cost_usd=0.0,
        )
        stages.append(stage_timeline)
        total_duration += stage_timeline.estimated_duration_sec

        # Stage 4: Target Encoding (FFmpeg / VideoToolbox)
        stage_encode = RenderPlanStage(
            stage_id="stage_04_encode",
            name=f"Distribution Encoding ({render_profile_id})",
            stage_type="ENCODE",
            dependencies=["stage_03_timeline"],
            estimated_duration_sec=2.0,
            estimated_cost_usd=0.0,
        )
        stages.append(stage_encode)
        total_duration += stage_encode.estimated_duration_sec

        # Stage 5: Automated Quality Control Gate
        stage_qc = RenderPlanStage(
            stage_id="stage_05_qc",
            name="Automated Video, Audio, Color & Subtitle QC",
            stage_type="QC",
            dependencies=["stage_04_encode"],
            estimated_duration_sec=1.5,
            estimated_cost_usd=0.0,
        )
        stages.append(stage_qc)
        total_duration += stage_qc.estimated_duration_sec

        # Stage 6: Delivery Packaging & Manifest
        stage_pkg = RenderPlanStage(
            stage_id="stage_06_package",
            name="Delivery Packaging, Stems, Checksums & Manifest",
            stage_type="PACKAGE",
            dependencies=["stage_05_qc"],
            estimated_duration_sec=0.5,
            estimated_cost_usd=0.0,
        )
        stages.append(stage_pkg)
        total_duration += stage_pkg.estimated_duration_sec

        # Cloud cost check
        requires_approval = False
        approval_reason = None
        if total_cost > 1.00:
            requires_approval = True
            approval_reason = f"Estimated cloud cost (${total_cost:.2f}) exceeds $1.00 safety ceiling."

        return RenderPlan(
            project_id=project_id,
            timeline_id=timeline_id,
            render_profile_id=render_profile_id,
            stages=stages,
            estimated_duration_sec=round(total_duration, 2),
            estimated_cost_usd=round(total_cost, 2),
            requires_approval=requires_approval,
            approval_reason=approval_reason,
        )
