"""
Studio Application Service implementation for Department 01: Studio Application.
Coordinates web workspace layouts, viewport streaming states, telemetry monitoring,
and UI configuration.
"""
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from core.assets.database import AssetDatabase
from .interface import (
    IStudioApplication,
    StudioApplicationRequest,
    StudioApplicationResponse
)


class StudioApplicationService(IStudioApplication):
    """
    Department 01 Facade: Coordinates the unified studio workspace,
    user preferences, layout configurations, and viewport telemetry.
    """

    def __init__(self, db: AssetDatabase, ui_dir: Optional[str] = None):
        self.db = db
        self.ui_dir = Path(ui_dir or Path(__file__).parent / "ui")
        self._user_layouts: Dict[str, Dict[str, Any]] = {}

    def get_system_telemetry(self) -> Dict[str, Any]:
        """
        Returns real-time telemetry: storage space, platform specs,
        and hardware encoder acceleration availability.
        """
        disk_usage = shutil.disk_usage(Path.cwd())
        free_gb = round(disk_usage.free / (1024 ** 3), 2)
        total_gb = round(disk_usage.total / (1024 ** 3), 2)

        is_mac = sys.platform == "darwin"
        return {
            "platform": sys.platform,
            "is_apple_silicon": is_mac,
            "videotoolbox_acceleration": is_mac,
            "storage": {
                "free_gb": free_gb,
                "total_gb": total_gb,
                "used_gb": round(disk_usage.used / (1024 ** 3), 2),
                "percent_used": round((disk_usage.used / disk_usage.total) * 100, 1)
            },
            "status": "HEALTHY",
            "active_version": "1.0.0"
        }

    def get_workspace_layout(self, workspace_id: str) -> Dict[str, Any]:
        """
        Retrieves panel layout geometry for a workspace preset.
        """
        default_layouts = {
            "creative": {"left_panel_width": 300, "right_panel_width": 360, "bottom_panel_height": 280},
            "editing": {"left_panel_width": 260, "right_panel_width": 320, "bottom_panel_height": 380},
            "color": {"left_panel_width": 220, "right_panel_width": 380, "bottom_panel_height": 320},
            "audio": {"left_panel_width": 240, "right_panel_width": 340, "bottom_panel_height": 340},
            "vfx": {"left_panel_width": 260, "right_panel_width": 360, "bottom_panel_height": 300}
        }
        return self._user_layouts.get(workspace_id, default_layouts.get(workspace_id, {"left_panel_width": 280, "right_panel_width": 320, "bottom_panel_height": 300}))

    def save_workspace_layout(self, workspace_id: str, layout_config: Dict[str, Any]) -> None:
        """
        Persists a customized panel layout configuration.
        """
        self._user_layouts[workspace_id] = layout_config

    async def execute(self, request: StudioApplicationRequest) -> StudioApplicationResponse:
        action = request.parameters.get("action", "get_telemetry")
        if action == "get_telemetry":
            data = self.get_system_telemetry()
            return StudioApplicationResponse(
                success=True,
                message="Telemetry retrieved",
                data=data
            )
        elif action == "get_layout":
            ws_id = request.parameters.get("workspace_id", "creative")
            layout = self.get_workspace_layout(ws_id)
            return StudioApplicationResponse(
                success=True,
                message=f"Layout for {ws_id} retrieved",
                data={"layout": layout}
            )
        elif action == "save_layout":
            ws_id = request.parameters.get("workspace_id", "creative")
            layout = request.parameters.get("layout", {})
            self.save_workspace_layout(ws_id, layout)
            return StudioApplicationResponse(
                success=True,
                message=f"Layout for {ws_id} saved",
                data={"layout": layout}
            )
        else:
            return StudioApplicationResponse(
                success=False,
                message=f"Unknown action {action}",
                data={}
            )

    def health_check(self) -> bool:
        """
        Verifies database and UI directory existence.
        """
        try:
            with self.db.get_connection() as conn:
                conn.execute("SELECT 1 FROM projects LIMIT 1")
            return self.ui_dir.exists()
        except Exception:
            return False
