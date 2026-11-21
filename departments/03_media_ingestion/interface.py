"""
Interface definition for Department 03: Media Ingestion & Conformance.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from core.assets.database import AssetRecord, AssetRole

class MediaIngestionRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    file_path: Optional[str] = Field(None, description="Local file path for direct import")
    display_name: Optional[str] = None
    roles: List[AssetRole] = Field(default_factory=lambda: [AssetRole.SOURCE_FOOTAGE])
    parameters: Dict[str, Any] = Field(default_factory=dict)

class MediaIngestionResponse(BaseModel):
    success: bool
    message: str
    asset_id: Optional[UUID] = None
    data: Dict[str, Any] = Field(default_factory=dict)

class IMediaIngestion(ABC):
    """
    Abstract contract for Department 03: Media Ingestion & Conformance
    """
    @abstractmethod
    async def import_local_file(
        self,
        project_id: UUID,
        source_path: Path,
        display_name: Optional[str] = None,
        roles: Optional[List[AssetRole]] = None
    ) -> AssetRecord:
        """Imports an existing local file into the project asset registry."""
        pass

    @abstractmethod
    async def import_stream(
        self,
        project_id: UUID,
        stream: BinaryIO,
        filename: str,
        display_name: Optional[str] = None,
        roles: Optional[List[AssetRole]] = None
    ) -> AssetRecord:
        """Streams uploaded binary data directly into project storage and registers it."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling (FFmpeg, FFprobe) is ready."""
        pass
