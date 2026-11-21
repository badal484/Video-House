"""
Interface definition for Department 21: Storage & Asset Management.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from core.assets.database import (
    AssetRecord,
    AssetRole,
    DerivativeRecord,
    MediaType,
    ProcessingStatus,
    TechnicalMetadata
)

class IStorageAssetManagement(ABC):
    """
    Abstract contract for Department 21: Storage & Asset Management
    """
    @abstractmethod
    def get_asset(self, asset_id: UUID) -> Optional[AssetRecord]:
        """Retrieves asset metadata record."""
        pass

    @abstractmethod
    def list_project_assets(
        self,
        project_id: UUID,
        media_type: Optional[MediaType] = None,
        role: Optional[AssetRole] = None,
        status: Optional[ProcessingStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AssetRecord]:
        """Lists assets for a project with optional filtering and pagination."""
        pass

    @abstractmethod
    def get_technical_metadata(self, asset_id: UUID) -> Optional[TechnicalMetadata]:
        """Retrieves extracted technical stream metadata."""
        pass

    @abstractmethod
    def get_derivatives(self, asset_id: UUID) -> List[DerivativeRecord]:
        """Retrieves generated proxies, previews, and audio tracks."""
        pass

    @abstractmethod
    def delete_asset(self, asset_id: UUID) -> bool:
        """Deletes asset and removes files if not locked by dependencies."""
        pass

    @abstractmethod
    def get_storage_usage(self, project_id: UUID) -> int:
        """Calculates total disk storage used by a project in bytes."""
        pass
