"""Use case: discover a single source."""

from typing import Dict, Optional

from ..domain.entities import DiscoveredFile, RegistryEntry
from ..domain.errors import ContractError, DiscoveryError
from ..domain.value_objects import BytesSizeKB, MimeType, Sha256, Url
from ..engine.crawler import Crawler
from ..engine.ranker import Ranker
from ..engine.selector import Selector
from ..engine.validator import Validator
from ..engine.versioning import Versioning
from ..infrastructure.hashing import sha256_bytes
from ..interfaces.clock_port import ClockPort
from ..interfaces.contracts_port import ContractsPort
from ..interfaces.html_port import HtmlPort
from ..interfaces.http_port import HttpPort
from ..interfaces.logger_port import LoggerPort
from ..interfaces.metrics_port import MetricsPort
from ..interfaces.mirror_port import MirrorPort
from ..interfaces.registry_port import RegistryPort


class DiscoverSourceUseCase:
    """Use case for discovering a single source."""

    def __init__(
        self,
        contracts_port: ContractsPort,
        http_port: HttpPort,
        html_port: HtmlPort,
        registry_port: RegistryPort,
        mirror_port: MirrorPort,
        clock_port: ClockPort,
        metrics_port: MetricsPort,
        logger: LoggerPort,
    ):
        """Initialize use case."""
        self.contracts = contracts_port
        self.http = http_port
        self.html = html_port
        self.registry = registry_port
        self.mirror = mirror_port
        self.clock = clock_port
        self.metrics = metrics_port
        self.logger = logger

    def execute(self, key: str, fast: bool = False) -> Optional[RegistryEntry]:
        """Discover source for a given key.
        
        Args:
            key: Source key
            fast: Fast mode (override max_depth=1, max_candidates=1)
        
        Returns:
            RegistryEntry if successful, None otherwise
        """
        self.logger.info("Starting discovery", key=key, fast=fast)
        self.metrics.increment("discovery.started")
        
        # Load contract
        contract = self.contracts.load_by_key(key)
        if not contract:
            self.logger.error("Contract not found", key=key)
            self.metrics.increment("discovery.contract_not_found")
            raise ContractError(f"Contract not found for key: {key}")
        
        # Override scope if fast mode
        if fast:
            contract["scope"] = contract.get("scope", {})
            contract["scope"]["max_depth"] = 1
            contract["scope"]["max_candidates"] = 1
        
        source_type = contract.get("source_type", "html")
        
        if source_type == "api":
            # API-first: no crawl, just GET and register
            return self._discover_api(key, contract)
        else:
            # HTML: crawl -> rank -> validate -> select -> version -> mirror -> registry
            return self._discover_html(key, contract)

    def _discover_api(self, key: str, contract: Dict) -> Optional[RegistryEntry]:
        """Discover API source."""
        endpoint = contract.get("endpoint")
        if not endpoint:
            raise ContractError(f"API endpoint not specified for key: {key}")
        
        headers = contract.get("headers", {})
        
        self.logger.info("Fetching API endpoint", key=key, endpoint=endpoint)
        
        # GET endpoint
        content, response_headers, error = self.http.get(endpoint)
        if error or not content:
            self.logger.error("API fetch failed", key=key, error=error)
            self.metrics.increment("discovery.api_fetch_failed")
            return None
        
        # Calculate hash
        sha256 = Sha256(value=sha256_bytes(content))
        
        # Extract version
        versioning_strategy = contract.get("versioning", "none")
        version = Versioning.extract_version(
            versioning_strategy, "", {"patterns": []}, response_headers or {}
        )
        
        # Extract filename from URL or use default
        from urllib.parse import urlparse
        parsed = urlparse(endpoint)
        url_filename = parsed.path.split("/")[-1] if parsed.path else None
        filename = url_filename if url_filename and "." in url_filename else f"{key}.json"
        
        # Extract MIME type from headers
        mime_type = None
        if response_headers:
            content_type = response_headers.get("content-type", "")
            if content_type:
                mime_str = content_type.split(";")[0].strip()
                if mime_str:
                    mime_type = MimeType(value=mime_str)
        
        # Calculate size
        size_kb = None
        if content:
            size_kb = BytesSizeKB(value=len(content) / 1024.0)
        
        # Create registry entry
        entry = RegistryEntry(
            key=key,
            url=Url(value=endpoint),
            version=version,
            filename=filename,
            mime=mime_type,
            size_kb=size_kb,
            sha256=sha256,
            last_checked=self.clock.now(),
            status="ok",
            notes="api_source",
            s3_key=None,
        )
        
        # Mirror if requested
        mirror = contract.get("mirror", False)
        if mirror:
            s3_key = self.mirror.write(key, version, entry.filename, content)
            entry.s3_key = s3_key
        
        # Upsert registry
        self.registry.upsert(entry)
        
        self.logger.info("API discovery completed", key=key, version=version)
        self.metrics.increment("discovery.completed")
        
        return entry

    def _discover_html(self, key: str, contract: Dict) -> Optional[RegistryEntry]:
        start_urls = contract.get("start_urls", [])
        if not start_urls:
            raise ContractError(f"start_urls not specified for key: {key}")
        
        scope = contract.get("scope", {})
        find = contract.get("find", {})
        match_config = contract.get("match", {})
        select_config = contract.get("select", {})
        expect_config = contract.get("expect", {})
        versioning_strategy = contract.get("versioning", "best_effort_date_or_last_modified")
        mirror = contract.get("mirror", True)
        
        max_depth = scope.get("max_depth", 2)
        max_candidates = scope.get("max_candidates", 10)
        
        # Initialize engine components
        crawler = Crawler(self.http, self.html, self.logger)
        ranker = Ranker()
        validator = Validator(self.http, self.logger)
        selector = Selector(self.logger)
        
        # Crawl
        self.logger.info("Crawling", key=key, start_urls=start_urls)
        candidates = crawler.crawl(start_urls, scope, find, max_depth, max_candidates)
        
        # If no candidates found from crawling, check for known_urls in contract
        if not candidates:
            known_urls = contract.get("known_urls", [])
            if known_urls:
                self.logger.info("No candidates from crawl, checking known_urls", key=key, count=len(known_urls))
                # Create candidates from known URLs
                from ..domain.entities import DiscoveredFile
                from ..domain.value_objects import Url
                from urllib.parse import urlparse
                
                for url_str in known_urls:
                    # Extract filename from URL
                    parsed = urlparse(url_str)
                    filename = parsed.path.split("/")[-1] if parsed.path else f"{key}.xlsx"
                    
                    candidate = DiscoveredFile(
                        key=key,
                        url=Url(value=url_str),
                        filename=filename,
                        score=100,  # High priority for known URLs
                    )
                    candidates.append(candidate)
        
        if not candidates:
            self.logger.warning("No candidates found", key=key)
            self.metrics.increment("discovery.no_candidates")
            return None
        
        # Set key for candidates
        for candidate in candidates:
            candidate.key = key
        
        # Rank
        self.logger.info("Ranking candidates", key=key, count=len(candidates))
        ranked = ranker.rank(candidates, match_config)
        
        # Validate
        self.logger.info("Validating candidates", key=key, count=len(ranked))
        valid = validator.validate(ranked, expect_config)
        
        if not valid:
            self.logger.warning("No valid candidates", key=key)
            self.metrics.increment("discovery.no_valid_candidates")
            return None
        
        # Select
        self.logger.info("Selecting best candidate", key=key, count=len(valid))
        selected = selector.select(valid, select_config, match_config)
        
        if not selected:
            self.logger.warning("No candidate selected", key=key)
            self.metrics.increment("discovery.no_selection")
            return None
        
        # Get full content for mirroring
        content, headers, error = self.http.get(selected.url.value)
        if error or not content:
            self.logger.error("Failed to fetch selected file", key=key, url=selected.url.value, error=error)
            self.metrics.increment("discovery.fetch_failed")
            return None
        
        # Calculate hash
        sha256 = Sha256(value=sha256_bytes(content))
        
        # Extract version
        headers_dict = headers or {}
        version = Versioning.extract_version(
            versioning_strategy, selected.filename, match_config, headers_dict
        )
        
        # Mirror if requested
        s3_key = None
        if mirror:
            s3_key = self.mirror.write(key, version, selected.filename, content)
        
        # Create registry entry
        entry = RegistryEntry(
            key=key,
            url=selected.url,
            version=version,
            filename=selected.filename,
            mime=selected.mime,
            size_kb=selected.size_kb,
            sha256=sha256,
            last_checked=self.clock.now(),
            status="ok",
            notes=selected.notes,
            s3_key=s3_key,
        )
        
        # Upsert registry
        self.registry.upsert(entry)
        
        self.logger.info(
            "Discovery completed",
            key=key,
            version=version,
            url=selected.url.value,
        )
        self.metrics.increment("discovery.completed")
        
        return entry

