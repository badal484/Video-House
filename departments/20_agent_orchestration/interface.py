"""
Interface definition for Department: 20_agent_orchestration
LangGraph state machines + Temporal.io durable execution.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class AgentOrchestrationRequest(BaseModel):
    project_id: UUID = Field(..., description="Target project UUID")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class AgentOrchestrationResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    produced_asset_ids: List[UUID] = Field(default_factory=list)

class IAgentOrchestration(ABC):
    """
    Abstract contract for Department 20_agent_orchestration: AgentOrchestration
    """
    @abstractmethod
    async def execute(self, request: AgentOrchestrationRequest) -> AgentOrchestrationResponse:
        """Executes the primary task of this department."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies underlying tooling and dependencies are ready."""
        pass
