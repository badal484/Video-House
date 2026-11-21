"""
Generation Request Router
Department 15: 15_ai_generation
"""
from __future__ import annotations

from typing import Optional

from ..core.generation_models import (
    GenerationModality,
    GenerationRequest,
)
from ..providers.base import BaseGenerationProvider
from ..providers.registry import ProviderRegistry


class GenerationRouter:
    """Capability-based generation router selecting optimal providers."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def route_request(self, request: GenerationRequest) -> BaseGenerationProvider:
        """
        Determines the most suitable provider to execute the generation request.
        """
        # 1. User preferred provider check
        if request.preferred_provider:
            p = self.registry.get_provider(request.preferred_provider)
            if p and p.spec.is_active:
                valid, _ = p.validate_request(request)
                if valid:
                    return p

        # 2. Get all compatible providers
        compatible = self.registry.get_compatible_providers(request)
        if not compatible:
            # Fallback to local mock engine if available
            mock = self.registry.get_provider("mock_local_engine")
            if mock:
                return mock
            raise ValueError(f"No compatible generation provider found for modality '{request.modality.value}'.")

        # 3. Preference ranking:
        # If API key required and available, prefer commercial; else fall back to mock or open
        for p in compatible:
            if not p.spec.is_mock:
                # Check if API key is configured
                if hasattr(p, "api_key") and getattr(p, "api_key", None):
                    return p

        # Default to first compatible provider (e.g. mock or local)
        return compatible[0]
