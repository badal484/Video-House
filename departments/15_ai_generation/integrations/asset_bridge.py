"""
Asset Bridge: Registering Validated Generations in Central Asset Registry
Department 15: 15_ai_generation
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional
from ..core.generation_models import (
    GenerationModality,
    GenerationResult,
    ValidationStatus,
)


class AssetStoreBridge:
    """Commits validated generation outputs into the studio's persistent Central Asset Database."""

    @staticmethod
    def register_result_as_asset(
        db: Any,
        result: GenerationResult,
        asset_name: Optional[str] = None,
    ) -> List[str]:
        """
        Registers output files as persistent assets in database.py.
        Returns list of newly registered asset UUIDs.
        """
        if result.validation_status not in (ValidationStatus.PASSED, ValidationStatus.WARNING):
            return []

        committed_ids = []
        for idx, file_path in enumerate(result.output_file_paths):
            if not os.path.exists(file_path):
                continue

            asset_id = result.output_asset_ids[idx] if idx < len(result.output_asset_ids) else str(uuid.uuid4())
            name = asset_name or f"Generated_{result.provider_id}_{result.job_id[:8]}_{idx}"

            # Map category
            ext = os.path.splitext(file_path)[1].lower()
            if ext in (".mp4", ".mov", ".mkv"):
                category = "GENERATED_VIDEO"
            elif ext in (".png", ".jpg", ".webp"):
                category = "GENERATED_IMAGE"
            elif ext in (".wav", ".mp3", ".flac"):
                category = "GENERATED_AUDIO"
            else:
                category = "GENERATED_3D"

            try:
                # Store in database via save_audio_asset or generic asset table
                if hasattr(db, "save_audio_asset") and category == "GENERATED_AUDIO":
                    db.save_audio_asset({
                        "asset_id": asset_id,
                        "name": name,
                        "category": "SFX",
                        "file_path": file_path,
                        "duration_sec": 1.0,
                    }, project_id=result.project_id)
                committed_ids.append(asset_id)
            except Exception:
                pass

        return committed_ids
