"""
Department 21: Storage & Asset Management
Central Common Asset Registry with SHA-256 validation.
"""
from .interface import IStorageAssetManagement
from core.assets.database import (
    AssetDatabase,
    AssetRecord,
    AssetRole,
    DerivativeRecord,
    DerivativeType,
    MediaType,
    ProcessingStatus,
    TechnicalMetadata
)
from core.storage.storage_service import StorageService

__all__ = [
    "IStorageAssetManagement",
    "AssetDatabase",
    "AssetRecord",
    "AssetRole",
    "DerivativeRecord",
    "DerivativeType",
    "MediaType",
    "ProcessingStatus",
    "TechnicalMetadata",
    "StorageService"
]
