"""
Interface definition for Department: 02_project_management
Project state, version branching, target delivery profiles.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ProjectManagementRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ProjectManagementResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IProjectManagement(ABC):
    """
    Abstract contract for Department 02_project_management: ProjectManagement
    """
    @abstractmethod
    async def execute(self, request: ProjectManagementRequest) -> ProjectManagementResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
