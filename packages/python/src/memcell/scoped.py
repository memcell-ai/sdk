from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar, Union
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
        subject: Optional[str] = None,
    ) -> None:
        self._client = client
        self.namespace = namespace
        self.default_subject = subject

    def recall(
        self,
        query: str,
        subject: Optional[str] = None,
        kind: Optional[Union[str, List[str]]] = None,
        min_confidence: Optional[float] = None,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        format: str = "xml",
        allow_provisional: Optional[bool] = None,
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
        title: Optional[str] = None,
        context: Optional[str] = None,
        example: Optional[str] = None,
        tags: Optional[List[str]] = None,
        subject: Optional[str] = None,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        confidence: Optional[float] = None,
        expires_at: Optional[Any] = None,
        raw: Optional[str] = None,
        session_id: Optional[str] = None,
        async_: Optional[bool] = None,
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
        subject: Optional[str] = None,
        reason: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        recall_id: Optional[str] = None,
        statement_id: Optional[str] = None,
        auto_distill: bool = True,
        async_: Optional[bool] = None,
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
        recall_id: Optional[str] = None,
        reason: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
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
        on_progress: Optional[Callable[[JobEvent], None]] = None,
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
        subject: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
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
            try:
                self.report(
                    action_taken=action,
                    outcome="failed",
                    reason=str(e),
                    subject=target_subject,
                    recall_id=recall.recall_id,
                    external_ref=external_ref,
                    payload=payload,
                )
            except Exception:
                pass
            raise e


class AsyncScopedMemCell:
    """Asynchronous memory handle scoped to a specific project namespace and default subject."""

    def __init__(
        self,
        client: Any,
        namespace: str,
        subject: Optional[str] = None,
    ) -> None:
        self._client = client
        self.namespace = namespace
        self.default_subject = subject

    async def recall(
        self,
        query: str,
        subject: Optional[str] = None,
        kind: Optional[Union[str, List[str]]] = None,
        min_confidence: Optional[float] = None,
        limit: Optional[int] = None,
        tags: Optional[List[str]] = None,
        format: str = "xml",
        allow_provisional: Optional[bool] = None,
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
        title: Optional[str] = None,
        context: Optional[str] = None,
        example: Optional[str] = None,
        tags: Optional[List[str]] = None,
        subject: Optional[str] = None,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        confidence: Optional[float] = None,
        expires_at: Optional[Any] = None,
        raw: Optional[str] = None,
        session_id: Optional[str] = None,
        async_: Optional[bool] = None,
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
        subject: Optional[str] = None,
        reason: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        recall_id: Optional[str] = None,
        statement_id: Optional[str] = None,
        auto_distill: bool = True,
        async_: Optional[bool] = None,
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
        recall_id: Optional[str] = None,
        reason: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
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
        on_progress: Optional[Callable[[JobEvent], None]] = None,
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
        fn: Callable[[ScopedExecutionContext], Union[T, Awaitable[T]]],
        subject: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
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
            try:
                await self.report(
                    action_taken=action,
                    outcome="failed",
                    reason=str(e),
                    subject=target_subject,
                    recall_id=recall.recall_id,
                    external_ref=external_ref,
                    payload=payload,
                )
            except Exception:
                pass
            raise e
