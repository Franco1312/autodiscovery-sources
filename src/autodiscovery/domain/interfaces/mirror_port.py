"""Mirror port interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class IMirrorPort(ABC):
    """Port for mirroring files (FS and/or S3)."""

    @abstractmethod
    def mirror_file(
        self,
        url: str,
        key: str,
        version: str,
        filename: str,
    ) -> tuple[Path, str]:
        """
        Mirror file from URL to local FS and optionally S3.

        Args:
            url: URL to download
            key: Source key
            version: Version string
            filename: Filename

        Returns:
            Tuple of (local_path, sha256_hash)
        """

    @abstractmethod
    def get_mirror_path(
        self,
        key: str,
        version: str,
        filename: str,
    ) -> Path:
        """
        Get expected mirror path for a file.

        Args:
            key: Source key
            version: Version string
            filename: Filename

        Returns:
            Expected mirror path
        """
