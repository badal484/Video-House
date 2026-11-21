"""Voice talent assignment and biometric consent management for Department 17."""
from .consent_manager import ConsentManager
from .voice_assigner import VoiceAssignmentManager

__all__ = ["ConsentManager", "VoiceAssignmentManager"]
