from typing import Any, Optional


class MemCellError(Exception):
    """Base exception thrown by the MemCell SDK on API and network failures."""

    def __init__(
        self,
        message: str,
        status: int = 0,
        code: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details

    def __repr__(self) -> str:
        return f"MemCellError(status={self.status}, code={self.code!r}, message={self.message!r})"


class RateLimitError(MemCellError):
    """Exception thrown when an API request is rejected with HTTP 429 Too Many Requests per ADR 057."""

    def __init__(
        self,
        message: str,
        door: Optional[str] = None,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        retry_after: int = 1,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message=message,
            status=429,
            code="rate_limited",
            details=details,
        )
        self.door = door
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after

    def __repr__(self) -> str:
        return (
            f"RateLimitError(door={self.door!r}, limit={self.limit}, "
            f"window_seconds={self.window_seconds}, retry_after={self.retry_after}, message={self.message!r})"
        )
