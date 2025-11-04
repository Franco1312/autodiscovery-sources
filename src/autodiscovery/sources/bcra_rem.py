"""BCRA REM discoverer."""

import logging
import re
from pathlib import Path
from urllib.parse import urlparse

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.infrastructure.html_parser import HTMLParser
from autodiscovery.sources.base import BaseDiscoverer
from autodiscovery.util.date import normalize_spanish_month, version_from_year_month

logger = logging.getLogger(__name__)


class BCRAREMDiscoverer(BaseDiscoverer):
    """Discoverer for BCRA REM PDF files."""

    def discover(self, start_urls: list[str]) -> DiscoveredFile | None:
        """Discover latest REM PDF file."""
        # Pattern: relevamiento-expectativas-mercado-<month>-<year>.pdf
        # Month can be in Spanish (full or abbreviated)
        pattern = r"relevamiento-expectativas-mercado-(\w+)-(\d{4})\.pdf"
        candidates = []

        for url in start_urls:
            try:
                html_parser = HTMLParser(self.client)
                soup = html_parser.fetch_html(url)
                links = html_parser.extract_links(soup, url)
                # Filter by extension
                links = [link for link in links if link[0].lower().endswith(".pdf")]

                # Find all REM PDFs
                for link_url, _link_text in links:
                    parsed = urlparse(link_url)
                    filename = Path(parsed.path).name

                    match = re.search(pattern, filename, re.IGNORECASE)
                    if match:
                        month_str, year_str = match.groups()
                        candidates.append((link_url, year_str, month_str, filename))

            except Exception as e:
                logger.warning(f"Failed to discover from {url}: {e}")
                continue

        if not candidates:
            return None

        # Sort by year-month (most recent first)
        def sort_key(item):
            year, month_str = item[1], item[2]
            month_num = normalize_spanish_month(month_str)
            if month_num:
                return (year, month_num)
            return (year, "00")

        candidates.sort(key=sort_key, reverse=True)
        latest_url, year, month, filename = candidates[0]

        # Validate and create
        version = version_from_year_month(year, month)
        discovered = self._validate_and_create(latest_url, version, filename)
        return discovered

    def _validate_and_create(self, url: str, version: str, filename: str) -> DiscoveredFile | None:
        """Validate URL and create DiscoveredFile."""
        try:
            response = self.client.head(url)
            mime = response.headers.get("content-type", "").split(";")[0].strip()
            size_bytes = int(response.headers.get("content-length", 0))
            size_kb = size_bytes / 1024.0

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
