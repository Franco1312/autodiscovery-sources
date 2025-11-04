"""HTML parser implementation."""

import logging
from urllib.parse import quote, urljoin, urlparse

from bs4 import BeautifulSoup

from autodiscovery.domain.interfaces.html_port import IHTMLPort
from autodiscovery.domain.interfaces.http_port import IHTTPPort

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


class HTMLParser(IHTMLPort):
    """Implementation of HTML parser using BeautifulSoup."""

    def __init__(self, http_port: IHTTPPort):
        self.http_port = http_port

    def fetch_html(self, url: str):
        """Fetch and parse HTML from URL."""
        if self.http_port is None:
            raise ValueError("HTTP port is required for fetch_html")
        response = self.http_port.get(url)
        soup = BeautifulSoup(response.content, "lxml")
        return soup

    def extract_links(
        self,
        html,
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
        links = []
        for anchor in html.find_all("a", href=True):
            href = anchor.get("href", "")
            text = anchor.get_text(strip=True)

            # Resolve relative URLs using urljoin
            absolute_url = urljoin(base_url, href)

            # Normalize URL (encode spaces, special chars, accents)
            absolute_url = normalize_url(absolute_url)

            links.append((absolute_url, text))

        return links
