"""
Department 08: Video Editing.
OpenTimelineIO multi-track editorial assembly, trimming, transitions,
effects, keyframe evaluation, blueprint execution, preview, and rendering.
"""
from .interface import IVideoEditing, VideoEditingRequest, VideoEditingResponse
from .service import VideoEditingService
from .timeline_manager import TimelineManager
from .blueprint_executor import BlueprintExecutor
from .render_engine import RenderEngine
from .preview_engine import PreviewEngine
from .sync_engine import AudioVideoSyncEngine

__all__ = [
    "IVideoEditing",
    "VideoEditingRequest",
    "VideoEditingResponse",
    "VideoEditingService",
    "TimelineManager",
    "BlueprintExecutor",
    "RenderEngine",
    "PreviewEngine",
    "AudioVideoSyncEngine"
]
