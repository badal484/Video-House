"""
Department 05: Multimodal Providers
Unified provider adapters for Google Gemini, TwelveLabs, Qwen2.5-VL,
and Local On-Device processing.
"""
from .interface import (
    IEmbeddingProvider,
    IMultimodalProviders,
    ISpeechProvider,
    IVideoUnderstandingProvider,
    MultimodalProvidersRequest,
    MultimodalProvidersResponse,
    ProviderRoutingMode,
    VideoAnalysisResult
)
from .gemini_provider import GeminiProvider
from .twelvelabs_provider import TwelveLabsProvider
from .local_provider import LocalMultimodalProvider
from .router import MultimodalProviderRouter

__all__ = [
    "IEmbeddingProvider",
    "IMultimodalProviders",
    "ISpeechProvider",
    "IVideoUnderstandingProvider",
    "MultimodalProvidersRequest",
    "MultimodalProvidersResponse",
    "ProviderRoutingMode",
    "VideoAnalysisResult",
    "GeminiProvider",
    "TwelveLabsProvider",
    "LocalMultimodalProvider",
    "MultimodalProviderRouter"
]
