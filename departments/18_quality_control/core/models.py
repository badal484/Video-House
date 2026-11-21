"""
Domain models for Department 18: Quality Control.
Strongly-typed Pydantic v2 schemas for defect tracking, rule definitions, and audit reports.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class QCSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class QCCheckType(str, enum.Enum):
    FILE_INTEGRITY = "FILE_INTEGRITY"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    COLOR = "COLOR"
    SUBTITLE = "SUBTITLE"
    VISUAL_METRIC = "VISUAL_METRIC"


class QCDefect(BaseModel):
    defect_id: UUID = Field(default_factory=uuid4)
    check_type: QCCheckType
    severity: QCSeverity
    rule_name: str
    description: str
    timestamp_sec: Optional[float] = None
    frame_number: Optional[int] = None
    remediation_suggestion: Optional[str] = None


class QCRule(BaseModel):
    rule_id: str
    name: str
    check_type: QCCheckType
    default_severity: QCSeverity
    threshold: Optional[float] = None
    description: str


class QCPolicy(BaseModel):
    policy_id: str
    name: str
    target_profile_type: str = "DEFAULT"
    max_allowed_warnings: int = 5
    strict_mode: bool = False
    enabled_rules: List[str] = Field(default_factory=list)


class QCReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    asset_id: UUID
    render_job_id: Optional[UUID] = None
    passed: bool = True
    total_issues: int = 0
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    defects: List[QCDefect] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    inspected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

