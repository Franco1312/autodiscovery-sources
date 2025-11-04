"""HTML parsing utilities (backward compatibility)."""

import logging

from bs4 import BeautifulSoup

from autodiscovery.http import HTTPClient
from autodiscovery.infrastructure.html_parser import HTMLParser

logger = logging.getLogger(__name__)


# Backward compatibility functions
def fetch_html(url: str, client: HTTPClient) -> BeautifulSoup:
    """Fetch and parse HTML from URL (backward compatibility)."""
    parser = HTMLParser(client)
    return parser.fetch_html(url)


def find_links(
    soup: BeautifulSoup,
    base_url: str,
    pattern: str | None = None,
    text_contains: list[str] | None = None,
    ext: list[str] | None = None,
) -> list[tuple[str, str]]:
    """
    Find links matching criteria (backward compatibility).

    Returns list of (href, text) tuples with absolute URLs (normalized).
    """
    # Create a temporary parser for backward compatibility
    # In new code, use HTMLParser directly
    from autodiscovery.infrastructure.html_parser import HTMLParser

    # Create a dummy parser that only uses find_links (doesn't need http_client)
    class DummyParser(HTMLParser):
        def __init__(self):
            pass  # Skip parent init

        def find_links(self, soup, base_url, pattern=None, text_contains=None, ext=None):
            return super().find_links(soup, base_url, pattern, text_contains, ext)

    parser = DummyParser()
    result = parser.find_links(soup, base_url, pattern, text_contains, ext)
    return result  # type: ignore[no-any-return]


def fuzzy_text_match(
    text: str,
    keywords: list[str],
    threshold: int = 2,
) -> bool:
    """
    Fuzzy match text against keywords.

    Returns True if at least one keyword appears in text (case-insensitive).
    """
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)
