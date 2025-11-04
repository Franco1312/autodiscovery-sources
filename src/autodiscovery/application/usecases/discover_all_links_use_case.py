"""Use case for discovering all links from all sources."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from autodiscovery.infrastructure.discoverer_factory import DiscovererFactory
from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.domain.interfaces import IFileValidator, IHTMLParser, IHTTPClient

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredLink:
    """Represents a discovered link."""

    url: str
    text: str
    source_page: str
    status: str = "ok"
    mime: Optional[str] = None
    size_kb: Optional[float] = None
    size_bytes: Optional[int] = None
    content_disposition: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SourceLinksResult:
    """Result for a single source."""

    key: str
    start_urls: List[str]
    links_found: List[DiscoveredLink]
    selected_link: Optional[Dict] = None
    filter_extensions: Optional[List[str]] = None
    error: Optional[str] = None


@dataclass
class DiscoverAllLinksResult:
    """Result of discover all links use case."""

    sources: Dict[str, SourceLinksResult]
    total_links: int
    valid_links: int
    selected_links: int


class DiscoverAllLinksUseCase:
    """Use case for discovering all links from all sources."""

    def __init__(
        self,
        contract_service: ContractService,
        file_validator: Optional[IFileValidator],
        http_client: IHTTPClient,
        html_parser: IHTMLParser,
    ):
        self.contract_service = contract_service
        self.file_validator = file_validator
        self.http_client = http_client
        self.html_parser = html_parser

    def execute(
        self,
        filter_extensions: Optional[List[str]] = None,
        validate: bool = True,
    ) -> DiscoverAllLinksResult:
        """
        Execute the discover all links use case.

        Args:
            filter_extensions: List of file extensions to filter by
            validate: Whether to validate links with HEAD request

        Returns:
            DiscoverAllLinksResult with all discovered links
        """
        contracts = self.contract_service.load_contracts()
        sources_data = {}

        for contract in contracts:
            key = contract.get("key")
            if not key:
                continue

            discoverer = DiscovererFactory.create(key, self.http_client)
            if not discoverer:
                logger.warning(f"Discoverer not found for key: {key}")
                continue

            start_urls = contract.get("start_urls", [])
            logger.info(f"Discovering links for {key} from {len(start_urls)} URLs")

            source_result = SourceLinksResult(
                key=key,
                start_urls=start_urls,
                links_found=[],
                selected_link=None,
                filter_extensions=filter_extensions,
            )

            try:
                # Extract all links from each start URL
                for start_url in start_urls:
                    try:
                        soup = self.html_parser.fetch_html(start_url)
                        all_links = self.html_parser.find_links(
                            soup, start_url, ext=filter_extensions if filter_extensions else None
                        )
                        logger.info(f"Found {len(all_links)} links from {start_url}")

                        # Process each link
                        for link_url, link_text in all_links:
                            # Verify extension if filtered
                            if filter_extensions:
                                parsed = urlparse(link_url)
                                file_ext = Path(parsed.path).suffix.lower()
                                if file_ext not in [e.lower() for e in filter_extensions]:
                                    continue

                            # Validate link if requested
                            link_data = DiscoveredLink(
                                url=link_url,
                                text=link_text,
                                source_page=start_url,
                            )

                            if validate and self.file_validator:
                                try:
                                    is_valid, mime, size_kb = self.file_validator.validate_file(
                                        link_url, key
                                    )
                                    if is_valid:
                                        link_data.status = "ok"
                                        link_data.mime = mime
                                        link_data.size_kb = size_kb
                                        link_data.size_bytes = int(size_kb * 1024) if size_kb else None
                                        source_result.links_found.append(link_data)
                                        logger.debug(f"✓ Valid file: {link_url} (MIME: {mime}, size: {size_kb:.2f} KB)")
                                    else:
                                        # Log why it was rejected for debugging
                                        logger.debug(f"✗ Link rejected: {link_url} (MIME: {mime or 'unknown'}, size: {size_kb or 0:.2f} KB)")
                                        continue
                                except Exception as e:
                                    logger.debug(f"✗ Link validation error: {link_url} - {e}")
                                    continue
                            else:
                                # No validation, add all links
                                source_result.links_found.append(link_data)

                    except Exception as e:
                        logger.warning(f"Failed to fetch links from {start_url}: {e}")
                        source_result.links_found.append(
                            DiscoveredLink(
                                url="",
                                text="",
                                source_page=start_url,
                                status="error",
                                error=str(e),
                            )
                        )

                # Try to discover selected link
                try:
                    discovered = discoverer.discover(start_urls)
                    if discovered:
                        source_result.selected_link = {
                            "url": discovered.url,
                            "version": discovered.version,
                            "filename": discovered.filename,
                            "mime": discovered.mime,
                            "size_kb": discovered.size_kb,
                        }
                except Exception as e:
                    logger.warning(f"Failed to discover selected link for {key}: {e}")
                    source_result.selected_link = {"error": str(e)}

            except Exception as e:
                logger.error(f"Failed to process {key}: {e}")
                source_result.error = str(e)

            sources_data[key] = source_result

        # Calculate totals
        total_links = sum(len(data.links_found) for data in sources_data.values())
        valid_links = sum(
            len([l for l in data.links_found if l.status == "ok"])
            for data in sources_data.values()
        )
        selected_count = sum(
            1
            for data in sources_data.values()
            if data.selected_link and "error" not in data.selected_link
        )

        return DiscoverAllLinksResult(
            sources=sources_data,
            total_links=total_links,
            valid_links=valid_links,
            selected_links=selected_count,
        )

