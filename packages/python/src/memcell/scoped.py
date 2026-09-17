import contextlib
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from .models import (
    FeedbackResponse,
    JobEvent,
    OutcomeVerdict,
    RecallResponse,
    RememberResponse,
    ReportResponse,
    ScopedExecutionContext,
)

T = TypeVar("T")


class ScopedExecutionResult(BaseModel, Generic[T]):
    """Result envelope for wrapped agent execution."""

    result: T
    report: ReportResponse
    recall: RecallResponse


class ScopedMemCell:
    """Synchronous memory handle scoped to a specific project namespace and default subject."""

    def __init__(
        self,
        client: Any,
        namespace: str,
        subject: str | None = None,
    ) -> None:
        self._client = client
        self.namespace = namespace
        self.default_subject = subject

    def recall(
        self,
        query: str,
        subject: str | None = None,
        kind: str | list[str] | None = None,
        min_confidence: float | None = None,
        limit: int | None = None,
        tags: list[str] | None = None,
        format: str = "xml",
        allow_provisional: bool | None = None,
    ) -> RecallResponse:
        return self._client.recall(
            query=query,
            namespace=self.namespace,
            subject=subject or self.default_subject,
            kind=kind,
            min_confidence=min_confidence,
            limit=limit,
            tags=tags,
            format=format,
            allow_provisional=allow_provisional,
        )

    def remember(
        self,
        title: str | None = None,
        context: str | None = None,
        example: str | None = None,
        tags: list[str] | None = None,
        subject: str | None = None,
        kind: str | None = None,
        status: str | None = None,
        confidence: float | None = None,
        expires_at: Any | None = None,
        raw: str | None = None,
        session_id: str | None = None,
        async_: bool | None = None,
    ) -> RememberResponse:
        return self._client.remember(
            title=title,
            context=context,
            example=example,
            tags=tags,
            subject=subject or self.default_subject,
            kind=kind,
            status=status,
            confidence=confidence,
            expires_at=expires_at,
            raw=raw,
            session_id=session_id,
            namespace=self.namespace,
            async_=async_,
        )

    def report(
        self,
        action_taken: str,
        outcome: OutcomeVerdict,
        subject: str | None = None,
        reason: str | None = None,
        external_ref: str | None = None,
        payload: dict[str, Any] | None = None,
        recall_id: str | None = None,
        statement_id: str | None = None,
        auto_distill: bool = True,
        async_: bool | None = None,
    ) -> ReportResponse:
        return self._client.report(
            action_taken=action_taken,
            outcome=outcome,
            namespace=self.namespace,
            subject=subject or self.default_subject,
            reason=reason,
            external_ref=external_ref,
            payload=payload,
            recall_id=recall_id,
            statement_id=statement_id,
            auto_distill=auto_distill,
            async_=async_,
        )

    def feedback(
        self,
        statement_id: str,
        outcome: OutcomeVerdict,
        recall_id: str | None = None,
        reason: str | None = None,
        external_ref: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> FeedbackResponse:
        return self._client.feedback(
            statement_id=statement_id,
            outcome=outcome,
            recall_id=recall_id,
            reason=reason,
            external_ref=external_ref,
            payload=payload,
            namespace=self.namespace,
        )

    def wait_for_job(
        self,
        job_id: str,
        timeout_ms: int = 15000,
        poll_interval_ms: int = 250,
        on_progress: Callable[[JobEvent], None] | None = None,
    ) -> JobEvent:
        return self._client.wait_for_job(
            job_id=job_id,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            on_progress=on_progress,
        )

    def wrap_execution(
        self,
        action: str,
        fn: Callable[[ScopedExecutionContext], T],
        subject: str | None = None,
        external_ref: str | None = None,
        payload: dict[str, Any] | None = None,
        query: str | None = None,
    ) -> ScopedExecutionResult[T]:
        target_subject = subject or self.default_subject
        recall = self.recall(query=query or action, subject=target_subject)
        context = ScopedExecutionContext(
            recall_id=recall.recall_id,
            prompt_context=recall.prompt_context,
            statements=recall.statements,
            action=action,
            subject=target_subject,
        )

        try:
            result = fn(context)
            report = self.report(
                action_taken=action,
                outcome="worked",
                subject=target_subject,
                recall_id=recall.recall_id,
                external_ref=external_ref,
                payload=payload,
            )
            return ScopedExecutionResult[T](result=result, report=report, recall=recall)
        except Exception as e:
            with contextlib.suppress(Exception):
                self.report(
                    action_taken=action,
                    outcome="failed",
                    reason=str(e),
                    subject=target_subject,
                    recall_id=recall.recall_id,
                    external_ref=external_ref,
                    payload=payload,
                )
            raise


class AsyncScopedMemCell:
    """Asynchronous memory handle scoped to a specific project namespace and default subject."""

    def __init__(
        self,
        client: Any,
        namespace: str,
        subject: str | None = None,
    ) -> None:
        self._client = client
        self.namespace = namespace
        self.default_subject = subject

    async def recall(
        self,
        query: str,
        subject: str | None = None,
        kind: str | list[str] | None = None,
        min_confidence: float | None = None,
        limit: int | None = None,
        tags: list[str] | None = None,
        format: str = "xml",
        allow_provisional: bool | None = None,
    ) -> RecallResponse:
        return await self._client.recall(
            query=query,
            namespace=self.namespace,
            subject=subject or self.default_subject,
            kind=kind,
            min_confidence=min_confidence,
            limit=limit,
            tags=tags,
            format=format,
            allow_provisional=allow_provisional,
        )

    async def remember(
        self,
        title: str | None = None,
        context: str | None = None,
        example: str | None = None,
        tags: list[str] | None = None,
        subject: str | None = None,
        kind: str | None = None,
        status: str | None = None,
        confidence: float | None = None,
        expires_at: Any | None = None,
        raw: str | None = None,
        session_id: str | None = None,
        async_: bool | None = None,
    ) -> RememberResponse:
        return await self._client.remember(
            title=title,
            context=context,
            example=example,
            tags=tags,
            subject=subject or self.default_subject,
            kind=kind,
            status=status,
            confidence=confidence,
            expires_at=expires_at,
            raw=raw,
            session_id=session_id,
            namespace=self.namespace,
            async_=async_,
        )

    async def report(
        self,
        action_taken: str,
        outcome: OutcomeVerdict,
        subject: str | None = None,
        reason: str | None = None,
        external_ref: str | None = None,
        payload: dict[str, Any] | None = None,
        recall_id: str | None = None,
        statement_id: str | None = None,
        auto_distill: bool = True,
        async_: bool | None = None,
    ) -> ReportResponse:
        return await self._client.report(
            action_taken=action_taken,
            outcome=outcome,
            namespace=self.namespace,
            subject=subject or self.default_subject,
            reason=reason,
            external_ref=external_ref,
            payload=payload,
            recall_id=recall_id,
            statement_id=statement_id,
            auto_distill=auto_distill,
            async_=async_,
        )

    async def feedback(
        self,
        statement_id: str,
        outcome: OutcomeVerdict,
        recall_id: str | None = None,
        reason: str | None = None,
        external_ref: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> FeedbackResponse:
        return await self._client.feedback(
            statement_id=statement_id,
            outcome=outcome,
            recall_id=recall_id,
            reason=reason,
            external_ref=external_ref,
            payload=payload,
            namespace=self.namespace,
        )

    async def wait_for_job(
        self,
        job_id: str,
        timeout_ms: int = 15000,
        poll_interval_ms: int = 250,
        on_progress: Callable[[JobEvent], None] | None = None,
    ) -> JobEvent:
        return await self._client.wait_for_job(
            job_id=job_id,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
            on_progress=on_progress,
        )

    async def wrap_execution(
        self,
        action: str,
        fn: Callable[[ScopedExecutionContext], T | Awaitable[T]],
        subject: str | None = None,
        external_ref: str | None = None,
        payload: dict[str, Any] | None = None,
        query: str | None = None,
    ) -> ScopedExecutionResult[T]:
        target_subject = subject or self.default_subject
        recall = await self.recall(query=query or action, subject=target_subject)
        context = ScopedExecutionContext(
            recall_id=recall.recall_id,
            prompt_context=recall.prompt_context,
            statements=recall.statements,
            action=action,
            subject=target_subject,
        )

        try:
            res = fn(context)
            if hasattr(res, "__await__"):
                result = await res  # type: ignore
            else:
                result = res  # type: ignore

            report = await self.report(
                action_taken=action,
                outcome="worked",
                subject=target_subject,
                recall_id=recall.recall_id,
                external_ref=external_ref,
                payload=payload,
            )
            return ScopedExecutionResult[T](result=result, report=report, recall=recall)
        except Exception as e:
            with contextlib.suppress(Exception):
                await self.report(
                    action_taken=action,
                    outcome="failed",
                    reason=str(e),
                    subject=target_subject,
                    recall_id=recall.recall_id,
                    external_ref=external_ref,
                    payload=payload,
                )
            raise
