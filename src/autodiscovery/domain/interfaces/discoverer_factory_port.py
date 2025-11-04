"""Port for discoverer factory."""

from abc import ABC, abstractmethod

from autodiscovery.domain.interfaces.http_port import IHTTPPort
from autodiscovery.domain.interfaces.source_discoverer_port import ISourceDiscovererPort


class IDiscovererFactoryPort(ABC):
    """Port for creating discoverers based on source key."""

    @abstractmethod
    def create(self, key: str, http_client: IHTTPPort) -> ISourceDiscovererPort | None:
        """
        Create a discoverer for the given source key.

        Args:
            key: Source key identifier
            http_client: HTTP client port

        Returns:
            Discoverer instance or None if not found
        """
