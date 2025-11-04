"""Base discoverer implementation."""

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.domain.interfaces.http_port import IHTTPPort
from autodiscovery.domain.interfaces.source_discoverer_port import ISourceDiscovererPort


class BaseDiscoverer(ISourceDiscovererPort):
    """Base class for source discoverers."""

    def __init__(self, client: IHTTPPort):
        self.client = client

    def discover(self, start_urls: list[str]) -> DiscoveredFile | None:
        """
        Discover file from start URLs.

        Returns DiscoveredFile if found, None otherwise.
        """
        raise NotImplementedError
