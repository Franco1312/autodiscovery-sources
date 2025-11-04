"""Use case for discovering all links from all sources."""

import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.application.services.link_crawler_service import LinkCrawlerService
from autodiscovery.application.services.pattern_matcher_service import PatternMatcherService
from autodiscovery.application.services.url_filter_service import URLFilterService
from autodiscovery.domain.interfaces.discoverer_factory_port import IDiscovererFactoryPort
from autodiscovery.domain.interfaces.html_port import IHTMLPort
from autodiscovery.domain.interfaces.http_port import IHTTPPort

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


@dataclass
class CrawlConfig:
    """Crawl configuration extracted from contract."""

    max_depth: int
    same_domain_only: bool
    follow_html: bool
    avoid_domains: list[str]
    avoid_keywords: list[str]
    match_patterns: list[str]
    match_keywords: list[str] | None


class DiscoverAllLinksUseCase:
    """Use case for discovering all links from all sources."""

    def __init__(
        self,
        contract_service: ContractService,
        file_validator,  # FileValidator service (no port needed)
        http_client: IHTTPPort,
        html_parser: IHTMLPort,
        discoverer_factory: IDiscovererFactoryPort,
    ):
        self.contract_service = contract_service
        self.file_validator = file_validator
        self.http_client = http_client
        self.html_parser = html_parser
        self.discoverer_factory = discoverer_factory

        # Initialize specialized services
        self.url_filter = URLFilterService(http_client)
        self.pattern_matcher = PatternMatcherService()
        self.link_crawler = LinkCrawlerService(self.url_filter, self.pattern_matcher, html_parser)

    # ========== Contract configuration extraction ==========

    def _extract_crawl_config(self, contract: dict) -> CrawlConfig:
        """Extract crawl configuration from contract."""
        crawl_config = contract.get("crawl", {})
        match_config = contract.get("match", {})
        match_patterns = match_config.get("patterns", []) if match_config else []

        return CrawlConfig(
            max_depth=crawl_config.get("max_depth", 0),
            same_domain_only=crawl_config.get("same_domain_only", True),
            follow_html=crawl_config.get("follow_html", True),
            avoid_domains=crawl_config.get("avoid_domains", []),
            avoid_keywords=crawl_config.get("avoid_keywords", []),
            match_patterns=match_patterns,
            match_keywords=self.pattern_matcher.extract_keywords_from_patterns(match_patterns)
            if match_patterns
            else None,
        )

    # ========== Link collection ==========

    def _collect_links_from_url(
        self,
        start_url: str,
        config: CrawlConfig,
        filter_extensions: list[str] | None,
        visited: set[str],
    ) -> list[tuple[str, str]]:
        """Collect links from a single start URL."""
        base_domain = self.url_filter.get_domain(start_url) if config.same_domain_only else None

        if config.follow_html and config.max_depth > 0:
            return self.link_crawler.crawl_recursive(
                start_url,
                config.max_depth,
                0,
                visited,
                config.same_domain_only,
                base_domain,
                filter_extensions,
                config.avoid_domains,
                config.avoid_keywords,
                config.match_patterns,
                config.match_keywords,
            )
        else:
            return self.link_crawler.extract_links_simple(start_url, filter_extensions)

    def _remove_duplicates(self, links: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """Remove duplicate links by URL."""
        seen = set()
        unique = []
        for url, text in links:
            if url not in seen:
                seen.add(url)
                unique.append((url, text))
        return unique

    # ========== Link validation and processing ==========

    def _sort_links_by_preference(
        self, links: list[tuple[str, str]], prefer_ext: list[str] | None
    ) -> list[tuple[str, str]]:
        """Sort links by extension preference (Excel/CSV first, PDF last)."""
        if not prefer_ext:
            return links

        from autodiscovery.domain.policies import SelectionPolicy

        candidates = [{"url": url, "text": text} for url, text in links]
        sorted_candidates = SelectionPolicy.prefer_ext(candidates, prefer_ext)
        return [(c["url"], c["text"]) for c in sorted_candidates]

    def _find_source_page(self, link_url: str, start_urls: list[str]) -> str:
        """Find which start URL this link came from."""
        for start in start_urls:
            if link_url.startswith(start) or self.url_filter.get_domain(
                link_url
            ) == self.url_filter.get_domain(start):
                return start
        return start_urls[0] if start_urls else ""

    def _validate_and_process_links(
        self,
        links: list[tuple[str, str]],
        contract: dict,
        key: str,
        start_urls: list[str],
        filter_extensions: list[str] | None,
        validate: bool,
    ) -> list[DiscoveredLink]:
        """Validate and process links into DiscoveredLink objects."""
        # Sort by extension preference
        select_config = contract.get("select", {})
        prefer_ext = select_config.get("prefer_ext", [])
        links = self._sort_links_by_preference(links, prefer_ext)

        # Get validation config
        expect_config = contract.get("expect", {})
        max_age_days = expect_config.get("max_age_days") if expect_config else None

        validated_links = []
        processed = 0
        validated = 0

        # Get avoid_keywords from contract
        crawl_config = contract.get("crawl", {})
        avoid_keywords = crawl_config.get("avoid_keywords", [])

        for link_url, link_text in links:
            processed += 1
            if processed % 50 == 0:
                logger.info(
                    f"Validation progress: {processed}/{len(links)} links processed ({validated} valid)"
                )

            # Exclude by keywords (e.g., normativas)
            if self.url_filter.should_exclude_by_keywords(link_url, link_text, avoid_keywords):
                logger.debug(f"Skipping excluded file: {link_url} (matches avoid_keywords)")
                continue

            # Filter by extension
            if filter_extensions:
                parsed = urlparse(link_url)
                if Path(parsed.path).suffix.lower() not in [e.lower() for e in filter_extensions]:
                    continue

            source_page = self._find_source_page(link_url, start_urls)
            link_data = DiscoveredLink(url=link_url, text=link_text, source_page=source_page)

            if validate and self.file_validator:
                try:
                    is_valid, mime, size_kb = self.file_validator.validate_file(
                        link_url, key, max_age_days=max_age_days
                    )
                    if is_valid:
                        validated += 1
                        link_data.status = "ok"
                        link_data.mime = mime
                        link_data.size_kb = size_kb
                        link_data.size_bytes = int(size_kb * 1024) if size_kb else None
                        validated_links.append(link_data)
                    else:
                        logger.debug(f"✗ Link rejected: {link_url}")
                except Exception as e:
                    logger.warning(f"Link validation error for {link_url}: {e}")
            else:
                validated += 1
                validated_links.append(link_data)

        logger.info(f"Validation completed: {validated}/{processed} valid links found")
        return validated_links

    # ========== Main execution ==========

    def _process_source(
        self,
        contract: dict,
        filter_extensions: list[str] | None,
        validate: bool,
    ) -> SourceLinksResult:
        """Process a single source contract."""
        key = contract.get("key")
        if not key:
            return SourceLinksResult(
                key="unknown",
                start_urls=[],
                links_found=[],
                filter_extensions=filter_extensions,
                error="Missing key in contract",
            )

        start_urls = contract.get("start_urls", [])

        discoverer = self.discoverer_factory.create(key, self.http_client)
        if not discoverer:
            logger.warning(f"Discoverer not found for key: {key}")
            return SourceLinksResult(
                key=key,
                start_urls=start_urls,
                links_found=[],
                filter_extensions=filter_extensions,
                error="Discoverer not found",
            )

        logger.info(f"Starting discovery for {key} from {len(start_urls)} start URLs")
        config = self._extract_crawl_config(contract)
        logger.info(
            f"Crawl config for {key}: max_depth={config.max_depth}, "
            f"same_domain_only={config.same_domain_only}, "
            f"avoid_domains={len(config.avoid_domains)} domains, "
            f"avoid_keywords={len(config.avoid_keywords)} keywords, "
            f"match_patterns={len(config.match_patterns)} patterns"
        )

        source_result = SourceLinksResult(
            key=key,
            start_urls=start_urls,
            links_found=[],
            filter_extensions=filter_extensions,
        )

        try:
            # Collect all links
            all_links: list[tuple[str, str]] = []
            visited: set[str] = set()

            for idx, start_url in enumerate(start_urls, 1):
                logger.info(f"Processing start URL {idx}/{len(start_urls)}: {start_url}")
                links = self._collect_links_from_url(start_url, config, filter_extensions, visited)
                all_links.extend(links)

            # Remove duplicates
            all_links = self._remove_duplicates(all_links)
            logger.info(f"Discovery completed for {key}: {len(all_links)} unique links found")

            # Validate and process links
            validated_links = self._validate_and_process_links(
                all_links, contract, key, start_urls, filter_extensions, validate
            )
            source_result.links_found = validated_links

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
            logger.error(f"Failed to process {key}: {e}", exc_info=True)
            source_result.error = str(e)

        return source_result

    def execute(
        self,
        filter_extensions: list[str] | None = None,
        validate: bool = True,
    ) -> DiscoverAllLinksResult:
        """Execute the discover all links use case."""
        contracts = self.contract_service.load_contracts()
        sources_data = {}

        for contract in contracts:
            key = contract.get("key")
            if not key:
                continue

            source_result = self._process_source(contract, filter_extensions, validate)
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
