"""Service for URL filtering and validation."""

from urllib.parse import urlparse

from autodiscovery.domain.interfaces.http_port import IHTTPPort


class URLFilterService:
    """Service for filtering and validating URLs."""

    def __init__(self, http_client: IHTTPPort):
        """Initialize URL filter service."""
        self.http_client = http_client

    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def should_avoid_url(self, url: str, avoid_domains: list[str] | None = None) -> bool:
        """Check if URL should be avoided based on avoid_domains configuration."""
        if not avoid_domains:
            return False

        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(avoid_domain.lower() in domain for avoid_domain in avoid_domains)

    def should_exclude_by_keywords(
        self, url: str, text: str | None = None, avoid_keywords: list[str] | None = None
    ) -> bool:
        """Check if file should be excluded based on avoid_keywords configuration."""
        if not avoid_keywords:
            return False

        url_lower = url.lower()
        text_lower = (text or "").lower()

        # Check if any keyword appears in URL or link text
        for keyword in avoid_keywords:
            if keyword.lower() in url_lower or (text and keyword.lower() in text_lower):
                return True

        return False

    def is_html_url_by_structure(self, url: str) -> bool:
        """Check if URL is likely HTML based on URL structure only (no HTTP request)."""
        parsed = urlparse(url)
        path = parsed.path.lower()

        file_extensions = [
            ".pdf",
            ".xls",
            ".xlsx",
            ".xlsm",
            ".csv",
            ".zip",
            ".doc",
            ".docx",
            ".ppt",
            ".pptx",
            ".txt",
            ".json",
            ".xml",
            ".rss",
            ".atom",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".ico",
            ".css",
            ".js",
        ]

        if any(path.endswith(ext) for ext in file_extensions):
            return False

        html_extensions = [".html", ".htm", ".asp", ".aspx", ".php", ".jsp", ".cgi"]
        if any(path.endswith(ext) for ext in html_extensions):
            return True

        if not path or path.endswith("/"):
            return True

        from pathlib import Path

        return not bool(Path(path).suffix)

    def is_html_url(self, url: str, avoid_domains: list[str] | None = None) -> bool:
        """Check if URL is HTML page (with HTTP verification if needed)."""
        if avoid_domains and self.should_avoid_url(url, avoid_domains):
            return False

        if not self.is_html_url_by_structure(url):
            return False

        try:
            response = self.http_client.head(url, headers=None)
            mime = response.headers.get("content-type", "").split(";")[0].strip().lower()
            html_mimes = ["text/html", "application/xhtml+xml"]
            return any(m in mime for m in html_mimes)
        except Exception:
            return self.is_html_url_by_structure(url)
