"""
Master Creative Director Service.
Orchestrates brief interpretation, concept generation, scriptwriting,
cinematography planning, storyboard structuring, and reference style transfer.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from core.assets.database import AssetDatabase
from core.assets.intelligence_models import ReferenceProfile
from core.planning.planning_models import (
    CharacterProfile,
    CreativeBrief,
    CreativeConcept,
    EnvironmentProfile,
    PlannedShot,
    ProductionScript,
    StoryboardFrame
)
from .brief_interpreter import CreativeBriefService
from .concept_generator import ConceptGenerationService
from .interface import (
    CreativeDirectionRequest,
    CreativeDirectionResponse,
    ICreativeDirection
)
from .script_engine import ScriptAndNarrativeService
from .shot_planner import CinematographyShotPlanner
from .storyboard_planner import StoryboardPlanningService
from .style_interpreter import ReferenceMatchingDegree, ReferenceStyleInterpreter

logger = logging.getLogger("studio.creative_direction.service")

class CreativeDirectorService(ICreativeDirection):
    def __init__(
        self,
        db: Optional[AssetDatabase] = None,
        brief_service: Optional[CreativeBriefService] = None,
        concept_service: Optional[ConceptGenerationService] = None,
        script_service: Optional[ScriptAndNarrativeService] = None,
        shot_planner: Optional[CinematographyShotPlanner] = None,
        storyboard_planner: Optional[StoryboardPlanningService] = None,
        style_interpreter: Optional[ReferenceStyleInterpreter] = None
    ):
        self.db = db
        self.brief_service = brief_service or CreativeBriefService()
        self.concept_service = concept_service or ConceptGenerationService()
        self.script_service = script_service or ScriptAndNarrativeService()
        self.shot_planner = shot_planner or CinematographyShotPlanner()
        self.storyboard_planner = storyboard_planner or StoryboardPlanningService()
        self.style_interpreter = style_interpreter or ReferenceStyleInterpreter()

    def health_check(self) -> bool:
        return True

    async def execute(self, request: CreativeDirectionRequest) -> CreativeDirectionResponse:
        """
        Executes a targeted creative direction task (parse_brief, generate_concepts, develop_script, plan_shots).
        """
        action = request.parameters.get("action", "parse_brief")
        project_id = request.project_id

        if action == "parse_brief":
            brief, questions = self.brief_service.parse_brief(project_id, request.parameters)
            if self.db:
                self.db.save_creative_brief(brief)
            return CreativeDirectionResponse(
                success=True,
                message="Creative brief parsed and structured successfully.",
                data={
                    "brief": {
                        "brief_id": str(brief.brief_id),
                        "project_name": brief.project_name,
                        "production_type": brief.production_type.value,
                        "genre": brief.genre,
                        "target_duration_sec": brief.target_duration_sec,
                        "assumptions": brief.assumptions
                    },
                    "clarification_questions": questions
                }
            )

        elif action == "generate_concepts":
            brief_dict = self.db.get_creative_brief(project_id) if self.db else None
            if not brief_dict:
                brief, _ = self.brief_service.parse_brief(project_id, request.parameters)
            else:
                brief, _ = self.brief_service.parse_brief(project_id, brief_dict)

            concepts = self.concept_service.generate_concepts(brief, count=3)
            if self.db:
                self.db.save_creative_concepts(concepts)
            return CreativeDirectionResponse(
                success=True,
                message=f"Generated {len(concepts)} distinct creative concepts.",
                data={"concepts": [{
                    "concept_id": str(c.concept_id),
                    "name": c.name,
                    "premise": c.creative_premise,
                    "complexity": c.production_complexity.value
                } for c in concepts]}
            )

        return CreativeDirectionResponse(
            success=False,
            message=f"Unknown creative direction action: {action}",
            data={}
        )

    def parse_brief(
        self, project_id: UUID, raw_input: Dict[str, Any]
    ) -> Tuple[CreativeBrief, List[str]]:
        brief, questions = self.brief_service.parse_brief(project_id, raw_input)
        if self.db:
            self.db.save_creative_brief(brief)
        return brief, questions

    def generate_concepts(
        self, brief: CreativeBrief, count: int = 3
    ) -> List[CreativeConcept]:
        concepts = self.concept_service.generate_concepts(brief, count=count)
        if self.db:
            self.db.save_creative_concepts(concepts)
        return concepts

    def develop_script(
        self, brief: CreativeBrief, concept: Optional[CreativeConcept] = None
    ) -> ProductionScript:
        script = self.script_service.generate_script(brief, concept)
        if self.db:
            self.db.save_script(script)
        return script

    def plan_shots(
        self, script: ProductionScript, visual_style: str = "Cinematic Realism"
    ) -> List[PlannedShot]:
        shots = self.shot_planner.plan_shots_for_script(script, visual_style=visual_style)
        if self.db:
            self.db.save_planned_shots(shots)
        return shots

    def plan_storyboard(
        self,
        shots: List[PlannedShot],
        characters: Optional[List[CharacterProfile]] = None,
        environments: Optional[List[EnvironmentProfile]] = None
    ) -> List[StoryboardFrame]:
        frames = self.storyboard_planner.plan_storyboard(shots, characters, environments)
        if self.db:
            self.db.save_storyboard_frames(frames)
        return frames

    def apply_reference_style(
        self,
        brief: CreativeBrief,
        ref_profile: ReferenceProfile,
        degree: ReferenceMatchingDegree = ReferenceMatchingDegree.STRONG_MATCHING
    ) -> CreativeBrief:
        updated = self.style_interpreter.apply_reference_to_brief(brief, ref_profile, degree)
        if self.db:
            self.db.save_creative_brief(updated)
        return updated

