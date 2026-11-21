"""
Master Production Planning Service.
Orchestrates dependency DAG breakdowns, Mode B editing blueprints,
production feasibility analysis, and master blueprint compiling with human approval gates.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from core.assets.database import AssetDatabase
from core.assets.intelligence_models import ReferenceProfile
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
from .blueprint_manager import ProductionBlueprintManager
from .edit_planner import EditingBlueprintService
from .feasibility_evaluator import ProductionFeasibilityService
from .interface import (
    IProductionPlanning,
    ProductionPlanningRequest,
    ProductionPlanningResponse
)
from .production_breakdown import ProductionBreakdownService

logger = logging.getLogger("studio.production_planning.service")

class ProductionPlanningService(IProductionPlanning):
    def __init__(
        self,
        db: Optional[AssetDatabase] = None,
        breakdown_service: Optional[ProductionBreakdownService] = None,
        edit_planner: Optional[EditingBlueprintService] = None,
        feasibility_service: Optional[ProductionFeasibilityService] = None,
        blueprint_manager: Optional[ProductionBlueprintManager] = None
    ):
        self.db = db
        self.breakdown_service = breakdown_service or ProductionBreakdownService()
        self.edit_planner = edit_planner or EditingBlueprintService()
        self.feasibility_service = feasibility_service or ProductionFeasibilityService()
        self.blueprint_manager = blueprint_manager or ProductionBlueprintManager(db)

    def health_check(self) -> bool:
        return True

    async def execute(self, request: ProductionPlanningRequest) -> ProductionPlanningResponse:
        action = request.parameters.get("action", "build_breakdown")
        project_id = request.project_id

        if action == "build_breakdown":
            shots_data = request.parameters.get("shots", [])
            # In practical API flow, shots are retrieved or converted
            breakdown = self.breakdown_service.build_breakdown(project_id, [])
            return ProductionPlanningResponse(
                success=True,
                message="Production breakdown generated.",
                data={"tasks_count": len(breakdown.tasks), "cost_usd": breakdown.estimated_cost_usd}
            )

        return ProductionPlanningResponse(
            success=False,
            message=f"Unknown production planning action: {action}",
            data={}
        )

    def build_breakdown(
        self, project_id: UUID, shots: List[PlannedShot], script: Optional[ProductionScript] = None
    ) -> ProductionBreakdown:
        return self.breakdown_service.build_breakdown(project_id, shots, script)

    def create_edit_blueprint(
        self,
        project_id: UUID,
        target_duration_sec: float,
        source_shots: List[Dict[str, Any]],
        ref_profile: Optional[ReferenceProfile] = None,
        instructions: str = ""
    ) -> EditingBlueprint:
        blueprint = self.edit_planner.create_edit_blueprint(
            project_id, target_duration_sec, source_shots, ref_profile, instructions
        )
        if self.db:
            self.db.save_editing_blueprint(blueprint)
        return blueprint

    def evaluate_feasibility(
        self, project_id: UUID, breakdown: ProductionBreakdown, shots: List[PlannedShot]
    ) -> ProductionFeasibility:
        return self.feasibility_service.evaluate_feasibility(project_id, breakdown, shots)

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
        return self.blueprint_manager.compile_blueprint(
            project_id=project_id,
            brief=brief,
            selected_concept=selected_concept,
            script=script,
            planned_shots=planned_shots,
            storyboard=storyboard,
            characters=characters,
            environments=environments,
            props=props,
            continuity_rules=continuity_rules,
            breakdown=breakdown,
            editing_blueprint=editing_blueprint,
            feasibility=feasibility,
            version=version
        )

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
        return self.blueprint_manager.submit_approval(
            project_id, entity_type, entity_id, version, status, reviewer_notes, approved_by
        )
