"""BCRA infomodia discoverer."""

import logging
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.html import fetch_html, find_links
from autodiscovery.http import HTTPClient
from autodiscovery.sources.base import BaseDiscoverer
from autodiscovery.util.date import version_from_date_filename

logger = logging.getLogger(__name__)


class BCRAInfomodiaDiscoverer(BaseDiscoverer):
    """Discoverer for BCRA infomodia-YYYY-MM-DD.xls files."""

    def discover(self, start_urls: List[str]) -> Optional[DiscoveredFile]:
        """Discover latest infomodia-YYYY-MM-DD.xls file."""
        pattern = r"infomodia-(\d{4}-\d{2}-\d{2})\.xls"
        candidates = []

        for url in start_urls:
            try:
                soup = fetch_html(url, self.client)
                links = find_links(soup, url)

                # Find all matches
                for link_url, link_text in links:
                    parsed = urlparse(link_url)
                    filename = Path(parsed.path).name

                    match = re.search(pattern, filename, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        candidates.append((link_url, date_str, filename))

            except Exception as e:
                logger.warning(f"Failed to discover from {url}: {e}")
                continue

        if not candidates:
            return None

        # Sort by date (most recent first)
        candidates.sort(key=lambda x: x[1], reverse=True)
        latest_url, latest_date, latest_filename = candidates[0]

        # Validate and create
        discovered = self._validate_and_create(latest_url, latest_date, latest_filename)
        return discovered

    def _validate_and_create(
        self, url: str, date_str: str, filename: str
    ) -> Optional[DiscoveredFile]:
        """Validate URL and create DiscoveredFile."""
        try:
            response = self.client.head(url)
            mime = response.headers.get("content-type", "").split(";")[0].strip()
            size_bytes = int(response.headers.get("content-length", 0))
            size_kb = size_bytes / 1024.0

            version = version_from_date_filename(date_str)

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

