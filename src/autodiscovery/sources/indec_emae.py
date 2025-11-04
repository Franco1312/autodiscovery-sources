"""INDEC EMAE discoverer."""

import logging
from pathlib import Path
from urllib.parse import urlparse

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.infrastructure.html_parser import HTMLParser
from autodiscovery.sources.base import BaseDiscoverer
from autodiscovery.util.date import version_from_date_today

logger = logging.getLogger(__name__)


class INDECEMAEDiscoverer(BaseDiscoverer):
    """Discoverer for INDEC EMAE files."""

    def discover(self, start_urls: list[str]) -> DiscoveredFile | None:
        """Discover EMAE file using fuzzy text matching."""
        keywords = ["EMAE", "Estimador mensual de actividad económica"]
        extensions = [".xlsx", ".xls", ".csv", ".pdf"]
        candidates = []

        for url in start_urls:
            try:
                html_parser = HTMLParser(self.client)
                soup = html_parser.fetch_html(url)
                links = html_parser.extract_links(soup, url)
                # Filter by extension and text
                links = [
                    link
                    for link in links
                    if any(link[0].lower().endswith(ext) for ext in extensions)
                    and any(kw.lower() in link[1].lower() for kw in keywords)
                ]

                # Prioritize .xlsx over .pdf
                for link_url, _link_text in links:
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

    def _validate_and_create(self, url: str, filename: str) -> DiscoveredFile | None:
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
