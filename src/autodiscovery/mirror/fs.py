"""Filesystem mirror implementation."""

import logging
from pathlib import Path
from typing import Optional

from autodiscovery.config import Config
from autodiscovery.hashutil import sha256_stream
from autodiscovery.http import HTTPClient
from autodiscovery.util.fsx import atomic_write_stream, safe_mkdirs

logger = logging.getLogger(__name__)


class FileSystemMirror:
    """Filesystem mirror manager."""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Config.MIRRORS_PATH

    def mirror_file(
        self,
        url: str,
        key: str,
        version: str,
        filename: str,
        client: HTTPClient,
    ) -> tuple[Path, str]:
        """
        Mirror file from URL to filesystem.

        Returns (stored_path, sha256).
        """
        # Build path: mirrors/<key>/<version>/<filename>
        mirror_dir = self.base_path / key / version
        safe_mkdirs(mirror_dir)
        stored_path = mirror_dir / filename

        logger.info(f"Mirroring {url} to {stored_path}")

        # Stream download and write atomically
        response = client.get(url)
        response.raise_for_status()

        # Calculate SHA256 while streaming
        import io
        stream = io.BytesIO(response.content)
        sha256 = sha256_stream(stream)

        # Reset stream for writing
        stream.seek(0)
        atomic_write_stream(stored_path, stream)

        logger.info(f"Mirrored to {stored_path} (SHA256: {sha256})")
        return stored_path, sha256

