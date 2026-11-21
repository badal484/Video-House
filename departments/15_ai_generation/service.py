"""
Department 15 Service Implementation: AI Generation
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from .interface import (
    IAIGeneration,
    AIGenerationRequest,
    AIGenerationResponse,
)
from .core.generation_models import (
    GenerationModality,
    GenerationRequest,
    JobStatus,
)
from .providers.registry import ProviderRegistry
from .router.generation_router import GenerationRouter
from .router.cost_estimator import GenerationBudgetManager
from .orchestration.job_queue import GenerationJobQueue
from .approval.approval_gate import ApprovalGateManager
from .prompts.prompt_compiler import PromptCompiler, StructuredPromptDimensions


class AIGenerationService(IAIGeneration):
    """
    Department 15 Service managing multi-provider generative AI workflows,
    prompt compilation, queue execution, quality control, and budget firewalls.
    """

    def __init__(self, output_root: str = "temp/generation_scratch"):
        self.output_root = output_root
        os.makedirs(self.output_root, exist_ok=True)

        self.registry = ProviderRegistry(register_defaults=True)
        self.router = GenerationRouter(self.registry)
        self.budget_mgr = GenerationBudgetManager()
        self.job_queue = GenerationJobQueue(self.registry, self.router, self.budget_mgr)
        self.approval_gate = ApprovalGateManager()

    async def execute(self, request: AIGenerationRequest) -> AIGenerationResponse:
        params = request.parameters
        action = params.get("action", "submit_job")

        try:
            if action == "submit_job":
                modality_str = params.get("modality", "TEXT_TO_IMAGE").upper()
                modality = GenerationModality[modality_str] if modality_str in GenerationModality.__members__ else GenerationModality.TEXT_TO_IMAGE
                
                gen_req = GenerationRequest(
                    project_id=str(request.project_id),
                    shot_id=params.get("shot_id"),
                    modality=modality,
                    preferred_provider=params.get("preferred_provider"),
                    preferred_model=params.get("preferred_model"),
                    raw_prompt=params.get("prompt", "Cinematic creative generation"),
                    aspect_ratio=params.get("aspect_ratio", "16:9"),
                    duration_sec=float(params.get("duration_sec", 5.0)),
                )
                
                # Check approval gate
                req_approval, reason = self.approval_gate.requires_approval(gen_req)
                if req_approval:
                    ticket = self.approval_gate.create_ticket(gen_req, reason)
                    return AIGenerationResponse(
                        success=False,
                        message=f"Generation held for human approval: {reason}",
                        data={"ticket": ticket.model_dump(), "status": "BLOCKED"},
                    )

                result = await self.job_queue.submit_request(gen_req)
                return AIGenerationResponse(
                    success=(result.status == JobStatus.SUCCEEDED),
                    message=f"Generation job {result.job_id} finished with status '{result.status.value}'.",
                    data=result.to_dict(),
                    produced_asset_ids=[UUID(a) for a in result.output_asset_ids if len(a) == 36],
                )

            elif action == "poll_job":
                job_id = params.get("job_id", "")
                job = self.job_queue.get_job(job_id)
                if not job:
                    return AIGenerationResponse(success=False, message=f"Job '{job_id}' not found.")
                return AIGenerationResponse(
                    success=True,
                    message=f"Job '{job_id}' status: {job.status.value}",
                    data=job.to_dict(),
                )

            elif action == "compile_prompt":
                dims_data = params.get("dimensions", {})
                dims = StructuredPromptDimensions(**dims_data)
                provider = params.get("provider_id", "runway_gen3")
                pos, neg = PromptCompiler.compile_for_provider(dims, provider)
                return AIGenerationResponse(
                    success=True,
                    message="Prompt compiled successfully.",
                    data={"compiled_positive_prompt": pos, "compiled_negative_prompt": neg},
                )

            elif action == "budget_status":
                status = self.budget_mgr.get_budget_status(str(request.project_id))
                return AIGenerationResponse(
                    success=True,
                    message="Budget status retrieved.",
                    data=status,
                )

            return AIGenerationResponse(
                success=False,
                message=f"Unknown generation action: '{action}'.",
            )

        except Exception as e:
            return AIGenerationResponse(
                success=False,
                message=f"AI generation service error: {str(e)}",
            )

    def health_check(self) -> bool:
        """Verifies active providers are registered and operational."""
        return len(self.registry.list_providers()) > 0
