from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

MemoryKind = Literal["invariant", "reflex", "episodic"]
MemoryStatus = Literal["provisional", "active", "pinned", "decayed", "refuted"]
OutcomeVerdict = Literal["worked", "failed", "avoided"]


class StatementItem(BaseModel):
    """An individual atomic unit of cognitive memory in MemCell."""

    id: str
    title: str
    context: Optional[str] = None
    example: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    subject: Optional[str] = None
    kind: MemoryKind = "reflex"
    status: MemoryStatus = "active"
    confidence: float = 0.5
    score: Optional[float] = None
    relevance: Optional[float] = None
    decay_factor: Optional[float] = None
    is_guard: bool = False
    is_invariant: bool = False
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class RecallResponse(BaseModel):
    """Result of pre-flight memory recall."""

    recall_id: str
    prompt_context: str
    statements: List[StatementItem] = Field(default_factory=list)
    matched_tags: Optional[List[str]] = None
    guard_mode: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None


class RememberResponse(BaseModel):
    """Result of explicitly filing statements into MemCell memory."""

    created: List[StatementItem] = Field(default_factory=list)
    reinforced: Optional[List[Dict[str, Any]]] = None
    superseded: Optional[List[Dict[str, Any]]] = None
    note: Optional[str] = None
    accepted: Optional[bool] = None
    job_id: Optional[str] = None
    status: Optional[str] = None


class ReportResponse(BaseModel):
    """Result of post-flight execution reporting and reinforcement."""

    outcome: OutcomeVerdict
    attributed: List[Dict[str, Any]] = Field(default_factory=list)
    distilled_statement: Optional[StatementItem] = None
    note: Optional[str] = None
    accepted: Optional[bool] = None
    job_id: Optional[str] = None
    status: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Direct statement evaluation response."""

    outcome: OutcomeVerdict
    attributed: List[Dict[str, Any]] = Field(default_factory=list)


class JobEvent(BaseModel):
    """Telemetry milestone during background job distillation."""

    step: str
    progress: int
    message: Optional[str] = None
    metadata: Optional[Any] = None


class OrganizationItem(BaseModel):
    """Organization metadata item."""

    id: str
    slug: str
    name: str
    role: Optional[str] = None
    created_at: Optional[datetime] = None


class ScopedExecutionContext(BaseModel):
    """Context object injected into agent callbacks during wrap_execution."""

    recall_id: str
    prompt_context: str
    statements: List[StatementItem] = Field(default_factory=list)
    action: str
    subject: Optional[str] = None
