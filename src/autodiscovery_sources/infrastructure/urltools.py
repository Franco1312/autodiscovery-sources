"""URL utilities."""

from urllib.parse import quote, urljoin, urlparse
from urllib.request import url2pathname


def urljoin_safe(base: str, relative: str) -> str:
    """Safely join URLs, handling percent-encoding."""
    # Normalize base URL
    parsed_base = urlparse(base)
    # Join URLs
    joined = urljoin(base, relative)
    # Parse and reconstruct to handle encoding
    parsed = urlparse(joined)
    # Reconstruct URL with proper encoding
    scheme = parsed.scheme
    netloc = parsed.netloc
    path = quote(parsed.path, safe="/")
    params = quote(parsed.params, safe="") if parsed.params else ""
    query = parsed.query  # Keep as-is
    fragment = quote(parsed.fragment, safe="") if parsed.fragment else ""
    
    # Reconstruct
    result = f"{scheme}://{netloc}{path}"
    if params:
        result += f";{params}"
    if query:
        result += f"?{query}"
    if fragment:
        result += f"#{fragment}"
    
    return result


def percent_encode_safe(text: str) -> str:
    """Percent-encode text, preserving safe characters."""
    return quote(text, safe="/?=&")

