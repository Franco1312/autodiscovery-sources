"""Domain interfaces (ports)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from autodiscovery.domain.entities import DiscoveredFile, SourceEntry

if TYPE_CHECKING:
    from typing import Protocol
    HTTPResponse = Any  # Protocol for HTTP response
    HTTPStreamResponse = Any  # Protocol for HTTP stream response
    HTMLSoup = Any  # Protocol for HTML soup


class ISourceDiscoverer(ABC):
    """Interface for source discoverers."""

    @abstractmethod
    def discover(self, start_urls: List[str]) -> Optional[DiscoveredFile]:
        """
        Discover file from start URLs.

        Returns DiscoveredFile if found, None otherwise.
        """
        pass


class IRegistryRepository(ABC):
    """Interface for registry repository."""

    @abstractmethod
    def get_entry(self, key: str) -> Optional[SourceEntry]:
        """Get entry by key."""
        pass

    @abstractmethod
    def set_entry(self, key: str, entry: SourceEntry) -> None:
        """Set entry by key."""
        pass

    @abstractmethod
    def has_entry(self, key: str) -> bool:
        """Check if entry exists."""
        pass

    @abstractmethod
    def list_keys(self) -> List[str]:
        """List all keys in registry."""
        pass


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
        pass


class IFileValidator(ABC):
    """Interface for file validation."""

    @abstractmethod
    def validate_file(
        self,
        url: str,
        key: str,
        expected_mime: Optional[str] = None,
        expected_mime_any: Optional[List[str]] = None,
        min_size_kb: Optional[float] = None,
    ) -> tuple[bool, Optional[str], Optional[float]]:
        """
        Validate file accessibility and metadata.

        Returns (is_valid, mime, size_kb).
        """
        pass


class IHTTPClient(ABC):
    """Interface for HTTP client."""

    @abstractmethod
    def get(self, url: str) -> Any:  # HTTPResponse
        """Make GET request."""
        pass

    @abstractmethod
    def head(self, url: str) -> Any:  # HTTPResponse
        """Make HEAD request."""
        pass

    @abstractmethod
    def stream(self, url: str) -> Any:  # HTTPStreamResponse
        """Make streaming GET request."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close HTTP client."""
        pass

    @abstractmethod
    def __enter__(self) -> "IHTTPClient":
        """Context manager entry."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        pass


class IHTMLParser(ABC):
    """Interface for HTML parsing."""

    @abstractmethod
    def fetch_html(self, url: str) -> Any:  # HTMLSoup
        """Fetch and parse HTML from URL."""
        pass

    @abstractmethod
    def find_links(
        self,
        soup: Any,  # HTMLSoup
        base_url: str,
        pattern: Optional[str] = None,
        text_contains: Optional[List[str]] = None,
        ext: Optional[List[str]] = None,
    ) -> List[Tuple[str, str]]:
        """
        Find links matching criteria.

        Returns list of (href, text) tuples with absolute URLs (normalized).
        """
        pass


class IValidationRules(ABC):
    """Interface for validation rules."""

    @abstractmethod
    def validate_mime(self, key: str, mime: str) -> bool:
        """Validate MIME type for key."""
        pass

    @abstractmethod
    def validate_size(self, key: str, size_kb: float) -> bool:
        """Validate size for key."""
        pass

    @abstractmethod
    def get_expected_mime(self, key: str) -> Optional[str]:
        """Get expected MIME type for key."""
        pass

    @abstractmethod
    def get_expected_mime_any(self, key: str) -> Optional[List[str]]:
        """Get list of expected MIME types for key."""
        pass

    @abstractmethod
    def get_min_size_kb(self, key: str) -> Optional[float]:
        """Get minimum size in KB for key."""
        pass

    @abstractmethod
    def get_discontinuity_notes(self, key: str) -> Optional[str]:
        """Get discontinuity notes for key."""
        pass


class IContractRepository(ABC):
    """Interface for contract repository."""

    @abstractmethod
    def load_contracts(self) -> List[Dict[str, Any]]:
        """Load all contracts."""
        pass

    @abstractmethod
    def get_contract(self, key: str) -> Optional[Dict[str, Any]]:
        """Get contract for a specific key."""
        pass

    @abstractmethod
    def get_all_keys(self) -> List[str]:
        """Get all contract keys."""
        pass

