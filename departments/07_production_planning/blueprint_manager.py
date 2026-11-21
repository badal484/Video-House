"""
Production Blueprint Manager and Approval Gatekeeper.
Compiles versioned, schema-validated master ProductionBlueprint documents
connecting Project → Brief → Concepts → Script → Scenes → Shots → Storyboard →
Continuity → Breakdown → Feasibility → Human Approvals.
"""
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.assets.database import AssetDatabase
from core.planning.planning_models import (
    ApprovalStatus,
    CharacterProfile,
    ContinuityRule,
    CreativeApproval,
    CreativeBrief,
    CreativeConcept,
    EditingBlueprint,
    EnvironmentProfile,
    PlannedShot,
    PlanningEntityType,
    ProductionBreakdown,
    ProductionBlueprint,
    ProductionFeasibility,
    ProductionScript,
    PropEntity,
    StoryboardFrame
)

logger = logging.getLogger("studio.production_planning.blueprint")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ProductionBlueprintManager:
    def __init__(self, db: Optional[AssetDatabase] = None):
        self.db = db

    def compile_blueprint(
        self,
        project_id: UUID,
        brief: CreativeBrief,
        selected_concept: Optional[CreativeConcept] = None,
        script: Optional[ProductionScript] = None,
        planned_shots: Optional[List[PlannedShot]] = None,
        storyboard: Optional[List[StoryboardFrame]] = None,
        characters: Optional[List[CharacterProfile]] = None,
        environments: Optional[List[EnvironmentProfile]] = None,
        props: Optional[List[PropEntity]] = None,
        continuity_rules: Optional[List[ContinuityRule]] = None,
        breakdown: Optional[ProductionBreakdown] = None,
        editing_blueprint: Optional[EditingBlueprint] = None,
        feasibility: Optional[ProductionFeasibility] = None,
        version: int = 1
    ) -> ProductionBlueprint:
        """
        Synthesizes all creative and planning assets into a unified, versioned blueprint.
        Evaluates approval status to determine readiness for downstream production engines.
        """
        approvals: List[CreativeApproval] = []
        if self.db:
            app_dicts = self.db.get_creative_approvals(project_id)
            for a in app_dicts:
                approvals.append(CreativeApproval(
                    approval_id=a["approval_id"],
                    project_id=a["project_id"],
                    entity_type=PlanningEntityType(a["entity_type"]),
                    entity_id=a["entity_id"],
                    version=a["version"],
                    status=ApprovalStatus(a["status"]),
                    reviewer_notes=a["reviewer_notes"],
                    approved_by=a["approved_by"],
                    approved_at=a["approved_at"]
                ))

        # Check production readiness: Must have approved script or edit plan, and no rejections
        has_approved_plan = any(
            a.status == ApprovalStatus.APPROVED and a.entity_type in [
                PlanningEntityType.SCRIPT, PlanningEntityType.EDITING_BLUEPRINT, PlanningEntityType.PRODUCTION_BLUEPRINT
            ]
            for a in approvals
        )
        has_rejection = any(
            a.status in [ApprovalStatus.REJECTED, ApprovalStatus.REVISION_REQUESTED]
            for a in approvals
        )
        is_ready = has_approved_plan and not has_rejection

        blueprint = ProductionBlueprint(
            blueprint_id=uuid4(),
            project_id=project_id,
            version=version,
            brief=brief,
            selected_concept=selected_concept,
            script=script,
            planned_shots=planned_shots or [],
            storyboard=storyboard or [],
            characters=characters or [],
            environments=environments or [],
            props=props or [],
            continuity_rules=continuity_rules or [],
            breakdown=breakdown,
            editing_blueprint=editing_blueprint,
            feasibility=feasibility,
            approvals=approvals,
            is_ready_for_production=is_ready,
            created_at=utc_now_iso()
        )

        if self.db:
            self.db.save_production_blueprint(blueprint)

        return blueprint

    def submit_approval(
        self,
        project_id: UUID,
        entity_type: PlanningEntityType,
        entity_id: UUID,
        version: int,
        status: ApprovalStatus,
        reviewer_notes: str = "",
        approved_by: str = "human_director"
    ) -> CreativeApproval:
        """
        Records a human creative approval or rejection checkpoint in the asset registry.
        """
        approval = CreativeApproval(
            approval_id=uuid4(),
            project_id=project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            version=version,
            status=status,
            reviewer_notes=reviewer_notes,
            approved_by=approved_by if status == ApprovalStatus.APPROVED else None,
            approved_at=utc_now_iso() if status == ApprovalStatus.APPROVED else None
        )
        if self.db:
            self.db.save_creative_approval(approval)
        return approval

