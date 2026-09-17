from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

MemoryKind = Literal["invariant", "reflex", "episodic"]
MemoryStatus = Literal["provisional", "active", "pinned", "decayed", "refuted"]
OutcomeVerdict = Literal["worked", "failed", "avoided"]


class StatementItem(BaseModel):
    """An individual atomic unit of cognitive memory in MemCell."""

    id: str
    title: str
    context: str | None = None
    example: str | None = None
    tags: list[str] = Field(default_factory=list)
    subject: str | None = None
    kind: MemoryKind = "reflex"
    status: MemoryStatus = "active"
    confidence: float = 0.5
    score: float | None = None
    relevance: float | None = None
    decay_factor: float | None = None
    is_guard: bool = False
    is_invariant: bool = False
    expires_at: datetime | None = None
    created_at: datetime | None = None


class RecallResponse(BaseModel):
    """Result of pre-flight memory recall."""

    recall_id: str
    prompt_context: str
    statements: list[StatementItem] = Field(default_factory=list)
    matched_tags: list[str] | None = None
    guard_mode: str | None = None
    profile: dict[str, Any] | None = None


class RememberResponse(BaseModel):
    """Result of explicitly filing statements into MemCell memory."""

    created: list[StatementItem] = Field(default_factory=list)
    reinforced: list[dict[str, Any]] | None = None
    superseded: list[dict[str, Any]] | None = None
    note: str | None = None
    accepted: bool | None = None
    job_id: str | None = None
    status: str | None = None


class ReportResponse(BaseModel):
    """Result of post-flight execution reporting and reinforcement."""

    outcome: OutcomeVerdict
    attributed: list[dict[str, Any]] = Field(default_factory=list)
    distilled_statement: StatementItem | None = None
    note: str | None = None
    accepted: bool | None = None
    job_id: str | None = None
    status: str | None = None


class FeedbackResponse(BaseModel):
    """Direct statement evaluation response."""

    outcome: OutcomeVerdict
    attributed: list[dict[str, Any]] = Field(default_factory=list)


class JobEvent(BaseModel):
    """Telemetry milestone during background job distillation."""

    step: str
    progress: int
    message: str | None = None
    metadata: Any | None = None


class OrganizationItem(BaseModel):
    """Organization metadata item."""

    id: str
    slug: str
    name: str
    role: str | None = None
    created_at: datetime | None = None


class ScopedExecutionContext(BaseModel):
    """Context object injected into agent callbacks during wrap_execution."""

    recall_id: str
    prompt_context: str
    statements: list[StatementItem] = Field(default_factory=list)
    action: str
    subject: str | None = None
