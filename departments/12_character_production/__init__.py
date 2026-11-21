"""
Department 12: Character Production
Character consistency, world continuity, reference asset management, and continuity rule auditing.
"""
from .interface import (
    CharacterProductionRequest,
    CharacterProductionResponse,
    ICharacterProduction
)
from .continuity_service import WorldContinuityService
from departments.animation_2d.characters import (
    CharacterIdentity,
    ModelSheet,
    CharacterPose,
    ExpressionType,
    PoseType,
    CharacterGenerator,
    IdentityValidator,
)

__all__ = [
    "CharacterProductionRequest",
    "CharacterProductionResponse",
    "ICharacterProduction",
    "WorldContinuityService",
    "CharacterIdentity",
    "ModelSheet",
    "CharacterPose",
    "ExpressionType",
    "PoseType",
    "CharacterGenerator",
    "IdentityValidator",
]
