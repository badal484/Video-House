"""
Video Editing Service.
Department 08 master service implementing the IVideoEditing abstract interface.
Provides high-level orchestration for project creation, timeline manipulations,
blueprint execution, OTIO interchange, and preview/final rendering.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from core.assets.database import AssetDatabase
from core.timeline.otio_adapter import OTIOAdapter
from core.timeline.time_model import RationalTime
from core.timeline.timeline_models import EditingProject, Timeline
from .blueprint_executor import BlueprintExecutor
from .interface import IVideoEditing, VideoEditingRequest, VideoEditingResponse
from .preview_engine import PreviewEngine
from .render_engine import RenderEngine
from .sync_engine import AudioVideoSyncEngine
from .timeline_manager import TimelineManager

logger = logging.getLogger("studio.video_editing.service")


class VideoEditingService(IVideoEditing):
    """
    Department 08 Master Implementation.
    """

    def __init__(self, db: Optional[AssetDatabase] = None):
        self.db = db
        self.manager = TimelineManager(db)
        self.renderer = RenderEngine(db)
        self.previewer = PreviewEngine(db, self.renderer)
        self.executor = BlueprintExecutor(db, self.manager)
        self.sync_engine = AudioVideoSyncEngine()

    def health_check(self) -> bool:
        """Verifies underlying tooling (FFmpeg, OTIO, Python libraries) is healthy."""
        try:
            import opentimelineio as otio
            import subprocess
            res = subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return "ffmpeg version" in res.stdout.decode()
        except Exception as e:
            logger.error(f"Video editing health check failed: {e}")
            return False

    async def execute(self, request: VideoEditingRequest) -> VideoEditingResponse:
        """
        Executes editorial tasks (create project, execute blueprint, render, export OTIO).
        """
        project_id = request.project_id
        params = request.parameters
        action = params.get("action", "CREATE_TIMELINE")

        try:
            if action == "EXECUTE_BLUEPRINT":
                bp_data = params.get("blueprint", {})
                tl = self.executor.execute_blueprint(project_id, bp_data)
                return VideoEditingResponse(
                    success=True,
                    message="Editing blueprint executed successfully.",
                    data={"timeline": tl.to_dict()}
                )

            elif action == "RENDER_FINAL":
                tl_id = UUID(str(params["timeline_id"]))
                output_path = params.get("output_path", f"temp/renders/{tl_id}.mp4")
                tl = self.manager.get_timeline(tl_id)
                if not tl:
                    raise ValueError(f"Timeline {tl_id} not found")
                job = self.renderer.render_timeline(tl, output_path, is_preview=False)
                return VideoEditingResponse(
                    success=True,
                    message="Final render completed.",
                    data={"render_job": job.__dict__}
                )

            elif action == "RENDER_PREVIEW":
                tl_id = UUID(str(params["timeline_id"]))
                tl = self.manager.get_timeline(tl_id)
                if not tl:
                    raise ValueError(f"Timeline {tl_id} not found")
                job = self.previewer.generate_timeline_preview(tl)
                return VideoEditingResponse(
                    success=True,
                    message="Preview render ready.",
                    data={"render_job": job.__dict__}
                )

            elif action == "EXPORT_OTIO":
                tl_id = UUID(str(params["timeline_id"]))
                output_path = params.get("output_path", f"temp/interchange/{tl_id}.otio")
                tl = self.manager.get_timeline(tl_id)
                if not tl:
                    raise ValueError(f"Timeline {tl_id} not found")
                path = OTIOAdapter.export_otio_json(tl, output_path)
                return VideoEditingResponse(
                    success=True,
                    message="OTIO interchange exported successfully.",
                    data={"output_path": path}
                )

            else:
                # Default: create timeline
                tl = self.manager.create_timeline(project_id, name=params.get("name", "Master Timeline"))
                return VideoEditingResponse(
                    success=True,
                    message="Timeline initialized.",
                    data={"timeline": tl.to_dict()}
                )

        except Exception as e:
            logger.error(f"Editing execution failed: {e}")
            return VideoEditingResponse(
                success=False,
                message=str(e),
                data={}
            )
