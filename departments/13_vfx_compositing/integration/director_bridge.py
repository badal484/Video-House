"""
Director VFX Bridge
Ingests planned shots and creative blueprints from Department 04 (AI Director)
and schedules executable VFX shot tasks.
"""
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..core.vfx_project_models import VFXShotTask, VFXType, VFXTaskStatus


class DirectorVFXBridge:
    """
    Translates director blueprints and shot notes into VFX shot tasks.
    """

    @staticmethod
    def extract_vfx_tasks_from_blueprint(
        project_id: str,
        planned_shots: List[Dict[str, Any]],
    ) -> List[VFXShotTask]:
        """
        Inspects planned shots for 'required_vfx' or 'vfx_notes' and instantiates VFXShotTasks.
        """
        tasks: List[VFXShotTask] = []

        for shot in planned_shots:
            shot_id = str(shot.get("shot_id", uuid4()))
            vfx_notes = shot.get("vfx_notes", "").lower()
            requires_vfx = shot.get("required_vfx", False) or bool(vfx_notes)

            if not requires_vfx:
                continue

            # Classify VFX type based on notes
            if "screen" in vfx_notes or "phone" in vfx_notes or "monitor" in vfx_notes:
                vfx_type = VFXType.SCREEN_REPLACEMENT
            elif "green" in vfx_notes or "key" in vfx_notes or "chroma" in vfx_notes:
                vfx_type = VFXType.CHROMA_KEY
            elif "remove" in vfx_notes or "clean" in vfx_notes or "wire" in vfx_notes or "inpaint" in vfx_notes:
                vfx_type = VFXType.OBJECT_REMOVAL
            elif "sky" in vfx_notes or "cloud" in vfx_notes:
                vfx_type = VFXType.SKY_REPLACEMENT
            elif "track" in vfx_notes or "callout" in vfx_notes:
                vfx_type = VFXType.TRACKED_GRAPHIC
            elif "fog" in vfx_notes or "smoke" in vfx_notes or "dust" in vfx_notes or "particle" in vfx_notes:
                vfx_type = VFXType.ATMOSPHERIC_EFFECT
            else:
                vfx_type = VFXType.MULTI_LAYER_COMPOSITE

            task = VFXShotTask(
                task_id=str(uuid4()),
                project_id=project_id,
                shot_id=shot_id,
                name=f"VFX_{shot.get('name', shot_id)}",
                vfx_type=vfx_type,
                description=shot.get("vfx_notes", f"VFX shot task for {shot_id}"),
                status=VFXTaskStatus.PENDING,
            )
            tasks.append(task)

        return tasks
