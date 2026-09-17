from typing import Any, Dict, List, Optional, Union

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

    def scope(self, project_slug: str, subject: Optional[str] = None) -> Any:
        from .scoped import ScopedMemCell

        namespace = f"{self.org_slug}/{project_slug}"
        return ScopedMemCell(self._client, namespace, subject=subject)

    def _resolve_namespace(self, namespace: Optional[str]) -> str:
        if not namespace:
            return self.org_slug
        if "/" in namespace:
            return namespace
        return f"{self.org_slug}/{namespace}"

    def recall(
        self,
        query: str,
        namespace: Optional[str] = None,
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
        namespace: Optional[str] = None,
        async_: Optional[bool] = None,
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
        namespace: Optional[str] = None,
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
        recall_id: Optional[str] = None,
        reason: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
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

    def scope(self, project_slug: str, subject: Optional[str] = None) -> Any:
        from .scoped import AsyncScopedMemCell

        namespace = f"{self.org_slug}/{project_slug}"
        return AsyncScopedMemCell(self._client, namespace, subject=subject)

    def _resolve_namespace(self, namespace: Optional[str]) -> str:
        if not namespace:
            return self.org_slug
        if "/" in namespace:
            return namespace
        return f"{self.org_slug}/{namespace}"

    async def recall(
        self,
        query: str,
        namespace: Optional[str] = None,
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
        namespace: Optional[str] = None,
        async_: Optional[bool] = None,
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
        namespace: Optional[str] = None,
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
        recall_id: Optional[str] = None,
        reason: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
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
