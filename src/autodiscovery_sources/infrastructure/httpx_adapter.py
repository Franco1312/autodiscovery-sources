"""httpx adapter for HTTP operations."""

import os
from typing import Dict, Optional, Tuple

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..domain.errors import NetworkError
from ..interfaces.http_port import HttpPort


class HttpxAdapter(HttpPort):
    """httpx adapter for HTTP operations."""

    def __init__(
        self,
        timeout_head: float = None,
        timeout_get: float = None,
        max_retries: int = None,
        user_agent: str = None,
    ):
        """Initialize adapter with configuration."""
        self.timeout_head = float(
            timeout_head or os.getenv("HTTP_HEAD_TIMEOUT", "5.0")
        )
        self.timeout_get = float(
            timeout_get or os.getenv("HTTP_GET_TIMEOUT", "10.0")
        )
        self.max_retries = int(
            max_retries or os.getenv("HTTP_MAX_RETRIES", "2")
        )
        self.user_agent = user_agent or "RadarAutodiscovery/1.0"
        self.default_headers = {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        }

    def _normalize_headers(self, headers: httpx.Headers) -> Dict[str, str]:
        """Normalize headers to lowercase keys."""
        return {k.lower(): v for k, v in headers.items()}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def head(self, url: str, timeout: float = None) -> Tuple[Optional[Dict], Optional[str]]:
        """Perform HEAD request with retries."""
        timeout = timeout or self.timeout_head
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
                response = client.head(url, headers=self.default_headers)
                response.raise_for_status()
                headers = self._normalize_headers(response.headers)
                return headers, None
        except httpx.HTTPStatusError as e:
            return None, f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
        except httpx.TimeoutException:
            return None, f"Timeout after {timeout}s"
        except httpx.RequestError as e:
            return None, f"Request error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def get(self, url: str, timeout: float = None) -> Tuple[Optional[bytes], Optional[Dict], Optional[str]]:
        """Perform GET request with retries."""
        timeout = timeout or self.timeout_get
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
                response = client.get(url, headers=self.default_headers)
                response.raise_for_status()
                headers = self._normalize_headers(response.headers)
                return response.content, headers, None
        except httpx.HTTPStatusError as e:
            return None, None, f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
        except httpx.TimeoutException:
            return None, None, f"Timeout after {timeout}s"
        except httpx.RequestError as e:
            return None, None, f"Request error: {str(e)}"
        except Exception as e:
            return None, None, f"Unexpected error: {str(e)}"

