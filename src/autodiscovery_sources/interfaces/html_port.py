"""Port for HTML parsing and link extraction."""

from abc import ABC, abstractmethod
from typing import List, Tuple


class HtmlPort(ABC):
    """Port for HTML parsing."""

    @abstractmethod
    def extract_links(self, html: str, base_url: str) -> List[Tuple[str, str]]:
        """Extract links from HTML.
        
        Returns:
            List of tuples (href, anchor_text)
        """
        pass

