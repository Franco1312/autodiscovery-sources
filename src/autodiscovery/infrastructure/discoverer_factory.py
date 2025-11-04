"""Factory for creating discoverers."""

import logging
from typing import Dict, List, Optional, Type

from autodiscovery.domain.interfaces import IHTTPClient, ISourceDiscoverer
from autodiscovery.sources.bcra_infomodia import BCRAInfomodiaDiscoverer
from autodiscovery.sources.bcra_rem import BCRAREMDiscoverer
from autodiscovery.sources.bcra_series import BCRASeriesDiscoverer
from autodiscovery.sources.indec_emae import INDECEMAEDiscoverer

logger = logging.getLogger(__name__)


class DiscovererFactory:
    """Factory for creating source discoverers."""

    # Registry of discoverer classes by key
    _discoverers: Dict[str, Type[ISourceDiscoverer]] = {
        "bcra_series": BCRASeriesDiscoverer,
        "bcra_infomodia": BCRAInfomodiaDiscoverer,
        "bcra_rem_pdf": BCRAREMDiscoverer,
        "indec_emae": INDECEMAEDiscoverer,
    }

    @classmethod
    def create(cls, key: str, client: IHTTPClient) -> Optional[ISourceDiscoverer]:
        """
        Create a discoverer for the given key.

        Args:
            key: Source key
            client: HTTP client instance

        Returns:
            ISourceDiscoverer instance or None if key not found
        """
        discoverer_class = cls._discoverers.get(key)
        if not discoverer_class:
            logger.warning(f"Discoverer not found for key: {key}")
            return None

        try:
            return discoverer_class(client)
        except Exception as e:
            logger.error(f"Failed to create discoverer for {key}: {e}")
            return None

    @classmethod
    def register(cls, key: str, discoverer_class: Type[ISourceDiscoverer]) -> None:
        """
        Register a new discoverer class.

        Args:
            key: Source key
            discoverer_class: Discoverer class implementing ISourceDiscoverer
        """
        cls._discoverers[key] = discoverer_class
        logger.debug(f"Registered discoverer for key: {key}")

    @classmethod
    def get_available_keys(cls) -> List[str]:
        """Get list of available discoverer keys."""
        return list(cls._discoverers.keys())

