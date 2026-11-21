"""
Director Bridge: Compiling AI Director ProductionBlueprints into GenerationRequests
Department 15: 15_ai_generation
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..core.generation_models import (
    GenerationModality,
    GenerationRequest,
    ReferenceAssetBinding,
    ReferenceCategory,
)
from ..prompts.prompt_compiler import PromptCompiler, StructuredPromptDimensions


class DirectorGenerationBridge:
    """Translates high-level Director blueprints and planned shots into concrete GenerationRequests."""

    @classmethod
    def compile_planned_shots_to_requests(
        cls,
        blueprint: Dict[str, Any],
        project_id: str,
    ) -> List[GenerationRequest]:
        """
        Parses planned shots from a ProductionBlueprint and builds a list of ready-to-dispatch requests.
        """
        requests = []
        scenes = blueprint.get("scenes", [])

        for sc in scenes:
            scene_id = sc.get("scene_id", "scene_1")
            shots = sc.get("planned_shots", sc.get("shots", []))

            for sh in shots:
                shot_id = sh.get("shot_id", "shot_1")
                prompt_text = sh.get("visual_prompt", sh.get("description", "Cinematic scene"))
                dur = float(sh.get("duration_sec", 4.0))

                # Compile structured dimensions
                dims = StructuredPromptDimensions(
                    subject=sh.get("subject", prompt_text),
                    character_identity=sh.get("character_name"),
                    environment=sh.get("environment"),
                    composition=sh.get("framing", "medium shot"),
                    camera_movement=sh.get("camera_movement", "static"),
                    lighting=sh.get("lighting", "natural cinematic"),
                    visual_style=blueprint.get("visual_style", "cinematic photorealism"),
                    aspect_ratio=blueprint.get("aspect_ratio", "16:9"),
                )

                # Determine modality: if reference image present -> IMAGE_TO_VIDEO, else TEXT_TO_VIDEO
                refs = []
                ref_img = sh.get("storyboard_image_asset_id") or sh.get("reference_image_asset_id")
                if ref_img:
                    refs.append(ReferenceAssetBinding(
                        asset_id=str(ref_img),
                        category=ReferenceCategory.COMPOSITION,
                        weight=1.0,
                    ))
                    modality = GenerationModality.IMAGE_TO_VIDEO
                else:
                    modality = GenerationModality.TEXT_TO_VIDEO

                compiled_pos, compiled_neg = PromptCompiler.compile_for_provider(
                    dimensions=dims,
                    provider_id="runway_gen3",
                    modality=modality,
                )

                req = GenerationRequest(
                    project_id=project_id,
                    scene_id=scene_id,
                    shot_id=shot_id,
                    modality=modality,
                    raw_prompt=prompt_text,
                    compiled_prompt=compiled_pos,
                    negative_prompt=compiled_neg,
                    reference_assets=refs,
                    duration_sec=dur,
                    aspect_ratio=blueprint.get("aspect_ratio", "16:9"),
                )
                req.compute_idempotency_key()
                requests.append(req)

        return requests
