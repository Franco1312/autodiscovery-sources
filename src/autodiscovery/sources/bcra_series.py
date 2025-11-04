"""BCRA series.xlsm discoverer."""

import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.html import fetch_html, find_links
from autodiscovery.http import HTTPClient
from autodiscovery.sources.base import BaseDiscoverer
from autodiscovery.util.date import version_from_date_today

logger = logging.getLogger(__name__)


class BCRASeriesDiscoverer(BaseDiscoverer):
    """Discoverer for BCRA series.xlsm file."""

    def discover(self, start_urls: List[str]) -> Optional[DiscoveredFile]:
        """Discover series.xlsm file from BCRA PublicacionesEstadisticas pages."""
        target_filename = "series.xlsm"

        for url in start_urls:
            try:
                soup = fetch_html(url, self.client)
                links = find_links(soup, url)

                # Find exact match for series.xlsm
                for link_url, link_text in links:
                    parsed = urlparse(link_url)
                    filename = Path(parsed.path).name

                    if filename.lower() == target_filename.lower():
                        # Prefer links from Pdfs/PublicacionesEstadisticas/series.xlsm
                        if "Pdfs/PublicacionesEstadisticas" in link_url:
                            discovered = self._validate_and_create(link_url)
                            if discovered:
                                return discovered

                # If no preferred path found, try any series.xlsm
                for link_url, link_text in links:
                    parsed = urlparse(link_url)
                    filename = Path(parsed.path).name

                    if filename.lower() == target_filename.lower():
                        discovered = self._validate_and_create(link_url)
                        if discovered:
                            return discovered

            except Exception as e:
                logger.warning(f"Failed to discover from {url}: {e}")
                continue

        return None

    def _validate_and_create(self, url: str) -> Optional[DiscoveredFile]:
        """Validate URL and create DiscoveredFile."""
        try:
            response = self.client.head(url)
            mime = response.headers.get("content-type", "").split(";")[0].strip()
            size_bytes = int(response.headers.get("content-length", 0))
            size_kb = size_bytes / 1024.0

            filename = Path(urlparse(url).path).name
            version = version_from_date_today()

            return DiscoveredFile(
                url=url,
                version=version,
                filename=filename,
                mime=mime,
                size_kb=size_kb,
            )
        except Exception as e:
            logger.warning(f"Failed to validate {url}: {e}")
            return None

