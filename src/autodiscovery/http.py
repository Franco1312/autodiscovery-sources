"""HTTP client with retry and timeout logic."""

import logging
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from autodiscovery.config import Config
from autodiscovery.domain.interfaces import IHTTPClient

logger = logging.getLogger(__name__)


class HTTPClient(IHTTPClient):
    """HTTP client with retry logic and timeouts."""

    def __init__(
        self,
        timeout: int = None,
        retries: int = None,
        user_agent: str = None,
        verify: bool = None,
    ):
        self.timeout = timeout or Config.TIMEOUT_SECS
        self.retries = retries or Config.RETRIES
        self.user_agent = user_agent or Config.USER_AGENT
        self.verify = verify if verify is not None else Config.VERIFY_SSL

        self._client = httpx.Client(
            timeout=httpx.Timeout(self.timeout),
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
            verify=self.verify,
        )

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def head(self, url: str) -> httpx.Response:
        """Perform HEAD request with retry."""
        try:
            response = self._client.head(url)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.warning(f"HEAD request failed for {url}: {e}")
            raise

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def get(self, url: str) -> httpx.Response:
        """Perform GET request with retry."""
        try:
            response = self._client.get(url)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.warning(f"GET request failed for {url}: {e}")
            raise

    def stream(self, url: str):
        """Stream download from URL."""
        try:
            with self._client.stream("GET", url) as response:
                response.raise_for_status()
                yield from response.iter_bytes()
        except Exception as e:
            logger.warning(f"Stream request failed for {url}: {e}")
            raise

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

