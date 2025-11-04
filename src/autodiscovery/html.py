"""HTML parsing utilities (backward compatibility)."""

import logging
from typing import List, Optional

from bs4 import BeautifulSoup

from autodiscovery.http import HTTPClient
from autodiscovery.infrastructure.html_parser import HTMLParser, normalize_url

logger = logging.getLogger(__name__)

# Backward compatibility functions
def fetch_html(url: str, client: HTTPClient) -> BeautifulSoup:
    """Fetch and parse HTML from URL (backward compatibility)."""
    parser = HTMLParser(client)
    return parser.fetch_html(url)


def find_links(
    soup: BeautifulSoup,
    base_url: str,
    pattern: Optional[str] = None,
    text_contains: Optional[List[str]] = None,
    ext: Optional[List[str]] = None,
) -> List[tuple[str, str]]:
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
    return parser.find_links(soup, base_url, pattern, text_contains, ext)


def fuzzy_text_match(
    text: str,
    keywords: List[str],
    threshold: int = 2,
) -> bool:
    """
    Fuzzy match text against keywords.

    Returns True if at least one keyword appears in text (case-insensitive).
    """
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True
    return False

