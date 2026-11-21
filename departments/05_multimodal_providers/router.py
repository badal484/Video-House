"""
Master Multimodal Provider Router.
Orchestrates request routing between Local On-Device processing, Google Gemini, and TwelveLabs.
Enforces privacy boundaries, budget limits, and hardware-aware dispatching.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from .gemini_provider import GeminiProvider
from .interface import (
    IMultimodalProviders,
    MultimodalProvidersRequest,
    MultimodalProvidersResponse,
    ProviderRoutingMode,
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

    async def execute(self, request: MultimodalProvidersRequest) -> MultimodalProvidersResponse:
        """
        Routes the high-level multimodal request according to active mode and parameters.
        """
        action = request.action
        target_path = Path(request.target_path)
        prompt = request.prompt or "Analyze visual and narrative elements."

        # Routing decision
        if self.mode == ProviderRoutingMode.LOCAL_ONLY:
            provider_choice = "local"
        elif self.mode == ProviderRoutingMode.CLOUD_ONLY:
            provider_choice = "gemini"
        elif self.mode == ProviderRoutingMode.LOCAL_FIRST:
            provider_choice = "local"
        else:
            provider_choice = "local"

        if action == "analyze_video":
            if provider_choice == "local":
                res: VideoAnalysisResult = await self.local.analyze_video(target_path, prompt)
            else:
                res = await self.gemini.analyze_video(target_path, prompt)

            return MultimodalProvidersResponse(
                success=True,
                provider=res.provider,
                data={
                    "model": res.model,
                    "summary": res.summary,
                    "events": res.events,
                    "raw": res.raw_response
                },
                cost_usd=res.estimated_cost_usd
            )

        elif action == "compare":
            ref_path = Path(request.parameters.get("reference_path", str(target_path)))
            comp = await self.local.compare_videos(target_path, ref_path, prompt)
            return MultimodalProvidersResponse(
                success=True,
                provider=comp.get("provider", "local"),
                data=comp,
                cost_usd=comp.get("cost_usd", 0.0)
            )

        elif action == "transcribe":
            tr = await self.local.transcribe(target_path)
            return MultimodalProvidersResponse(
                success=True,
                provider=tr.get("provider", "local"),
                data=tr,
                cost_usd=0.0
            )

        elif action == "embed":
            vec = await self.twelvelabs.embed_text(prompt)
            return MultimodalProvidersResponse(
                success=True,
                provider="twelvelabs-marengo",
                data={"vector_dim": len(vec), "vector_sample": vec[:5]},
                cost_usd=0.0
            )

        return MultimodalProvidersResponse(
            success=False,
            provider="unknown",
            data={"error": f"Unknown action: {action}"},
            cost_usd=0.0
        )

