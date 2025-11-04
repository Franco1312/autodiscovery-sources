"""Use case for discovering all links from all sources."""

import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.domain.interfaces.html_port import IHTMLPort
from autodiscovery.domain.interfaces.http_port import IHTTPPort
from autodiscovery.infrastructure.discoverer_factory import DiscovererFactory

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredLink:
    """Represents a discovered link."""

    url: str
    text: str
    source_page: str
    status: str = "ok"
    mime: str | None = None
    size_kb: float | None = None
    size_bytes: int | None = None
    content_disposition: str | None = None
    error: str | None = None


@dataclass
class SourceLinksResult:
    """Result for a single source."""

    key: str
    start_urls: list[str]
    links_found: list[DiscoveredLink]
    selected_link: dict | None = None
    filter_extensions: list[str] | None = None
    error: str | None = None


@dataclass
class DiscoverAllLinksResult:
    """Result of discover all links use case."""

    sources: dict[str, SourceLinksResult]
    total_links: int
    valid_links: int
    selected_links: int


class DiscoverAllLinksUseCase:
    """Use case for discovering all links from all sources."""

    def __init__(
        self,
        contract_service: ContractService,
        file_validator,  # FileValidator service (no port needed)
        http_client: IHTTPPort,
        html_parser: IHTMLPort,
    ):
        self.contract_service = contract_service
        self.file_validator = file_validator
        self.http_client = http_client
        self.html_parser = html_parser

    def execute(
        self,
        filter_extensions: list[str] | None = None,
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
                        all_links = self.html_parser.extract_links(soup, start_url)
                        # Filter by extension if needed
                        if filter_extensions:
                            all_links = [
                                link
                                for link in all_links
                                if any(link[0].lower().endswith(ext) for ext in filter_extensions)
                            ]
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
                                        link_data.size_bytes = (
                                            int(size_kb * 1024) if size_kb else None
                                        )
                                        source_result.links_found.append(link_data)
                                        logger.debug(
                                            f"✓ Valid file: {link_url} (MIME: {mime}, size: {size_kb:.2f} KB)"
                                        )
                                    else:
                                        # Log why it was rejected for debugging
                                        logger.debug(
                                            f"✗ Link rejected: {link_url} (MIME: {mime or 'unknown'}, size: {size_kb or 0:.2f} KB)"
                                        )
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
            len([link for link in data.links_found if link.status == "ok"])
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
