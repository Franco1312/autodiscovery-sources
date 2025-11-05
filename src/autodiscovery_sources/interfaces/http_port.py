"""Port for HTTP operations."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple


class HttpPort(ABC):
    """Port for HTTP HEAD and GET operations."""

    @abstractmethod
    def head(self, url: str, timeout: float = 5.0) -> Tuple[Optional[Dict], Optional[str]]:
        """Perform HEAD request.
        
        Returns:
            Tuple of (headers dict, error message if any)
        """
        pass

    @abstractmethod
    def get(self, url: str, timeout: float = 10.0) -> Tuple[Optional[bytes], Optional[Dict], Optional[str]]:
        """Perform GET request.
        
        Returns:
            Tuple of (content bytes, headers dict, error message if any)
        """
        pass

