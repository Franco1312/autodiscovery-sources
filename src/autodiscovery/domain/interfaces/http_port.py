"""HTTP port interface."""

from abc import ABC, abstractmethod
from typing import Any, Protocol


class HTTPResponse(Protocol):
    """Protocol for HTTP response."""

    status_code: int
    headers: dict[str, str]
    content: bytes
    text: str

    def raise_for_status(self) -> None:
        """Raise exception if status code indicates error."""


class HTTPStreamResponse(Protocol):
    """Protocol for HTTP stream response."""

    status_code: int
    headers: dict[str, str]

    def iter_bytes(self) -> Any:
        """Iterate over response bytes."""

    def raise_for_status(self) -> None:
        """Raise exception if status code indicates error."""


class IHTTPPort(ABC):
    """Port for HTTP operations (HEAD, GET, stream)."""

    @abstractmethod
    def head(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> HTTPResponse:
        """
        Perform HEAD request.

        Args:
            url: URL to request
            headers: Optional headers

        Returns:
            HTTP response with headers
        """

    @abstractmethod
    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> HTTPResponse:
        """
        Perform GET request.

        Args:
            url: URL to request
            headers: Optional headers

        Returns:
            HTTP response with content
        """

    @abstractmethod
    def stream(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> HTTPStreamResponse:
        """
        Perform streaming GET request.

        Args:
            url: URL to request
            headers: Optional headers

        Returns:
            HTTP stream response
        """

    @abstractmethod
    def close(self) -> None:
        """Close HTTP client."""

    @abstractmethod
    def __enter__(self) -> "IHTTPPort":
        """Context manager entry."""

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
