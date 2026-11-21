"""
Rigging package exports for Department 10: 2D Animation.
"""
from .bone_models import BoneNode, CharacterRig
from .ik_solver import IKSolver2D
from .puppet_animator import PuppetAnimator

__all__ = [
    "BoneNode",
    "CharacterRig",
    "IKSolver2D",
    "PuppetAnimator",
]

