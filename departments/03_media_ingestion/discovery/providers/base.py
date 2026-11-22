"""
Base class for external creative resource providers.
Department: 03_media_ingestion/discovery/providers
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import DiscoveredAsset, ResourceQuery


class BaseResourceProvider(ABC):
    """
    Abstract contract for external resource providers.
    Supports pluggable discovery, metadata resolution, and download URL generation.
    """

    def __init__(self, name: str, is_enabled: bool = True):
        self.name = name
        self.is_enabled = is_enabled

    @abstractmethod
    def search(self, query: ResourceQuery) -> List[DiscoveredAsset]:
        """
        Executes a search against the provider API or endpoint.
        Returns normalized DiscoveredAsset instances.
        """
        pass

    @abstractmethod
    def get_asset_details(self, asset_id: str) -> Optional[DiscoveredAsset]:
        """
        Retrieves in-depth technical and license metadata for a specific asset.
        """
        pass
