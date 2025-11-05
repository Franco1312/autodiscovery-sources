"""BeautifulSoup adapter for HTML parsing."""

from typing import List, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ..interfaces.html_port import HtmlPort
from .urltools import urljoin_safe


class Bs4Adapter(HtmlPort):
    """BeautifulSoup adapter for HTML parsing."""

    def __init__(self):
        """Initialize adapter."""
        pass

    def extract_links(self, html: str, base_url: str) -> List[Tuple[str, str]]:
        """Extract links from HTML."""
        soup = BeautifulSoup(html, "lxml")
        links = []
        base_parsed = urlparse(base_url)
        
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            text = anchor.get_text(strip=True)
            
            if not href:
                continue
            
            # Resolve relative URLs
            if href.startswith("//"):
                href = f"{base_parsed.scheme}:{href}"
            elif href.startswith("/"):
                href = urljoin(base_url, href)
            elif not href.startswith(("http://", "https://")):
                href = urljoin_safe(base_url, href)
            
            # Clean up href
            href = href.split("#")[0]  # Remove fragment
            href = href.split("?")[0] if "?" in href else href  # Remove query params for now
            
            links.append((href, text))
        
        return links

