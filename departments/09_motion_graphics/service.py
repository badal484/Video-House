"""
Motion Graphics Service Implementation.
Concrete implementation of IMotionGraphics for Department 09.
"""
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional
from uuid import UUID

from .interface import (
    IMotionGraphics, MotionGraphicsRequest, MotionGraphicsResponse
)
from .presets.preset_registry import PresetRegistry
from .renderers.router import MotionRendererRouter
from .integration.timeline_adapter import TimelineMotionAdapter
from .core.design_validator import DesignValidator
from core.assets.database import AssetDatabase
from core.storage.storage_service import StorageService


class MotionGraphicsService(IMotionGraphics):
    """
    Production service orchestrating motion design, preset instantiation,
    validation, rendering, and timeline placement.
    """

    def __init__(
        self,
        db: Optional[AssetDatabase] = None,
        storage: Optional[StorageService] = None
    ):
        self.db = db or AssetDatabase()
        self.storage = storage or StorageService(self.db)
        self.presets = PresetRegistry()
        self.router = MotionRendererRouter()
        self.timeline_adapter = TimelineMotionAdapter(self.db, self.storage)

    async def execute(self, request: MotionGraphicsRequest) -> MotionGraphicsResponse:
        """
        Executes a motion graphics task based on the request parameters.
        Supported modes:
        - 'instantiate_preset': Creates a composition from a preset.
        - 'render_composition': Renders composition to video file.
        - 'insert_to_timeline': Renders and adds to an existing timeline track.
        """
        try:
            params = request.parameters
            mode = params.get("mode", "instantiate_preset")
            project_id = str(request.project_id)

            if mode == "instantiate_preset":
                preset_id = params.get("preset_id", "preset_title_cinematic_hero")
                preset_params = params.get("preset_parameters", {})
                preset_params["project_id"] = project_id
                comp = self.presets.instantiate(preset_id, preset_params)

                val_result = DesignValidator.validate_composition(comp)

                return MotionGraphicsResponse(
                    success=True,
                    message=f"Preset '{preset_id}' instantiated successfully.",
                    data={
                        "composition": comp.to_dict(),
                        "validation": val_result
                    }
                )

            elif mode == "render_composition":
                from .core.composition_models import MotionComposition
                comp_dict = params.get("composition")
                if not comp_dict:
                    return MotionGraphicsResponse(success=False, message="Missing 'composition' in parameters.")

                comp = MotionComposition.from_dict(comp_dict)
                codec = params.get("codec", "prores_ks")
                ext = "mov" if codec == "prores_ks" else "webm"
                storage_root = str(getattr(self.storage, "root_storage", getattr(self.storage, "base_dir", "assets")))
                out_dir = os.path.join(storage_root, project_id, "derivatives", "motion_graphics")
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, f"{comp.composition_id}.{ext}")

                rendered_path = self.router.render(comp, out_path)

                return MotionGraphicsResponse(
                    success=True,
                    message="Motion graphics composition rendered successfully.",
                    data={"output_path": rendered_path, "composition_id": comp.composition_id}
                )

            elif mode == "insert_to_timeline":
                from .core.composition_models import MotionComposition
                comp_dict = params.get("composition")
                timeline_id = params.get("timeline_id")
                if not comp_dict or not timeline_id:
                    return MotionGraphicsResponse(success=False, message="Missing 'composition' or 'timeline_id'.")

                comp = MotionComposition.from_dict(comp_dict)
                clip = self.timeline_adapter.render_and_insert_to_timeline(
                    composition=comp,
                    timeline_id=timeline_id,
                    target_track_name=params.get("track_name", "V3 - Graphics"),
                    codec=params.get("codec", "prores_ks")
                )

                return MotionGraphicsResponse(
                    success=True,
                    message=f"Composition rendered and inserted onto timeline '{timeline_id}'.",
                    data={"clip_id": clip.clip_id, "asset_id": clip.asset_id}
                )

            return MotionGraphicsResponse(
                success=False,
                message=f"Unknown motion graphics execution mode: '{mode}'"
            )

        except Exception as e:
            return MotionGraphicsResponse(
                success=False,
                message=f"Motion graphics execution failed: {str(e)}"
            )

    def health_check(self) -> bool:
        """Verifies FFmpeg is available and PIL is functional."""
        try:
            res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return res.returncode == 0
        except Exception:
            return False
