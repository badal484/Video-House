"""
Central Provider & Model Registry
Department 15: 15_ai_generation
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .base import BaseGenerationProvider
from .mock_provider import MockLocalProvider
from .runway_adapter import RunwayAdapter
from .kling_adapter import KlingAdapter
from .flux_adapter import FluxAdapter
from .wan_adapter import WanAdapter
from .elevenlabs_adapter import ElevenLabsAdapter
from ..core.generation_models import (
    GenerationModality,
    GenerationRequest,
    ModelSpec,
    ProviderSpec,
)


class ProviderRegistry:
    """Manages all registered AI generation providers and models."""

    def __init__(self, register_defaults: bool = True):
        self._providers: Dict[str, BaseGenerationProvider] = {}
        self._models: Dict[str, ModelSpec] = {}

        if register_defaults:
            self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Registers built-in mock and commercial cloud adapters."""
        self.register_provider(MockLocalProvider())
        self.register_provider(RunwayAdapter())
        self.register_provider(KlingAdapter())
        self.register_provider(FluxAdapter())
        self.register_provider(WanAdapter())
        self.register_provider(ElevenLabsAdapter())

    def register_provider(self, provider: BaseGenerationProvider) -> None:
        self._providers[provider.provider_id] = provider

    def get_provider(self, provider_id: str) -> Optional[BaseGenerationProvider]:
        return self._providers.get(provider_id)

    def list_providers(self, modality: Optional[GenerationModality] = None) -> List[ProviderSpec]:
        """Returns specs for all active providers, optionally filtered by modality."""
        providers = []
        for p in self._providers.values():
            if not p.spec.is_active:
                continue
            if modality and not p.supports_modality(modality):
                continue
            providers.append(p.spec)
        return providers

    def get_compatible_providers(self, request: GenerationRequest) -> List[BaseGenerationProvider]:
        """Finds all active providers that can satisfy the generation request."""
        compatible = []
        for p in self._providers.values():
            if not p.spec.is_active:
                continue
            valid, _ = p.validate_request(request)
            if valid:
                compatible.append(p)
        return compatible

    def register_model(self, model: ModelSpec) -> None:
        self._models[model.model_id] = model

    def get_model(self, model_id: str) -> Optional[ModelSpec]:
        return self._models.get(model_id)

    def list_models(self, modality: Optional[GenerationModality] = None) -> List[ModelSpec]:
        if modality:
            return [m for m in self._models.values() if m.modality == modality]
        return list(self._models.values())
