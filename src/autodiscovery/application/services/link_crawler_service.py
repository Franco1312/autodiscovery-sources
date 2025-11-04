"""Service for crawling links recursively."""

import logging

from autodiscovery.application.services.pattern_matcher_service import PatternMatcherService
from autodiscovery.application.services.url_filter_service import URLFilterService
from autodiscovery.domain.interfaces.html_port import IHTMLPort

logger = logging.getLogger(__name__)


class LinkCrawlerService:
    """Service for crawling links recursively."""

    def __init__(
        self,
        url_filter: URLFilterService,
        pattern_matcher: PatternMatcherService,
        html_parser: IHTMLPort,
    ):
        """Initialize link crawler service."""
        self.url_filter = url_filter
        self.pattern_matcher = pattern_matcher
        self.html_parser = html_parser

    def crawl_recursive(
        self,
        url: str,
        max_depth: int,
        current_depth: int,
        visited: set[str],
        same_domain_only: bool,
        base_domain: str | None,
        filter_extensions: list[str] | None,
        avoid_domains: list[str] | None,
        avoid_keywords: list[str] | None,
        match_patterns: list[str] | None,
        match_keywords: list[str] | None,
    ) -> list[tuple[str, str]]:
        """Crawl URLs recursively up to max_depth."""
        if current_depth > max_depth or url in visited:
            return []

        visited.add(url)
        all_links: list[tuple[str, str]] = []

        try:
            if self.url_filter.should_avoid_url(url, avoid_domains):
                return []

            if same_domain_only and base_domain and self.url_filter.get_domain(url) != base_domain:
                return []

            if not self.url_filter.is_html_url_by_structure(url) or not self.url_filter.is_html_url(
                url, avoid_domains
            ):
                return []

            logger.info(f"Crawling URL (depth={current_depth}/{max_depth}): {url}")
            soup = self.html_parser.fetch_html(url)
            links = self.html_parser.extract_links(soup, url)
            logger.info(f"Found {len(links)} links from {url} (depth={current_depth})")

            for link_url, link_text in links:
                if self.url_filter.should_avoid_url(link_url, avoid_domains):
                    continue

                # Exclude files by keywords (e.g., normativas)
                if self.url_filter.should_exclude_by_keywords(link_url, link_text, avoid_keywords):
                    logger.debug(f"Skipping excluded file: {link_url} (matches avoid_keywords)")
                    continue

                if filter_extensions:
                    if any(link_url.lower().endswith(ext) for ext in filter_extensions):
                        all_links.append((link_url, link_text))
                else:
                    all_links.append((link_url, link_text))

                # Recursive crawl for HTML links
                if (
                    current_depth < max_depth
                    and link_url not in visited
                    and self.url_filter.is_html_url_by_structure(link_url)
                    and self.pattern_matcher.should_crawl_link(
                        link_url, match_keywords, match_patterns
                    )
                ):
                    recursive_links = self.crawl_recursive(
                        link_url,
                        max_depth,
                        current_depth + 1,
                        visited,
                        same_domain_only,
                        base_domain,
                        filter_extensions,
                        avoid_domains,
                        avoid_keywords,
                        match_patterns,
                        match_keywords,
                    )
                    all_links.extend(recursive_links)

        except Exception as e:
            logger.warning(f"Failed to crawl {url} at depth {current_depth}: {e}", exc_info=True)

        return all_links

    def extract_links_simple(
        self, url: str, filter_extensions: list[str] | None
    ) -> list[tuple[str, str]]:
        """Extract links from URL without recursive crawling."""
        soup = self.html_parser.fetch_html(url)
        links = self.html_parser.extract_links(soup, url)

        if filter_extensions:
            links = [
                link
                for link in links
                if any(link[0].lower().endswith(ext) for ext in filter_extensions)
            ]

        return links
