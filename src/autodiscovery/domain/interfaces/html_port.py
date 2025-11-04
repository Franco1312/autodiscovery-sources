"""HTML port interface."""

from abc import ABC, abstractmethod
from typing import Any, Protocol


class HTMLSoup(Protocol):
    """Protocol for HTML soup (BeautifulSoup-like)."""

    def find_all(self, tag: str, **kwargs) -> list:
        """Find all elements matching criteria."""

    def find(self, tag: str, **kwargs) -> Any:
        """Find first element matching criteria."""


class IHTMLPort(ABC):
    """Port for HTML parsing and link extraction."""

    @abstractmethod
    def fetch_html(self, url: str) -> HTMLSoup:
        """
        Fetch and parse HTML from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML soup object
        """

    @abstractmethod
    def extract_links(
        self,
        html: HTMLSoup,
        base_url: str,
    ) -> list[tuple[str, str]]:
        """
        Extract all links from HTML and normalize URLs.

        Args:
            html: HTML soup object
            base_url: Base URL for resolving relative links

        Returns:
            List of (href, text) tuples with normalized absolute URLs
        """
