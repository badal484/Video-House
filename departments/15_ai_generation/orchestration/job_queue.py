"""
Asynchronous Generation Job Queue & Execution Engine
Department 15: 15_ai_generation
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from ..core.generation_models import (
    GenerationRequest,
    GenerationResult,
    JobStatus,
    ValidationStatus,
)
from ..providers.registry import ProviderRegistry
from ..router.generation_router import GenerationRouter
from ..router.cost_estimator import GenerationBudgetManager


class GenerationJobQueue:
    """Non-blocking asynchronous generation job execution manager."""

    def __init__(
        self,
        registry: ProviderRegistry,
        router: GenerationRouter,
        budget_mgr: GenerationBudgetManager,
    ):
        self.registry = registry
        self.router = router
        self.budget_mgr = budget_mgr
        self._jobs: Dict[str, GenerationResult] = {}
        self._idempotency_cache: Dict[str, str] = {}  # idempotency_key -> job_id
        self._active_tasks: Dict[str, asyncio.Task] = {}

    def get_job(self, job_id: str) -> Optional[GenerationResult]:
        return self._jobs.get(job_id)

    def list_jobs(self, project_id: Optional[str] = None) -> List[GenerationResult]:
        if project_id:
            return [j for j in self._jobs.values() if j.project_id == project_id]
        return list(self._jobs.values())

    async def submit_request(self, request: GenerationRequest) -> GenerationResult:
        """
        Submits generation request into the job queue.
        Enforces idempotency and budget checks.
        """
        # 1. Idempotency Check
        idemp_key = request.idempotency_key or request.compute_idempotency_key()
        if idemp_key in self._idempotency_cache:
            existing_job_id = self._idempotency_cache[idemp_key]
            existing_job = self._jobs.get(existing_job_id)
            if existing_job and existing_job.status in (JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.SUCCEEDED):
                return existing_job

        # 2. Provider Routing
        try:
            provider = self.router.route_request(request)
        except Exception as e:
            failed_res = GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id="none",
                model_id="none",
                error_message=str(e),
            )
            self._jobs[failed_res.job_id] = failed_res
            return failed_res

        # 3. Budget Check
        cost_est = provider.estimate_cost(request)
        request.estimated_cost_usd = cost_est
        budget_ok, budget_msg = self.budget_mgr.check_budget(request.project_id, cost_est)
        if not budget_ok:
            blocked_res = GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.BLOCKED,
                provider_id=provider.provider_id,
                model_id=request.preferred_model or "default",
                error_message=budget_msg,
            )
            self._jobs[blocked_res.job_id] = blocked_res
            return blocked_res

        # 4. Dispatch Generation Task
        res = await provider.submit_job(request)
        self._jobs[res.job_id] = res
        self._idempotency_cache[idemp_key] = res.job_id

        # Commit spend
        if res.status == JobStatus.SUCCEEDED:
            self.budget_mgr.record_spend(request.project_id, res.actual_cost_usd)

        return res

    async def cancel_job(self, job_id: str) -> bool:
        """Cancels an active job."""
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job_id in self._active_tasks:
            self._active_tasks[job_id].cancel()

        provider = self.registry.get_provider(job.provider_id)
        if provider:
            await provider.cancel_job(job_id)

        job.status = JobStatus.CANCELLED
        return True
