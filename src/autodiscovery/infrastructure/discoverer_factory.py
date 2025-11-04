"""Factory for creating discoverers."""

import logging

from autodiscovery.domain.interfaces.discoverer_factory_port import IDiscovererFactoryPort
from autodiscovery.domain.interfaces.http_port import IHTTPPort
from autodiscovery.domain.interfaces.source_discoverer_port import ISourceDiscovererPort
from autodiscovery.sources.bcra_infomodia import BCRAInfomodiaDiscoverer
from autodiscovery.sources.bcra_rem import BCRAREMDiscoverer
from autodiscovery.sources.bcra_series import BCRASeriesDiscoverer
from autodiscovery.sources.indec_emae import INDECEMAEDiscoverer

logger = logging.getLogger(__name__)


class DiscovererFactory(IDiscovererFactoryPort):
    """Factory for creating source discoverers."""

    # Registry of discoverer classes by key
    _discoverers: dict[str, type[ISourceDiscovererPort]] = {
        "bcra_series": BCRASeriesDiscoverer,
        "bcra_infomodia_xls": BCRAInfomodiaDiscoverer,
        "bcra_infomodia_pdf": BCRAInfomodiaDiscoverer,  # Same discoverer, different format
        "bcra_rem_pdf": BCRAREMDiscoverer,
        "bcra_rem_xlsx": BCRAREMDiscoverer,  # Same discoverer, different format
        "indec_emae_api": INDECEMAEDiscoverer,
        # Legacy keys for backward compatibility
        "bcra_infomodia": BCRAInfomodiaDiscoverer,
        "indec_emae": INDECEMAEDiscoverer,
    }

    def create(self, key: str, http_client: IHTTPPort) -> ISourceDiscovererPort | None:
        """
        Create a discoverer for the given key.

        Args:
            key: Source key
            http_client: HTTP client instance

        Returns:
            ISourceDiscovererPort instance or None if key not found
        """
        discoverer_class = self._discoverers.get(key)
        if not discoverer_class:
            logger.warning(f"Discoverer not found for key: {key}")
            return None

        try:
            return discoverer_class(http_client)  # type: ignore[call-arg]
        except Exception as e:
            logger.error(f"Failed to create discoverer for {key}: {e}")
            return None

    @classmethod
    def register(cls, key: str, discoverer_class: type[ISourceDiscovererPort]) -> None:
        """
        Register a new discoverer class.

        Args:
            key: Source key
            discoverer_class: Discoverer class implementing ISourceDiscovererPort
        """
        cls._discoverers[key] = discoverer_class
        logger.debug(f"Registered discoverer for key: {key}")

    @classmethod
    def get_available_keys(cls) -> list[str]:
        """Get list of available discoverer keys."""
        return list(cls._discoverers.keys())
