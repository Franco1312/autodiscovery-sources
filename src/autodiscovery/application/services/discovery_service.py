"""Service for discovering sources."""

import logging

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.domain.interfaces.source_discoverer_port import ISourceDiscovererPort

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Service for discovering sources."""

    def __init__(self, discoverer: ISourceDiscovererPort):
        self.discoverer = discoverer

    def discover(self, start_urls: list[str]) -> DiscoveredFile | None:
        """
        Discover file from start URLs.

        Args:
            start_urls: List of URLs to start discovery from

        Returns:
            DiscoveredFile if found, None otherwise
        """
        try:
            return self.discoverer.discover(start_urls)
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return None
