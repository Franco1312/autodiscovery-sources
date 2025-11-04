"""Base discoverer implementation."""

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.domain.interfaces import ISourceDiscoverer
from autodiscovery.http import HTTPClient


class BaseDiscoverer(ISourceDiscoverer):
    """Base class for source discoverers."""

    def __init__(self, client: HTTPClient):
        self.client = client

    def discover(self, start_urls: list[str]) -> DiscoveredFile | None:
        """
        Discover file from start URLs.

        Returns DiscoveredFile if found, None otherwise.
        """
        raise NotImplementedError
