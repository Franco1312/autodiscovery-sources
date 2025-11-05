"""Generic crawler for discovering candidate files."""

from collections import deque
from typing import Dict, List, Set
from urllib.parse import unquote, urlparse

from ..domain.entities import DiscoveredFile
from ..domain.value_objects import Url
from ..infrastructure.urltools import urljoin_safe
from ..interfaces.html_port import HtmlPort
from ..interfaces.http_port import HttpPort
from ..interfaces.logger_port import LoggerPort


class Crawler:
    """Generic crawler for discovering files."""

    def __init__(
        self,
        http_port: HttpPort,
        html_port: HtmlPort,
        logger: LoggerPort,
    ):
        """Initialize crawler."""
        self.http = http_port
        self.html = html_port
        self.logger = logger

    def crawl(
        self,
        start_urls: List[str],
        scope: Dict,
        find: Dict,
        max_depth: int = 2,
        max_candidates: int = 10,
    ) -> List[DiscoveredFile]:
        """Crawl starting from URLs and return discovered candidates.
        
        Args:
            start_urls: List of starting URLs
            scope: Scope configuration (allow_domains, allow_paths_any, etc.)
            find: Find configuration (link_text_any, url_tokens_any)
            max_depth: Maximum crawl depth
            max_candidates: Maximum candidates to return
        
        Returns:
            List of DiscoveredFile candidates
        """
        candidates: List[DiscoveredFile] = []
        visited: Set[str] = set()
        queue = deque()
        
        # Initialize queue with start URLs at depth 0
        for url in start_urls:
            queue.append((url, 0))
        
        allow_domains = scope.get("allow_domains", [])
        allow_paths_any = scope.get("allow_paths_any", [])
        link_text_any = find.get("link_text_any", [])
        url_tokens_any = find.get("url_tokens_any", [])
        
        self.logger.debug(
            "Starting crawl",
            start_urls=start_urls,
            max_depth=max_depth,
            max_candidates=max_candidates,
        )
        
        while queue and len(candidates) < max_candidates:
            current_url, depth = queue.popleft()
            
            # Skip if already visited
            if current_url in visited:
                continue
            
            # Skip if depth exceeded
            if depth > max_depth:
                continue
            
            # Check domain and path scope
            parsed = urlparse(current_url)
            if allow_domains:
                # Check if domain matches (including subdomains)
                domain_matches = False
                for allowed_domain in allow_domains:
                    if parsed.netloc == allowed_domain or parsed.netloc.endswith(f".{allowed_domain}"):
                        domain_matches = True
                        break
                if not domain_matches:
                    self.logger.debug("Domain not allowed", url=current_url, domain=parsed.netloc, allowed=allow_domains)
                    continue
            
            if allow_paths_any:
                path_matches = any(
                    parsed.path.startswith(path) for path in allow_paths_any
                )
                if not path_matches:
                    self.logger.debug("Path not allowed", url=current_url, path=parsed.path)
                    continue
            
            visited.add(current_url)
            
            # Fetch HTML
            content, headers, error = self.http.get(current_url)
            if error or not content:
                self.logger.debug("Failed to fetch", url=current_url, error=error)
                continue
            
            # Check if it's HTML (basic check)
            content_type = headers.get("content-type", "").lower() if headers else ""
            if "text/html" not in content_type:
                # Not HTML, might be a direct file link
                filename = self._extract_filename(current_url, headers)
                candidate = DiscoveredFile(
                    key="",  # Will be set by caller
                    url=Url(value=current_url),
                    filename=filename,
                    score=0,
                )
                candidates.append(candidate)
                continue
            
            # Extract links
            try:
                html_text = content.decode("utf-8", errors="ignore")
                links = self.html.extract_links(html_text, current_url)
            except Exception as e:
                self.logger.debug("Failed to extract links", url=current_url, error=str(e))
                continue
            
            # Prefilter links
            for href, text in links:
                if href in visited:
                    continue
                
                # Prefilter: check if link text or URL tokens match
                if not self._prefilter_match(href, text, link_text_any, url_tokens_any):
                    self.logger.debug(
                        "Prefilter miss",
                        url=href,
                        text=text,
                        link_text_any=link_text_any,
                        url_tokens_any=url_tokens_any,
                    )
                    continue
                
                # Normalize URL
                normalized = urljoin_safe(current_url, href)
                
                # Check if it's a file (common extensions)
                parsed_link = urlparse(normalized)
                path_lower = parsed_link.path.lower()
                if any(
                    path_lower.endswith(ext)
                    for ext in [".xls", ".xlsx", ".xlsm", ".pdf", ".zip"]
                ):
                    # Potential file candidate
                    filename = self._extract_filename(normalized, None)
                    candidate = DiscoveredFile(
                        key="",  # Will be set by caller
                        url=Url(value=normalized),
                        filename=filename,
                        score=0,
                    )
                    candidates.append(candidate)
                elif depth < max_depth:
                    # Queue for further crawling
                    queue.append((normalized, depth + 1))
        
        self.logger.info(
            "Crawl completed",
            candidates_found=len(candidates),
            visited=len(visited),
        )
        
        return candidates[:max_candidates]

    def _prefilter_match(
        self, url: str, text: str, link_text_any: List[str], url_tokens_any: List[str]
    ) -> bool:
        """Check if link matches prefilter criteria."""
        # Check link text
        if link_text_any:
            text_lower = text.lower()
            if any(token.lower() in text_lower for token in link_text_any):
                return True
        
        # Check URL tokens
        if url_tokens_any:
            url_lower = url.lower()
            if any(token.lower() in url_lower for token in url_tokens_any):
                return True
        
        # If no filters specified, accept all
        if not link_text_any and not url_tokens_any:
            return True
        
        return False

    def _extract_filename(self, url: str, headers: Dict = None) -> str:
        """Extract filename from URL or headers."""
        # Try Content-Disposition header
        if headers:
            content_disposition = headers.get("content-disposition", "")
            if content_disposition:
                # Extract filename from Content-Disposition
                import re
                match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
                if match:
                    filename = match.group(1).strip('"\'')
                    return filename
        
        # Extract from URL path
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = path.split("/")[-1]
        
        if not filename or "." not in filename:
            # Fallback: use URL path
            filename = path.split("/")[-1] or "file"
        
        return filename

