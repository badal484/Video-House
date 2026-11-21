"""
Department 15: AI Generation Package
Multi-provider router for Runway Gen-3, Kling 1.5, Wan2.1, Flux.1.
"""
from .interface import (
    IAIGeneration,
    AIGenerationRequest,
    AIGenerationResponse,
)
from .service import AIGenerationService

__all__ = [
    "IAIGeneration",
    "AIGenerationRequest",
    "AIGenerationResponse",
    "AIGenerationService",
]
