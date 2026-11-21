"""
Department 10: 2D Animation, Anime & Character Studio Package
Provides traditional cel, anime pipeline, cut-out puppetry, skeletal rigging, and character identity.
"""
from .interface import (
    IAnimation2D,
    Animation2DRequest,
    Animation2DResponse,
)
from .core.models import (
    AnimationType,
    ExposureRate,
    TrackType,
    DrawingExposure,
    AnimationKeyframe,
    AnimationTrack,
    Camera2D,
    AnimationShot,
    CharacterInstance,
    AnimationScene,
    AnimationProject,
)
from .characters.character_models import (
    IdentityStatus,
    ExpressionType,
    PoseType,
    CharacterIdentity,
    CharacterPose,
    ModelSheet,
)
from .characters.character_generator import CharacterGenerator
from .characters.identity_validator import IdentityValidator
from .rigging.bone_models import BoneNode, CharacterRig
from .rigging.ik_solver import IKSolver2D
from .rigging.puppet_animator import PuppetAnimator
from .anime_pipeline.anime_models import (
    CelLayerType,
    FramingType,
    AnimeCelLayer,
    TimingChart,
    AnimeLayout,
)
from .anime_pipeline.cel_shader import AnimeCelShader
from .anime_pipeline.multiplane_background import MultiplaneBackgroundEngine
from .ai_generation.motion_retargeting import MotionRetargeter
from .ai_generation.facial_animator import VisemeType, FacialAnimator
from .ai_generation.inbetween_engine import InBetweenEngine
from .asset_library.asset_library import AssetCategory, AnimationAsset, AnimationAssetLibrary
from .rendering.vector_renderer import VectorAnimationRenderer
from .rendering.raster_renderer import RasterAnimationRenderer
from .rendering.sprite_sheet_packager import SpriteSheetPackager
from .integrations.timeline_adapter import TimelineAnimationAdapter
from .integrations.director_bridge import DirectorAnimationBridge
from .service import Animation2DService

__all__ = [
    "IAnimation2D",
    "Animation2DRequest",
    "Animation2DResponse",
    "AnimationType",
    "ExposureRate",
    "TrackType",
    "DrawingExposure",
    "AnimationKeyframe",
    "AnimationTrack",
    "Camera2D",
    "AnimationShot",
    "CharacterInstance",
    "AnimationScene",
    "AnimationProject",
    "IdentityStatus",
    "ExpressionType",
    "PoseType",
    "CharacterIdentity",
    "CharacterPose",
    "ModelSheet",
    "CharacterGenerator",
    "IdentityValidator",
    "BoneNode",
    "CharacterRig",
    "IKSolver2D",
    "PuppetAnimator",
    "CelLayerType",
    "FramingType",
    "AnimeCelLayer",
    "TimingChart",
    "AnimeLayout",
    "AnimeCelShader",
    "MultiplaneBackgroundEngine",
    "MotionRetargeter",
    "VisemeType",
    "FacialAnimator",
    "InBetweenEngine",
    "AssetCategory",
    "AnimationAsset",
    "AnimationAssetLibrary",
    "VectorAnimationRenderer",
    "RasterAnimationRenderer",
    "SpriteSheetPackager",
    "TimelineAnimationAdapter",
    "DirectorAnimationBridge",
    "Animation2DService",
]
