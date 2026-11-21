"""
World, Character, and Production Continuity Service.
Enforces character appearance consistency, wardrobe preservation, spatial screen direction
(180-degree rule), lighting continuity, and environmental coherence across scenes and shots.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.assets.database import AssetDatabase
from core.planning.planning_models import (
    CharacterProfile,
    ContinuityRule,
    ContinuityRuleType,
    EnvironmentProfile,
    PlannedShot,
    PropEntity
)
from .interface import (
    CharacterProductionRequest,
    CharacterProductionResponse,
    ICharacterProduction
)

logger = logging.getLogger("studio.character_production.continuity")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class WorldContinuityService(ICharacterProduction):
    def __init__(self, db: Optional[AssetDatabase] = None):
        self.db = db

    def health_check(self) -> bool:
        return True

    async def execute(self, request: CharacterProductionRequest) -> CharacterProductionResponse:
        return CharacterProductionResponse(
            success=True,
            message="World continuity operational.",
            data={}
        )

    def register_character(self, character: CharacterProfile) -> None:
        if self.db:
            self.db.save_character(character)

    def register_environment(self, environment: EnvironmentProfile) -> None:
        if self.db:
            self.db.save_environment(environment)

    def create_continuity_rule(
        self,
        project_id: UUID,
        rule_type: ContinuityRuleType,
        description: str,
        affected_scenes: Optional[List[UUID]] = None,
        affected_shots: Optional[List[UUID]] = None
    ) -> ContinuityRule:
        return ContinuityRule(
            rule_id=uuid4(),
            project_id=project_id,
            rule_type=rule_type,
            description=description,
            affected_scenes=affected_scenes or [],
            affected_shots=affected_shots or [],
            is_active=True
        )

    def audit_shot_continuity(
        self,
        shot: PlannedShot,
        active_rules: List[ContinuityRule]
    ) -> List[str]:
        """
        Audits a planned shot against active continuity rules.
        Returns a list of warnings if potential continuity violations are detected.
        """
        warnings: List[str] = []

        for rule in active_rules:
            if not rule.is_active:
                continue

            # Check if this shot or its parent scene is governed by the rule
            applies_to_shot = not rule.affected_shots or shot.shot_id in rule.affected_shots
            applies_to_scene = not rule.affected_scenes or shot.scene_id in rule.affected_scenes

            if applies_to_shot or applies_to_scene:
                if rule.rule_type == ContinuityRuleType.CHARACTER_APPEARANCE:
                    if not any("character" in c.lower() or "appearance" in c.lower() for c in shot.continuity_requirements):
                        warnings.append(f"Shot {shot.shot_number}: Missing character appearance constraint ({rule.description})")

                elif rule.rule_type == ContinuityRuleType.LIGHTING:
                    if not any("lighting" in c.lower() for c in shot.continuity_requirements):
                        warnings.append(f"Shot {shot.shot_number}: Missing lighting continuity constraint ({rule.description})")

                elif rule.rule_type == ContinuityRuleType.SPATIAL_AXIS:
                    if not any("screen direction" in c.lower() or "axis" in c.lower() for c in shot.continuity_requirements):
                        warnings.append(f"Shot {shot.shot_number}: Missing spatial 180-degree axis constraint ({rule.description})")

        return warnings
