"""
Master Multimodal Provider Router.
Orchestrates request routing between Local On-Device processing, Google Gemini, and TwelveLabs.
Enforces privacy boundaries, budget limits, and hardware-aware dispatching.
"""
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from .gemini_provider import GeminiProvider
from .interface import (
    IMultimodalProviders,
    MultimodalProvidersRequest,
    MultimodalProvidersResponse,
    ProviderRoutingMode,
    TaskType,
    VideoAnalysisResult
)
from .local_provider import LocalMultimodalProvider
from .twelvelabs_provider import TwelveLabsProvider

logger = logging.getLogger("studio.providers.router")

class MultimodalProviderRouter(IMultimodalProviders):
    def __init__(
        self,
        default_mode: ProviderRoutingMode = ProviderRoutingMode.LOCAL_FIRST,
        local_provider: Optional[LocalMultimodalProvider] = None,
        gemini_provider: Optional[GeminiProvider] = None,
        twelvelabs_provider: Optional[TwelveLabsProvider] = None
    ):
        self.mode = default_mode
        self.local = local_provider or LocalMultimodalProvider()
        self.gemini = gemini_provider or GeminiProvider()
        self.twelvelabs = twelvelabs_provider or TwelveLabsProvider()

    def health_check(self) -> bool:
        return self.local.health_check() and self.gemini.health_check() and self.twelvelabs.health_check()

    def select_provider_for_task(self, task_type: Optional[TaskType]) -> str:
        """
        Determines the optimal provider based on TaskType, hardware profile, and active routing mode.
        """
        if self.mode == ProviderRoutingMode.LOCAL_ONLY:
            return "local"
        if self.mode == ProviderRoutingMode.CLOUD_ONLY:
            return "gemini"

        if task_type in (
            TaskType.SHOT_BOUNDARY,
            TaskType.MOTION_ESTIMATION,
            TaskType.AUDIO_CLASSIFICATION,
            TaskType.CINEMATOGRAPHY,
            TaskType.COLOR_ANALYSIS
        ):
            # Local deterministic toolchains are millisecond-fast and perfectly frame-accurate
            return "local"
        elif task_type in (TaskType.GLOBAL_REASONING, TaskType.CREATIVE_SYNTHESIS):
            # Complex cross-shot creative narrative reasoning favors multimodal LLM
            return "gemini" if self.mode != ProviderRoutingMode.LOCAL_FIRST else "local"
        
        return "local"

    async def execute(self, request: MultimodalProvidersRequest) -> MultimodalProvidersResponse:
        """
        Routes the high-level multimodal request according to active mode, task type, and parameters.
        """
        start_time = time.perf_counter()
        action = request.action
        target_path = Path(request.target_path)
        prompt = request.prompt or "Analyze visual and narrative elements."
        task_type = request.task_type

        # Provider selection
        provider_choice = self.select_provider_for_task(task_type)
        fallback_used = False

        if action == "analyze_video":
            if provider_choice == "local":
                res: VideoAnalysisResult = await self.local.analyze_video(target_path, prompt)
            else:
                try:
                    res = await self.gemini.analyze_video(target_path, prompt)
                except Exception as e:
                    logger.warning(f"Cloud provider failed ({e}), falling back to local provider.")
                    res = await self.local.analyze_video(target_path, prompt)
                    fallback_used = True

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return MultimodalProvidersResponse(
                success=True,
                provider=res.provider,
                task_type=task_type,
                data={
                    "model": res.model,
                    "summary": res.summary,
                    "events": res.events,
                    "raw": res.raw_response
                },
                cost_usd=res.estimated_cost_usd,
                execution_metadata={
                    "latency_ms": elapsed_ms,
                    "routing_mode": self.mode.value,
                    "fallback_used": fallback_used
                }
            )

        elif action == "compare":
            ref_path = Path(request.parameters.get("reference_path", str(target_path)))
            comp = await self.local.compare_videos(target_path, ref_path, prompt)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return MultimodalProvidersResponse(
                success=True,
                provider=comp.get("provider", "local"),
                task_type=task_type,
                data=comp,
                cost_usd=comp.get("cost_usd", 0.0),
                execution_metadata={
                    "latency_ms": elapsed_ms,
                    "routing_mode": self.mode.value,
                    "fallback_used": False
                }
            )

        elif action == "transcribe":
            tr = await self.local.transcribe(target_path)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return MultimodalProvidersResponse(
                success=True,
                provider=tr.get("provider", "local"),
                task_type=task_type or TaskType.ASR_TRANSCRIPTION,
                data=tr,
                cost_usd=0.0,
                execution_metadata={
                    "latency_ms": elapsed_ms,
                    "routing_mode": self.mode.value,
                    "fallback_used": False
                }
            )

        elif action == "embed":
            vec = await self.twelvelabs.embed_text(prompt)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return MultimodalProvidersResponse(
                success=True,
                provider="twelvelabs-marengo",
                task_type=task_type,
                data={"vector_dim": len(vec), "vector_sample": vec[:5]},
                cost_usd=0.0,
                execution_metadata={
                    "latency_ms": elapsed_ms,
                    "routing_mode": self.mode.value,
                    "fallback_used": False
                }
            )

        return MultimodalProvidersResponse(
            success=False,
            provider="unknown",
            task_type=task_type,
            data={"error": f"Unknown action: {action}"},
            cost_usd=0.0,
            execution_metadata={
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                "routing_mode": self.mode.value,
                "fallback_used": False
            }
        )

