import asyncio
import json
import os
import random
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union
import httpx

from .auth import AuthManager
from .exceptions import MemCellError, RateLimitError
from .models import (
    FeedbackResponse,
    JobEvent,
    OrganizationItem,
    OutcomeVerdict,
    RecallResponse,
    RememberResponse,
    ReportResponse,
    StatementItem,
)

if TYPE_CHECKING:
    from .organization import AsyncOrganizationMemCell, OrganizationMemCell
    from .scoped import AsyncScopedMemCell, ScopedMemCell


def _resolve_endpoint(
    namespace: Optional[str],
    action: str,
) -> str:
    if namespace and "/" in namespace:
        owner, project = namespace.split("/", 1)
        return f"/api/v1/{owner}/{project}/{action}"
    return f"/api/v1/{action}"


def _parse_statement_item(data: Dict[str, Any]) -> StatementItem:
    tags = data.get("tags") or []
    kind = data.get("kind", "reflex")
    status = data.get("status", "active")
    is_guard = data.get("isGuard")
    if is_guard is None:
        is_guard = ("guard" in tags) or ("convention" in tags)
    is_invariant = data.get("isInvariant")
    if is_invariant is None:
        is_invariant = (kind == "invariant") or (status == "pinned")

    return StatementItem(
        id=str(data.get("id") or data.get("statementId") or ""),
        title=data.get("title", ""),
        context=data.get("context"),
        example=data.get("example"),
        tags=tags,
        subject=data.get("subject"),
        kind=kind,
        status=status,
        confidence=float(data.get("confidence", 0.5)),
        score=data.get("score"),
        relevance=data.get("relevance"),
        decay_factor=data.get("decayFactor"),
        is_guard=is_guard,
        is_invariant=is_invariant,
        expires_at=data.get("expiresAt"),
        created_at=data.get("createdAt"),
    )


class _OrganizationsNamespaceSync:
    def __init__(self, client: "MemCell") -> None:
        self._client = client

    def list(self) -> List[OrganizationItem]:
        resp = self._client._request("GET", "/api/v1/organizations")
        orgs = resp.get("organizations") or []
        return [OrganizationItem(**o) for o in orgs]

    def create(self, name: str, slug: Optional[str] = None) -> OrganizationItem:
        body: Dict[str, Any] = {"name": name}
        if slug:
            body["slug"] = slug
        resp = self._client._request("POST", "/api/v1/organizations", json=body)
        return OrganizationItem(**resp.get("organization", {}))

    def get(self, slug: str) -> OrganizationItem:
        resp = self._client._request("GET", f"/api/v1/organizations/{slug}")
        return OrganizationItem(**resp.get("organization", {}))


class _OrganizationsNamespaceAsync:
    def __init__(self, client: "AsyncMemCell") -> None:
        self._client = client

    async def list(self) -> List[OrganizationItem]:
        resp = await self._client._request("GET", "/api/v1/organizations")
        orgs = resp.get("organizations") or []
        return [OrganizationItem(**o) for o in orgs]

    async def create(self, name: str, slug: Optional[str] = None) -> OrganizationItem:
        body: Dict[str, Any] = {"name": name}
        if slug:
            body["slug"] = slug
        resp = await self._client._request("POST", "/api/v1/organizations", json=body)
        return OrganizationItem(**resp.get("organization", {}))

    async def get(self, slug: str) -> OrganizationItem:
        resp = await self._client._request("GET", f"/api/v1/organizations/{slug}")
        return OrganizationItem(**resp.get("organization", {}))


class MemCell:
    """Synchronous MemCell client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        initial_retry_delay_ms: int = 1000,
        max_retry_delay_ms: int = 15000,
        on_rate_limit_warning: Optional[Callable[[str, httpx.Response], None]] = None,
        timeout: float = 30.0,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        base = base_url or os.environ.get("MEMCELL_BASE_URL", "https://api.memcell.io")
        self.base_url = base.rstrip("/")
        self.max_retries = max_retries
        self.initial_retry_delay_ms = initial_retry_delay_ms
        self.max_retry_delay_ms = max_retry_delay_ms
        self.on_rate_limit_warning = on_rate_limit_warning

        self.auth_manager = AuthManager(
            base_url=self.base_url,
            api_key=api_key or os.environ.get("MEMCELL_API_KEY"),
            access_token=access_token,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
        )

        self._custom_client = http_client is not None
        self._http = http_client or httpx.Client(timeout=timeout)
        self.organizations = _OrganizationsNamespaceSync(self)

    def close(self) -> None:
        if not self._custom_client:
            self._http.close()

    def __enter__(self) -> "MemCell":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def for_organization(self, org_slug: str) -> "OrganizationMemCell":
        from .organization import OrganizationMemCell

        return OrganizationMemCell(self, org_slug)

    def scope(self, namespace: str, subject: Optional[str] = None) -> "ScopedMemCell":
        from .scoped import ScopedMemCell

        return ScopedMemCell(self, namespace, subject=subject)

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        attempt = 0
        while True:
            headers = kwargs.pop("headers", {}) or {}
            auth_header = self.auth_manager.get_authorization_header(self._http)
            if auth_header:
                headers["Authorization"] = auth_header
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json"

            url = f"{self.base_url}{path}"
            response = self._http.request(method, url, headers=headers, **kwargs)

            # Check 299 warning header
            warning = response.headers.get("RateLimit-Warning")
            if warning and self.on_rate_limit_warning:
                try:
                    self.on_rate_limit_warning(warning, response)
                except Exception:
                    pass

            # Handle 429
            if response.status_code == 429:
                retry_header = response.headers.get("Retry-After")
                try:
                    retry_sec = int(retry_header) if retry_header else None
                except ValueError:
                    retry_sec = None

                if attempt < self.max_retries:
                    attempt += 1
                    if retry_sec is not None and retry_sec > 0:
                        delay_ms = retry_sec * 1000
                    else:
                        delay_ms = min(
                            self.max_retry_delay_ms,
                            self.initial_retry_delay_ms * (2 ** (attempt - 1)),
                        )
                    delay_ms += random.randint(0, 200)
                    time.sleep(delay_ms / 1000.0)
                    continue

                # Retries exhausted -> throw RateLimitError
                err_json = response.json() if response.content else {}
                effective_retry = (
                    retry_sec if (retry_sec and retry_sec > 0) else err_json.get("retryAfter", 1)
                )
                door_str = f" on door '{err_json.get('door')}'" if err_json.get("door") else ""
                msg = (
                    err_json.get("message")
                    or f"Rate limit exceeded{door_str}. Please retry in {effective_retry}s."
                )
                raise RateLimitError(
                    message=msg,
                    door=err_json.get("door"),
                    limit=err_json.get("limit"),
                    window_seconds=err_json.get("windowSeconds"),
                    retry_after=effective_retry,
                    details=err_json,
                )

            if not response.is_success:
                err_json = response.json() if response.content else {}
                message = (
                    err_json.get("message")
                    or (
                        err_json.get("error", {}).get("message")
                        if isinstance(err_json.get("error"), dict)
                        else err_json.get("error")
                    )
                    or err_json.get("error_description")
                    or response.reason_phrase
                    or f"HTTP {response.status_code}"
                )
                code = (
                    err_json.get("error")
                    if isinstance(err_json.get("error"), str)
                    else f"HTTP_{response.status_code}"
                )
                raise MemCellError(
                    f"MemCell API Error ({response.status_code}): {message}",
                    status=response.status_code,
                    code=code,
                    details=err_json,
                )

            return response.json() if response.content else {}

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
        path = _resolve_endpoint(namespace, "recall")
        payload: Dict[str, Any] = {
            "query": query,
            "intent": query,
            "subject": subject,
            "kind": kind,
            "min_confidence": min_confidence,
            "limit": limit,
            "tags": tags,
            "format": format,
            "allow_provisional": allow_provisional,
        }
        if namespace and "/" not in namespace:
            payload["project"] = namespace

        data = self._request("POST", path, json=payload)
        raw_statements = data.get("statements") or data.get("results") or []
        statements = [_parse_statement_item(s) for s in raw_statements]

        return RecallResponse(
            recall_id=str(data.get("recallId") or data.get("momentId") or ""),
            prompt_context=str(data.get("promptContext") or ""),
            statements=statements,
            matched_tags=data.get("matchedTags"),
            guard_mode=data.get("guardMode"),
            profile=data.get("profile"),
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
        path = _resolve_endpoint(namespace, "remember")
        payload: Dict[str, Any] = {
            "title": title,
            "context": context,
            "example": example,
            "tags": tags,
            "subject": subject,
            "kind": kind,
            "status": status,
            "confidence": confidence,
            "expires_at": expires_at.isoformat()
            if hasattr(expires_at, "isoformat")
            else expires_at,
            "raw": raw,
            "sessionId": session_id,
            "async": async_,
        }
        if namespace and "/" not in namespace:
            payload["project"] = namespace

        data = self._request("POST", path, json=payload)
        if data.get("accepted"):
            return RememberResponse(
                accepted=True,
                job_id=data.get("jobId"),
                status=data.get("status"),
                created=[],
                note=data.get("note", "Job accepted for background execution."),
            )

        raw_created = data.get("created") or []
        created = [_parse_statement_item(s) for s in raw_created]
        return RememberResponse(
            created=created,
            reinforced=data.get("reinforced"),
            superseded=data.get("superseded"),
            note=data.get("note"),
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
        path = _resolve_endpoint(namespace, "report")
        body: Dict[str, Any] = {
            "action_taken": action_taken,
            "outcome": outcome,
            "subject": subject,
            "reason": reason,
            "external_ref": external_ref,
            "payload": payload,
            "recall_id": recall_id,
            "statement_id": statement_id,
            "auto_distill": auto_distill,
            "async": async_,
        }
        if namespace and "/" not in namespace:
            body["project"] = namespace

        data = self._request("POST", path, json=body)
        if data.get("accepted"):
            return ReportResponse(
                accepted=True,
                job_id=data.get("jobId"),
                status=data.get("status"),
                outcome=outcome,
                attributed=[],
                note=data.get("note", "Report accepted for background execution."),
            )

        distilled = None
        if data.get("distilledStatement"):
            distilled = _parse_statement_item(data["distilledStatement"])

        return ReportResponse(
            outcome=data.get("outcome", outcome),
            attributed=data.get("attributed") or [],
            distilled_statement=distilled,
            note=data.get("note"),
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
        path = _resolve_endpoint(namespace, "feedback")
        body: Dict[str, Any] = {
            "statement_id": statement_id,
            "recall_id": recall_id,
            "outcome": outcome,
            "reason": reason,
            "external_ref": external_ref,
            "payload": payload,
        }
        if namespace and "/" not in namespace:
            body["project"] = namespace

        data = self._request("POST", path, json=body)
        return FeedbackResponse(
            outcome=data.get("outcome", outcome),
            attributed=data.get("attributed") or [],
        )

    def wait_for_job(
        self,
        job_id: str,
        timeout_ms: int = 15000,
        poll_interval_ms: int = 250,
        on_progress: Optional[Callable[[JobEvent], None]] = None,
    ) -> JobEvent:
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0
        poll_sec = poll_interval_ms / 1000.0

        # Attempt SSE streaming
        try:
            auth_header = self.auth_manager.get_authorization_header(self._http)
            headers = {"Accept": "text/event-stream"}
            if auth_header:
                headers["Authorization"] = auth_header

            with self._http.stream(
                "GET", f"{self.base_url}/api/v1/jobs/{job_id}/stream", headers=headers
            ) as resp:
                if resp.is_success:
                    for line in resp.iter_lines():
                        if time.time() - start_time > timeout_sec:
                            raise MemCellError(f"Job {job_id} timed out after {timeout_ms}ms.")
                        if line.startswith("data:"):
                            json_str = line[len("data:") :].strip()
                            event_data = json.loads(json_str)
                            event = JobEvent(**event_data)
                            if on_progress:
                                on_progress(event)
                            if event.step == "completed":
                                return event
                            if event.step == "failed":
                                raise MemCellError(event.message or f"Job {job_id} failed.")
        except MemCellError:
            raise
        except Exception:
            pass  # Fall back to polling

        # Polling fallback
        while time.time() - start_time <= timeout_sec:
            try:
                res = self._request("GET", f"/api/v1/jobs/{job_id}")
                job = res.get("job")
                if job:
                    event = JobEvent(
                        step=job.get("step"),
                        progress=int(job.get("progress", 0)),
                        message=job.get("message"),
                        metadata=job.get("result"),
                    )
                    if on_progress:
                        on_progress(event)
                    if event.step == "completed":
                        return event
                    if event.step == "failed":
                        raise MemCellError(event.message or f"Job {job_id} failed.")
            except Exception:
                pass

            time.sleep(poll_sec)

        raise MemCellError(f"Job {job_id} timed out after {timeout_ms}ms.")


class AsyncMemCell:
    """Asynchronous MemCell client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        initial_retry_delay_ms: int = 1000,
        max_retry_delay_ms: int = 15000,
        on_rate_limit_warning: Optional[Callable[[str, httpx.Response], None]] = None,
        timeout: float = 30.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        base = base_url or os.environ.get("MEMCELL_BASE_URL", "https://api.memcell.io")
        self.base_url = base.rstrip("/")
        self.max_retries = max_retries
        self.initial_retry_delay_ms = initial_retry_delay_ms
        self.max_retry_delay_ms = max_retry_delay_ms
        self.on_rate_limit_warning = on_rate_limit_warning

        self.auth_manager = AuthManager(
            base_url=self.base_url,
            api_key=api_key or os.environ.get("MEMCELL_API_KEY"),
            access_token=access_token,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
        )

        self._custom_client = http_client is not None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)
        self.organizations = _OrganizationsNamespaceAsync(self)

    async def aclose(self) -> None:
        if not self._custom_client:
            await self._http.aclose()

    async def __aenter__(self) -> "AsyncMemCell":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    def for_organization(self, org_slug: str) -> "AsyncOrganizationMemCell":
        from .organization import AsyncOrganizationMemCell

        return AsyncOrganizationMemCell(self, org_slug)

    def scope(self, namespace: str, subject: Optional[str] = None) -> "AsyncScopedMemCell":
        from .scoped import AsyncScopedMemCell

        return AsyncScopedMemCell(self, namespace, subject=subject)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        attempt = 0
        while True:
            headers = kwargs.pop("headers", {}) or {}
            auth_header = await self.auth_manager.get_authorization_header_async(self._http)
            if auth_header:
                headers["Authorization"] = auth_header
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json"

            url = f"{self.base_url}{path}"
            response = await self._http.request(method, url, headers=headers, **kwargs)

            # Check 299 warning header
            warning = response.headers.get("RateLimit-Warning")
            if warning and self.on_rate_limit_warning:
                try:
                    self.on_rate_limit_warning(warning, response)
                except Exception:
                    pass

            # Handle 429
            if response.status_code == 429:
                retry_header = response.headers.get("Retry-After")
                try:
                    retry_sec = int(retry_header) if retry_header else None
                except ValueError:
                    retry_sec = None

                if attempt < self.max_retries:
                    attempt += 1
                    if retry_sec is not None and retry_sec > 0:
                        delay_ms = retry_sec * 1000
                    else:
                        delay_ms = min(
                            self.max_retry_delay_ms,
                            self.initial_retry_delay_ms * (2 ** (attempt - 1)),
                        )
                    delay_ms += random.randint(0, 200)
                    await asyncio.sleep(delay_ms / 1000.0)
                    continue

                # Retries exhausted -> throw RateLimitError
                err_json = response.json() if response.content else {}
                effective_retry = (
                    retry_sec if (retry_sec and retry_sec > 0) else err_json.get("retryAfter", 1)
                )
                door_str = f" on door '{err_json.get('door')}'" if err_json.get("door") else ""
                msg = (
                    err_json.get("message")
                    or f"Rate limit exceeded{door_str}. Please retry in {effective_retry}s."
                )
                raise RateLimitError(
                    message=msg,
                    door=err_json.get("door"),
                    limit=err_json.get("limit"),
                    window_seconds=err_json.get("windowSeconds"),
                    retry_after=effective_retry,
                    details=err_json,
                )

            if not response.is_success:
                err_json = response.json() if response.content else {}
                message = (
                    err_json.get("message")
                    or (
                        err_json.get("error", {}).get("message")
                        if isinstance(err_json.get("error"), dict)
                        else err_json.get("error")
                    )
                    or err_json.get("error_description")
                    or response.reason_phrase
                    or f"HTTP {response.status_code}"
                )
                code = (
                    err_json.get("error")
                    if isinstance(err_json.get("error"), str)
                    else f"HTTP_{response.status_code}"
                )
                raise MemCellError(
                    f"MemCell API Error ({response.status_code}): {message}",
                    status=response.status_code,
                    code=code,
                    details=err_json,
                )

            return response.json() if response.content else {}

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
        path = _resolve_endpoint(namespace, "recall")
        payload: Dict[str, Any] = {
            "query": query,
            "intent": query,
            "subject": subject,
            "kind": kind,
            "min_confidence": min_confidence,
            "limit": limit,
            "tags": tags,
            "format": format,
            "allow_provisional": allow_provisional,
        }
        if namespace and "/" not in namespace:
            payload["project"] = namespace

        data = await self._request("POST", path, json=payload)
        raw_statements = data.get("statements") or data.get("results") or []
        statements = [_parse_statement_item(s) for s in raw_statements]

        return RecallResponse(
            recall_id=str(data.get("recallId") or data.get("momentId") or ""),
            prompt_context=str(data.get("promptContext") or ""),
            statements=statements,
            matched_tags=data.get("matchedTags"),
            guard_mode=data.get("guardMode"),
            profile=data.get("profile"),
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
        path = _resolve_endpoint(namespace, "remember")
        payload: Dict[str, Any] = {
            "title": title,
            "context": context,
            "example": example,
            "tags": tags,
            "subject": subject,
            "kind": kind,
            "status": status,
            "confidence": confidence,
            "expires_at": expires_at.isoformat()
            if hasattr(expires_at, "isoformat")
            else expires_at,
            "raw": raw,
            "sessionId": session_id,
            "async": async_,
        }
        if namespace and "/" not in namespace:
            payload["project"] = namespace

        data = await self._request("POST", path, json=payload)
        if data.get("accepted"):
            return RememberResponse(
                accepted=True,
                job_id=data.get("jobId"),
                status=data.get("status"),
                created=[],
                note=data.get("note", "Job accepted for background execution."),
            )

        raw_created = data.get("created") or []
        created = [_parse_statement_item(s) for s in raw_created]
        return RememberResponse(
            created=created,
            reinforced=data.get("reinforced"),
            superseded=data.get("superseded"),
            note=data.get("note"),
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
        path = _resolve_endpoint(namespace, "report")
        body: Dict[str, Any] = {
            "action_taken": action_taken,
            "outcome": outcome,
            "subject": subject,
            "reason": reason,
            "external_ref": external_ref,
            "payload": payload,
            "recall_id": recall_id,
            "statement_id": statement_id,
            "auto_distill": auto_distill,
            "async": async_,
        }
        if namespace and "/" not in namespace:
            body["project"] = namespace

        data = await self._request("POST", path, json=body)
        if data.get("accepted"):
            return ReportResponse(
                accepted=True,
                job_id=data.get("jobId"),
                status=data.get("status"),
                outcome=outcome,
                attributed=[],
                note=data.get("note", "Report accepted for background execution."),
            )

        distilled = None
        if data.get("distilledStatement"):
            distilled = _parse_statement_item(data["distilledStatement"])

        return ReportResponse(
            outcome=data.get("outcome", outcome),
            attributed=data.get("attributed") or [],
            distilled_statement=distilled,
            note=data.get("note"),
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
        path = _resolve_endpoint(namespace, "feedback")
        body: Dict[str, Any] = {
            "statement_id": statement_id,
            "recall_id": recall_id,
            "outcome": outcome,
            "reason": reason,
            "external_ref": external_ref,
            "payload": payload,
        }
        if namespace and "/" not in namespace:
            body["project"] = namespace

        data = await self._request("POST", path, json=body)
        return FeedbackResponse(
            outcome=data.get("outcome", outcome),
            attributed=data.get("attributed") or [],
        )

    async def wait_for_job(
        self,
        job_id: str,
        timeout_ms: int = 15000,
        poll_interval_ms: int = 250,
        on_progress: Optional[Callable[[JobEvent], None]] = None,
    ) -> JobEvent:
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0
        poll_sec = poll_interval_ms / 1000.0

        # Attempt SSE streaming
        try:
            auth_header = await self.auth_manager.get_authorization_header_async(self._http)
            headers = {"Accept": "text/event-stream"}
            if auth_header:
                headers["Authorization"] = auth_header

            async with self._http.stream(
                "GET", f"{self.base_url}/api/v1/jobs/{job_id}/stream", headers=headers
            ) as resp:
                if resp.is_success:
                    async for line in resp.aiter_lines():
                        if time.time() - start_time > timeout_sec:
                            raise MemCellError(f"Job {job_id} timed out after {timeout_ms}ms.")
                        if line.startswith("data:"):
                            json_str = line[len("data:") :].strip()
                            event_data = json.loads(json_str)
                            event = JobEvent(**event_data)
                            if on_progress:
                                on_progress(event)
                            if event.step == "completed":
                                return event
                            if event.step == "failed":
                                raise MemCellError(event.message or f"Job {job_id} failed.")
        except MemCellError:
            raise
        except Exception:
            pass  # Fall back to polling

        # Polling fallback
        while time.time() - start_time <= timeout_sec:
            try:
                res = await self._request("GET", f"/api/v1/jobs/{job_id}")
                job = res.get("job")
                if job:
                    event = JobEvent(
                        step=job.get("step"),
                        progress=int(job.get("progress", 0)),
                        message=job.get("message"),
                        metadata=job.get("result"),
                    )
                    if on_progress:
                        on_progress(event)
                    if event.step == "completed":
                        return event
                    if event.step == "failed":
                        raise MemCellError(event.message or f"Job {job_id} failed.")
            except Exception:
                pass

            await asyncio.sleep(poll_sec)

        raise MemCellError(f"Job {job_id} timed out after {timeout_ms}ms.")
