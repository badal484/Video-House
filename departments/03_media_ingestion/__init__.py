"""
Department 03: Media Ingestion & Conformance
FFmpeg/FFprobe demuxing, conformance, proxy transcode, keyframe indexing.
"""
from .interface import IMediaIngestion, MediaIngestionRequest, MediaIngestionResponse
from .service import MediaIngestionService
from .metadata_extractor import MetadataExtractor
from .derivative_generator import DerivativeGenerator

__all__ = [
    "IMediaIngestion",
    "MediaIngestionRequest",
    "MediaIngestionResponse",
    "MediaIngestionService",
    "MetadataExtractor",
    "DerivativeGenerator"
]
