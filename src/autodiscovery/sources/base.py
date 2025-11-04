"""Base discoverer implementation."""

from typing import List, Optional

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.domain.interfaces import ISourceDiscoverer
from autodiscovery.http import HTTPClient


class BaseDiscoverer(ISourceDiscoverer):
    """Base class for source discoverers."""

    def __init__(self, client: HTTPClient):
        self.client = client

    def discover(self, start_urls: List[str]) -> Optional[DiscoveredFile]:
        """
        Discover file from start URLs.

        Returns DiscoveredFile if found, None otherwise.
        """
        raise NotImplementedError

