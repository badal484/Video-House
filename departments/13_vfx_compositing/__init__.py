"""
Department 13: VFX & Compositing Package
Provides node-based compositing, keying, tracking, rotoscoping, inpainting, and effects.
"""
from .interface import (
    IVFXCompositing,
    VFXCompositingRequest,
    VFXCompositingResponse,
)
from .core.graph_models import (
    PortDataType,
    BlendMode,
    VFXNodeType,
    NodePort,
    VFXNode,
    GraphEdge,
    CompositingGraph,
)
from .core.vfx_project_models import (
    VFXTaskStatus,
    VFXType,
    VFXShotTask,
    VFXProject,
)
from .core.color_space import (
    srgb_to_linear,
    linear_to_srgb,
    straight_to_premultiplied,
    premultiplied_to_straight,
    apply_green_despill,
    apply_blue_despill,
    grade_image,
)
from .tracking.feature_tracker import FeatureTracker, TrackSequence, TrackedPoint
from .tracking.planar_tracker import PlanarTracker
from .tracking.camera_solver import CameraSolver
from .keying.chroma_keyer import ChromaKeyer
from .rotoscoping.segmentation_engine import SegmentationEngine
from .rotoscoping.matte_refinement import MatteRefiner
from .cleanup.inpainting_engine import InpaintingEngine
from .effects.atmospheric import AtmosphericEffects
from .effects.cinematic_fx import CinematicEffects
from .engines.base import ICompositorEngine
from .engines.local_compositor import LocalCompositorEngine
from .engines.blender_compositor import BlenderCompositorEngine
from .engines.router import VFXEngineRouter
from .supervisor.vfx_supervisor import AIVFXSupervisor
from .supervisor.quality_checker import VFXQualityChecker
from .integration.timeline_bridge import TimelineVFXBridge
from .integration.director_bridge import DirectorVFXBridge
from .service import VFXCompositingService

__all__ = [
    "IVFXCompositing",
    "VFXCompositingRequest",
    "VFXCompositingResponse",
    "PortDataType",
    "BlendMode",
    "VFXNodeType",
    "NodePort",
    "VFXNode",
    "GraphEdge",
    "CompositingGraph",
    "VFXTaskStatus",
    "VFXType",
    "VFXShotTask",
    "VFXProject",
    "srgb_to_linear",
    "linear_to_srgb",
    "straight_to_premultiplied",
    "premultiplied_to_straight",
    "apply_green_despill",
    "apply_blue_despill",
    "grade_image",
    "FeatureTracker",
    "TrackSequence",
    "TrackedPoint",
    "PlanarTracker",
    "CameraSolver",
    "ChromaKeyer",
    "SegmentationEngine",
    "MatteRefiner",
    "InpaintingEngine",
    "AtmosphericEffects",
    "CinematicEffects",
    "ICompositorEngine",
    "LocalCompositorEngine",
    "BlenderCompositorEngine",
    "VFXEngineRouter",
    "AIVFXSupervisor",
    "VFXQualityChecker",
    "TimelineVFXBridge",
    "DirectorVFXBridge",
    "VFXCompositingService",
]
