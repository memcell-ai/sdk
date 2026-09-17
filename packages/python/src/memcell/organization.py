from typing import Any

from .models import (
    FeedbackResponse,
    OutcomeVerdict,
    RecallResponse,
    RememberResponse,
    ReportResponse,
)


class OrganizationMemCell:
    """Synchronous memory handle bound to a specific organization."""

    def __init__(self, client: Any, org_slug: str) -> None:
        self._client = client
        self.org_slug = org_slug

    def scope(self, project_slug: str, subject: str | None = None) -> Any:
        from .scoped import ScopedMemCell

        namespace = f"{self.org_slug}/{project_slug}"
        return ScopedMemCell(self._client, namespace, subject=subject)

    def _resolve_namespace(self, namespace: str | None) -> str:
        if not namespace:
            return self.org_slug
        if "/" in namespace:
            return namespace
        return f"{self.org_slug}/{namespace}"

    def recall(
        self,
        query: str,
        namespace: str | None = None,
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
            namespace=self._resolve_namespace(namespace),
            subject=subject,
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
        namespace: str | None = None,
        async_: bool | None = None,
    ) -> RememberResponse:
        return self._client.remember(
            title=title,
            context=context,
            example=example,
            tags=tags,
            subject=subject,
            kind=kind,
            status=status,
            confidence=confidence,
            expires_at=expires_at,
            raw=raw,
            session_id=session_id,
            namespace=self._resolve_namespace(namespace),
            async_=async_,
        )

    def report(
        self,
        action_taken: str,
        outcome: OutcomeVerdict,
        namespace: str | None = None,
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
            namespace=self._resolve_namespace(namespace),
            subject=subject,
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
        namespace: str | None = None,
    ) -> FeedbackResponse:
        return self._client.feedback(
            statement_id=statement_id,
            outcome=outcome,
            recall_id=recall_id,
            reason=reason,
            external_ref=external_ref,
            payload=payload,
            namespace=self._resolve_namespace(namespace),
        )


class AsyncOrganizationMemCell:
    """Asynchronous memory handle bound to a specific organization."""

    def __init__(self, client: Any, org_slug: str) -> None:
        self._client = client
        self.org_slug = org_slug

    def scope(self, project_slug: str, subject: str | None = None) -> Any:
        from .scoped import AsyncScopedMemCell

        namespace = f"{self.org_slug}/{project_slug}"
        return AsyncScopedMemCell(self._client, namespace, subject=subject)

    def _resolve_namespace(self, namespace: str | None) -> str:
        if not namespace:
            return self.org_slug
        if "/" in namespace:
            return namespace
        return f"{self.org_slug}/{namespace}"

    async def recall(
        self,
        query: str,
        namespace: str | None = None,
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
            namespace=self._resolve_namespace(namespace),
            subject=subject,
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
        namespace: str | None = None,
        async_: bool | None = None,
    ) -> RememberResponse:
        return await self._client.remember(
            title=title,
            context=context,
            example=example,
            tags=tags,
            subject=subject,
            kind=kind,
            status=status,
            confidence=confidence,
            expires_at=expires_at,
            raw=raw,
            session_id=session_id,
            namespace=self._resolve_namespace(namespace),
            async_=async_,
        )

    async def report(
        self,
        action_taken: str,
        outcome: OutcomeVerdict,
        namespace: str | None = None,
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
            namespace=self._resolve_namespace(namespace),
            subject=subject,
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
        namespace: str | None = None,
    ) -> FeedbackResponse:
        return await self._client.feedback(
            statement_id=statement_id,
            outcome=outcome,
            recall_id=recall_id,
            reason=reason,
            external_ref=external_ref,
            payload=payload,
            namespace=self._resolve_namespace(namespace),
        )
