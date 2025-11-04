"""HTML parser implementation."""

import logging
from urllib.parse import quote, urljoin, urlparse

from bs4 import BeautifulSoup

from autodiscovery.domain.interfaces import IHTMLParser, IHTTPClient

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """
    Normalize URL by encoding spaces and special characters.

    Preserves the structure but encodes path components.
    """
    parsed = urlparse(url)

    # Encode the path component (spaces, special chars)
    if parsed.path:
        # Split path into components and encode each part
        path_parts = parsed.path.split("/")
        encoded_parts = [quote(part, safe="") for part in path_parts]
        encoded_path = "/".join(encoded_parts)
    else:
        encoded_path = parsed.path

    # Reconstruct URL with encoded path
    normalized = parsed._replace(path=encoded_path).geturl()
    return normalized


class HTMLParser(IHTMLParser):
    """Implementation of HTML parser using BeautifulSoup."""

    def __init__(self, http_client: IHTTPClient):
        self.http_client = http_client

    def fetch_html(self, url: str) -> BeautifulSoup:
        """Fetch and parse HTML from URL."""
        if self.http_client is None:
            raise ValueError("HTTP client is required for fetch_html")
        response = self.http_client.get(url)
        soup = BeautifulSoup(response.content, "lxml")
        return soup

    def find_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
        pattern: str | None = None,
        text_contains: list[str] | None = None,
        ext: list[str] | None = None,
    ) -> list[tuple[str, str]]:
        """
        Find links matching criteria.

        Returns list of (href, text) tuples with absolute URLs (normalized).
        """
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            text = anchor.get_text(strip=True)

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)

            # Normalize URL (encode spaces and special characters)
            absolute_url = normalize_url(absolute_url)

            # Filter by extension if specified
            if ext:
                parsed = urlparse(absolute_url)
                if not any(parsed.path.lower().endswith(e.lower()) for e in ext):
                    continue

            # Filter by text contains if specified
            if text_contains and not any(term.lower() in text.lower() for term in text_contains):
                continue

            # Filter by pattern if specified
            if pattern:
                import re

                if not re.search(pattern, absolute_url, re.IGNORECASE):
                    continue

            links.append((absolute_url, text))

        return links
