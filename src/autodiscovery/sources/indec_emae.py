"""INDEC EMAE discoverer."""

import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from autodiscovery.html import fetch_html, find_links
from autodiscovery.http import HTTPClient
from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.sources.base import BaseDiscoverer
from autodiscovery.util.date import version_from_date_today

logger = logging.getLogger(__name__)


class INDECEMAEDiscoverer(BaseDiscoverer):
    """Discoverer for INDEC EMAE files."""

    def discover(self, start_urls: List[str]) -> Optional[DiscoveredFile]:
        """Discover EMAE file using fuzzy text matching."""
        keywords = ["EMAE", "Estimador mensual de actividad económica"]
        extensions = [".xlsx", ".xls", ".csv", ".pdf"]
        candidates = []

        for url in start_urls:
            try:
                soup = fetch_html(url, self.client)
                links = find_links(
                    soup,
                    url,
                    text_contains=keywords,
                    ext=extensions,
                )

                # Prioritize .xlsx over .pdf
                for link_url, link_text in links:
                    parsed = urlparse(link_url)
                    filename = Path(parsed.path).name
                    ext = Path(parsed.path).suffix.lower()

                    # Priority: .xlsx > .xls > .csv > .pdf
                    priority = {".xlsx": 4, ".xls": 3, ".csv": 2, ".pdf": 1}.get(ext, 0)
                    candidates.append((link_url, filename, priority, ext))

            except Exception as e:
                logger.warning(f"Failed to discover from {url}: {e}")
                continue

        if not candidates:
            return None

        # Sort by priority (highest first), then by URL
        candidates.sort(key=lambda x: (x[2], x[0]), reverse=True)
        latest_url, filename, _, ext = candidates[0]

        # Validate and create
        discovered = self._validate_and_create(latest_url, filename)
        return discovered

    def _validate_and_create(self, url: str, filename: str) -> Optional[DiscoveredFile]:
        """Validate URL and create DiscoveredFile."""
        try:
            response = self.client.head(url)
            mime = response.headers.get("content-type", "").split(";")[0].strip()
            size_bytes = int(response.headers.get("content-length", 0))
            size_kb = size_bytes / 1024.0

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

