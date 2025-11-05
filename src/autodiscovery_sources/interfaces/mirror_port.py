"""Port for mirror operations."""

from abc import ABC, abstractmethod
from typing import Optional


class MirrorPort(ABC):
    """Port for mirroring files to storage."""

    @abstractmethod
    def write(self, key: str, version: str, filename: str, content: bytes) -> Optional[str]:
        """Write file to mirror storage.
        
        Returns:
            Storage path/key (e.g., S3 key) or None if filesystem
        """
        pass

