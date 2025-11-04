"""Domain interfaces (ports)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from autodiscovery.domain.entities import DiscoveredFile, SourceEntry

if TYPE_CHECKING:
    HTTPResponse = Any  # Protocol for HTTP response
    HTTPStreamResponse = Any  # Protocol for HTTP stream response
    HTMLSoup = Any  # Protocol for HTML soup


class ISourceDiscoverer(ABC):
    """Interface for source discoverers."""

    @abstractmethod
    def discover(self, start_urls: list[str]) -> DiscoveredFile | None:
        """
        Discover file from start URLs.

        Returns DiscoveredFile if found, None otherwise.
        """


class IRegistryRepository(ABC):
    """Interface for registry repository."""

    @abstractmethod
    def get_entry(self, key: str) -> SourceEntry | None:
        """Get entry by key."""

    @abstractmethod
    def set_entry(self, key: str, entry: SourceEntry) -> None:
        """Set entry by key."""

    @abstractmethod
    def has_entry(self, key: str) -> bool:
        """Check if entry exists."""

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all keys in registry."""


class IMirrorService(ABC):
    """Interface for mirror service."""

    @abstractmethod
    def mirror_file(
        self,
        url: str,
        key: str,
        version: str,
        filename: str,
    ) -> tuple[Path, str]:
        """
        Mirror file from URL.

        Returns (stored_path, sha256).
        """


class IFileValidator(ABC):
    """Interface for file validation."""

    @abstractmethod
    def validate_file(
        self,
        url: str,
        key: str,
        expected_mime: str | None = None,
        expected_mime_any: list[str] | None = None,
        min_size_kb: float | None = None,
    ) -> tuple[bool, str | None, float | None]:
        """
        Validate file accessibility and metadata.

        Returns (is_valid, mime, size_kb).
        """


class IHTTPClient(ABC):
    """Interface for HTTP client."""

    @abstractmethod
    def get(self, url: str) -> Any:  # HTTPResponse
        """Make GET request."""

    @abstractmethod
    def head(self, url: str) -> Any:  # HTTPResponse
        """Make HEAD request."""

    @abstractmethod
    def stream(self, url: str) -> Any:  # HTTPStreamResponse
        """Make streaming GET request."""

    @abstractmethod
    def close(self) -> None:
        """Close HTTP client."""

    @abstractmethod
    def __enter__(self) -> "IHTTPClient":
        """Context manager entry."""

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""


class IHTMLParser(ABC):
    """Interface for HTML parsing."""

    @abstractmethod
    def fetch_html(self, url: str) -> Any:  # HTMLSoup
        """Fetch and parse HTML from URL."""

    @abstractmethod
    def find_links(
        self,
        soup: Any,  # HTMLSoup
        base_url: str,
        pattern: str | None = None,
        text_contains: list[str] | None = None,
        ext: list[str] | None = None,
    ) -> list[tuple[str, str]]:
        """
        Find links matching criteria.

        Returns list of (href, text) tuples with absolute URLs (normalized).
        """


class IValidationRules(ABC):
    """Interface for validation rules."""

    @abstractmethod
    def validate_mime(self, key: str, mime: str) -> bool:
        """Validate MIME type for key."""

    @abstractmethod
    def validate_size(self, key: str, size_kb: float) -> bool:
        """Validate size for key."""

    @abstractmethod
    def get_expected_mime(self, key: str) -> str | None:
        """Get expected MIME type for key."""

    @abstractmethod
    def get_expected_mime_any(self, key: str) -> list[str] | None:
        """Get list of expected MIME types for key."""

    @abstractmethod
    def get_min_size_kb(self, key: str) -> float | None:
        """Get minimum size in KB for key."""

    @abstractmethod
    def get_discontinuity_notes(self, key: str) -> str | None:
        """Get discontinuity notes for key."""


class IContractRepository(ABC):
    """Interface for contract repository."""

    @abstractmethod
    def load_contracts(self) -> list[dict[str, Any]]:
        """Load all contracts."""

    @abstractmethod
    def get_contract(self, key: str) -> dict[str, Any] | None:
        """Get contract for a specific key."""

    @abstractmethod
    def get_all_keys(self) -> list[str]:
        """Get all contract keys."""
