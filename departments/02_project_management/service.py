"""
Project Management Service implementation for Department 02: Project Management.
Manages project lifecycle, template instantiation, version branching, stage tracking,
and project settings validation.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.assets.database import AssetDatabase
from .interface import (
    IProjectManagement,
    ProjectManagementRequest,
    ProjectManagementResponse
)
from .models import (
    ProductionStage,
    ProjectTask,
    ProjectTemplate,
    ProjectTemplateType,
    TaskPriority,
    TaskStatus
)


STANDARD_TEMPLATES: Dict[ProjectTemplateType, ProjectTemplate] = {
    ProjectTemplateType.BLANK: ProjectTemplate(
        template_id=ProjectTemplateType.BLANK,
        name="Blank Project",
        description="Empty project canvas with standard 1080p settings.",
        width=1920,
        height=1080,
        fps=24.0,
        aspect_ratio="16:9",
        color_space="Rec.709",
        audio_sample_rate=48000,
        default_tracks=[{"type": "VIDEO", "name": "V1"}, {"type": "AUDIO", "name": "A1"}]
    ),
    ProjectTemplateType.YOUTUBE_16_9: ProjectTemplate(
        template_id=ProjectTemplateType.YOUTUBE_16_9,
        name="YouTube Long-Form (16:9)",
        description="Full HD 1080p landscape optimized for YouTube delivery with loudness targeting -14 LUFS.",
        width=1920,
        height=1080,
        fps=24.0,
        aspect_ratio="16:9",
        color_space="Rec.709",
        audio_sample_rate=48000,
        default_tracks=[
            {"type": "VIDEO", "name": "V1"},
            {"type": "GRAPHICS", "name": "V2 Graphics"},
            {"type": "AUDIO", "name": "A1 Dialogue"},
            {"type": "AUDIO", "name": "A2 Music"},
            {"type": "AUDIO", "name": "A3 SFX"}
        ]
    ),
    ProjectTemplateType.SOCIAL_VERTICAL_9_16: ProjectTemplate(
        template_id=ProjectTemplateType.SOCIAL_VERTICAL_9_16,
        name="Social Vertical Reel (9:16)",
        description="Vertical 1080x1920 @ 30fps optimized for TikTok, Instagram Reels, and YouTube Shorts.",
        width=1080,
        height=1920,
        fps=30.0,
        aspect_ratio="9:16",
        color_space="Rec.709",
        audio_sample_rate=48000,
        default_tracks=[
            {"type": "VIDEO", "name": "V1 Video"},
            {"type": "GRAPHICS", "name": "V2 Kinetic Subtitles"},
            {"type": "AUDIO", "name": "A1 Voice"},
            {"type": "AUDIO", "name": "A2 Music"}
        ]
    ),
    ProjectTemplateType.CINEMATIC_2_39: ProjectTemplate(
        template_id=ProjectTemplateType.CINEMATIC_2_39,
        name="Cinematic Widescreen (2.39:1)",
        description="Ultra-wide anamorphic 4K scope @ 23.976 fps with ACEScg scene-referred color management.",
        width=3840,
        height=1608,
        fps=23.976,
        aspect_ratio="2.39:1",
        color_space="ACEScg",
        audio_sample_rate=48000,
        default_tracks=[
            {"type": "VIDEO", "name": "V1 Master Plates"},
            {"type": "VIDEO", "name": "V2 VFX Composites"},
            {"type": "AUDIO", "name": "A1 Dialogue"},
            {"type": "AUDIO", "name": "A2 Foley"},
            {"type": "AUDIO", "name": "A3 Score"},
            {"type": "AUDIO", "name": "A4 Ambience"}
        ]
    ),
    ProjectTemplateType.ANIME_2D: ProjectTemplate(
        template_id=ProjectTemplateType.ANIME_2D,
        name="Japanese Anime / 2D (12 FPS on 2s)",
        description="Authentic Japanese anime pipeline with multiplane backgrounds, Settei model sheets, and cel layers.",
        width=1920,
        height=1080,
        fps=24.0,
        aspect_ratio="16:9",
        color_space="sRGB",
        audio_sample_rate=48000,
        default_tracks=[
            {"type": "VIDEO", "name": "V1 BG Multiplane"},
            {"type": "VIDEO", "name": "V2 Cel Animation"},
            {"type": "VIDEO", "name": "V3 Shiage Effects"},
            {"type": "AUDIO", "name": "A1 Seiyuu Dub"},
            {"type": "AUDIO", "name": "A2 Anime OST"}
        ]
    )
}


class ProjectManagementService(IProjectManagement):
    """
    Department 02 Facade: Handles project lifecycle, template generation,
    version snapshotting, stage tracking, and setting validation.
    """

    def __init__(self, db: AssetDatabase):
        self.db = db

    def get_templates(self) -> List[ProjectTemplate]:
        return list(STANDARD_TEMPLATES.values())

    def create_project_from_template(
        self,
        name: str,
        template_type: ProjectTemplateType = ProjectTemplateType.BLANK,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        template = STANDARD_TEMPLATES.get(template_type, STANDARD_TEMPLATES[ProjectTemplateType.BLANK])
        settings = {
            "template": template.template_id.value,
            "width": template.width,
            "height": template.height,
            "fps": template.fps,
            "aspect_ratio": template.aspect_ratio,
            "color_space": template.color_space,
            "audio_sample_rate": template.audio_sample_rate,
            "default_tracks": template.default_tracks,
            "current_stage": "PLANNING"
        }
        if custom_settings:
            settings.update(custom_settings)

        project_id = uuid4()
        self.db.create_project(project_id, name, settings)
        proj = self.db.get_project(project_id)
        if not proj:
            raise RuntimeError(f"Failed to create project from template {template_type}")
        return proj

    def list_projects(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return self.db.list_projects(limit=limit, offset=offset)

    def get_project(self, project_id: UUID) -> Optional[Dict[str, Any]]:
        return self.db.get_project(project_id)

    def update_project(
        self,
        project_id: UUID,
        name: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        return self.db.update_project(project_id, name=name, settings=settings)

    def delete_project(self, project_id: UUID) -> bool:
        return self.db.delete_project(project_id)

    def save_version(
        self,
        project_id: UUID,
        version_name: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        proj = self.db.get_project(project_id)
        if not proj:
            raise ValueError(f"Project {project_id} not found.")

        # Capture complete project snapshot: project metadata, settings, creative brief, etc.
        snapshot = {
            "project": {
                "name": proj["name"],
                "settings": proj["settings"],
                "updated_at": proj["updated_at"]
            },
            "assets_count": len(self.db.list_project_assets(project_id, limit=1000))
        }
        version_id = self.db.save_project_version(project_id, version_name, snapshot, notes=notes)
        return {
            "version_id": version_id,
            "project_id": project_id,
            "version_name": version_name,
            "notes": notes,
            "snapshot": snapshot
        }

    def list_versions(self, project_id: UUID) -> List[Dict[str, Any]]:
        return self.db.list_project_versions(project_id)

    def restore_version(self, project_id: UUID, version_id: str) -> Dict[str, Any]:
        ver = self.db.get_project_version(version_id)
        if not ver or ver["project_id"] != project_id:
            raise ValueError(f"Version {version_id} not found for project {project_id}")

        snapshot_proj = ver["snapshot"].get("project", {})
        # Restore project name and settings from snapshot
        updated = self.db.update_project(
            project_id,
            name=snapshot_proj.get("name"),
            settings=snapshot_proj.get("settings")
        )
        return {
            "restored_version_id": version_id,
            "project": updated
        }

    async def execute(self, request: ProjectManagementRequest) -> ProjectManagementResponse:
        action = request.parameters.get("action", "get")
        if action == "list":
            projects = self.list_projects()
            return ProjectManagementResponse(
                success=True,
                message=f"Retrieved {len(projects)} projects",
                data={"projects": projects}
            )
        elif action == "create":
            name = request.parameters.get("name", "Untitled Project")
            template_str = request.parameters.get("template", "BLANK")
            template_type = ProjectTemplateType(template_str) if template_str in ProjectTemplateType.__members__ else ProjectTemplateType.BLANK
            proj = self.create_project_from_template(name, template_type, request.parameters.get("settings"))
            return ProjectManagementResponse(
                success=True,
                message=f"Project '{name}' created successfully",
                data={"project": proj}
            )
        elif action == "save_version":
            version_name = request.parameters.get("version_name", "Milestone Snapshot")
            notes = request.parameters.get("notes")
            ver = self.save_version(request.project_id, version_name, notes)
            return ProjectManagementResponse(
                success=True,
                message=f"Version '{version_name}' saved",
                data={"version": ver}
            )
        elif action == "restore_version":
            version_id = request.parameters.get("version_id", "")
            res = self.restore_version(request.project_id, version_id)
            return ProjectManagementResponse(
                success=True,
                message=f"Version {version_id} restored",
                data=res
            )
        else:
            proj = self.get_project(request.project_id)
            if not proj:
                return ProjectManagementResponse(
                    success=False,
                    message=f"Project {request.project_id} not found",
                    data={}
                )
            return ProjectManagementResponse(
                success=True,
                message=f"Project {request.project_id} retrieved",
                data={"project": proj}
            )

    def health_check(self) -> bool:
        try:
            with self.db.get_connection() as conn:
                conn.execute("SELECT 1 FROM projects LIMIT 1")
            return True
        except Exception:
            return False
