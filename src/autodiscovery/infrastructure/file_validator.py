"""File validator implementation."""

import logging
from typing import List, Optional

from autodiscovery.domain.interfaces import IFileValidator, IHTTPClient

logger = logging.getLogger(__name__)


class FileValidator(IFileValidator):
    """Implementation of file validator using HTTP HEAD requests."""

    def __init__(self, client: IHTTPClient):
        self.client = client

    def validate_file(
        self,
        url: str,
        key: str,
        expected_mime: Optional[str] = None,
        expected_mime_any: Optional[List[str]] = None,
        min_size_kb: Optional[float] = None,
    ) -> tuple[bool, Optional[str], Optional[float]]:
        """
        Validate file accessibility and metadata.

        Returns (is_valid, mime, size_kb).
        """
        try:
            response = self.client.head(url)
            response.raise_for_status()

            mime = response.headers.get("content-type", "").split(";")[0].strip()
            size_bytes = int(response.headers.get("content-length", 0))
            size_kb = size_bytes / 1024.0 if size_bytes > 0 else 0

            # Verify it's a real file, not an HTML page
            html_mimes = ["text/html", "text/plain", "application/xhtml+xml"]
            if mime.lower() in [m.lower() for m in html_mimes]:
                logger.debug(f"Link is HTML page, not a file: {url} (MIME: {mime})")
                return False, None, None

            # MIME types válidos de archivos
            valid_file_mimes = [
                "application/pdf",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel.sheet.macroEnabled.12",
                "text/csv",
                "application/vnd.ms-excel.sheet.binary.macroEnabled.12",
                "application/zip",
                "application/x-zip-compressed",
                "application/octet-stream",
            ]

            # Verificar si es un archivo válido
            # Aceptar más tipos de application/* (no solo los listados)
            is_valid_file = (
                mime.lower() in [m.lower() for m in valid_file_mimes] or
                (mime.startswith("application/") and not mime.startswith("application/xhtml")) or
                mime.startswith("text/csv") or
                mime.startswith("application/vnd.") or
                mime.startswith("application/octet-stream")
            )

            # Verificar Content-Disposition si está presente
            content_disposition = response.headers.get("content-disposition", "")
            has_attachment = "attachment" in content_disposition.lower() or "filename" in content_disposition.lower()

            # Determinar si es un archivo válido
            if not is_valid_file and not has_attachment:
                logger.debug(f"Link is not a valid file type: {url} (MIME: {mime})")
                return False, None, None

            # Verificar tamaño mínimo
            min_size = min_size_kb or 1.0  # Default: 1 KB
            if size_kb < min_size and not has_attachment:
                logger.debug(f"Link is too small to be a real file: {url} ({size_kb:.2f} KB)")
                return False, None, None

            return True, mime, size_kb

        except Exception as e:
            logger.debug(f"File validation failed: {url} - {e}")
            return False, None, None

