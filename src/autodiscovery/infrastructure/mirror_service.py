"""Mirror service implementation."""

import logging
from pathlib import Path

from autodiscovery.domain.interfaces import IMirrorService
from autodiscovery.http import HTTPClient
from autodiscovery.mirror.fs import FileSystemMirror
from autodiscovery.mirror.s3 import S3Mirror

logger = logging.getLogger(__name__)


class MirrorService(IMirrorService):
    """Implementation of mirror service using filesystem and optional S3."""

    def __init__(self, client: HTTPClient):
        self.client = client
        self.fs_mirror = FileSystemMirror()
        self.s3_mirror = S3Mirror()

    def mirror_file(
        self,
        url: str,
        key: str,
        version: str,
        filename: str,
    ) -> tuple[Path, str]:
        """
        Mirror file from URL.

        Returns (stored_path, sha256).
        """
        stored_path, sha256 = self.fs_mirror.mirror_file(url, key, version, filename, self.client)

        # Try S3 mirror if enabled
        if self.s3_mirror.enabled:
            s3_key = self.s3_mirror.mirror_file(stored_path, key, version, filename)
            logger.debug(f"S3 mirror result: {s3_key}")

        return stored_path, sha256
