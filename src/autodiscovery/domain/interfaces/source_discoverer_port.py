"""Source discoverer port interface."""

from abc import ABC, abstractmethod

from autodiscovery.domain.entities import DiscoveredFile


class ISourceDiscovererPort(ABC):
    """Port for source discovery operations."""

    @abstractmethod
    def discover(self, start_urls: list[str]) -> DiscoveredFile | None:
        """
        Discover file from start URLs.

        Returns DiscoveredFile if found, None otherwise.
        """
