"""File validator implementation."""

import logging
from datetime import UTC, datetime

from autodiscovery.domain.interfaces.http_port import IHTTPPort

logger = logging.getLogger(__name__)


class FileValidator:
    """Implementation of file validator using HTTP HEAD requests."""

    def __init__(self, client: IHTTPPort):
        self.client = client

    def validate_file(
        self,
        url: str,
        key: str,
        expected_mime: str | None = None,
        expected_mime_any: list[str] | None = None,
        min_size_kb: float | None = None,
        max_age_days: int | None = None,
    ) -> tuple[bool, str | None, float | None]:
        """
        Validate file accessibility and metadata.

        Args:
            url: URL to validate
            key: Source key
            expected_mime: Expected MIME type
            expected_mime_any: List of acceptable MIME types
            min_size_kb: Minimum size in KB
            max_age_days: Maximum age in days (filters out old files)

        Returns (is_valid, mime, size_kb).
        """
        try:
            response = self.client.head(url, headers=None)
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
                mime.lower() in [m.lower() for m in valid_file_mimes]
                or (mime.startswith("application/") and not mime.startswith("application/xhtml"))
                or mime.startswith(("text/csv", "application/vnd.", "application/octet-stream"))
            )

            # Verificar Content-Disposition si está presente
            content_disposition = response.headers.get("content-disposition", "")
            has_attachment = (
                "attachment" in content_disposition.lower()
                or "filename" in content_disposition.lower()
            )

            # Determinar si es un archivo válido
            if not is_valid_file and not has_attachment:
                logger.debug(f"Link is not a valid file type: {url} (MIME: {mime})")
                return False, None, None

            # Verificar tamaño mínimo
            min_size = min_size_kb or 1.0  # Default: 1 KB
            if size_kb < min_size and not has_attachment:
                logger.debug(f"Link is too small to be a real file: {url} ({size_kb:.2f} KB)")
                return False, None, None

            # Verificar antigüedad máxima (usando Last-Modified header)
            if max_age_days is not None:
                last_modified_str = response.headers.get("last-modified")
                if last_modified_str:
                    try:
                        # Parse Last-Modified header (RFC 2822 format)
                        # Example: "Mon, 01 Jan 2024 12:00:00 GMT"
                        from email.utils import parsedate_to_datetime

                        last_modified = parsedate_to_datetime(last_modified_str)
                        # Ensure timezone-aware
                        if last_modified.tzinfo is None:
                            last_modified = last_modified.replace(tzinfo=UTC)

                        now = datetime.now(UTC)
                        age_days = (now - last_modified).days

                        if age_days > max_age_days:
                            logger.debug(
                                f"File too old: {url} (age: {age_days} days, max: {max_age_days} days)"
                            )
                            return False, None, None
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not parse Last-Modified header for {url}: {e}")
                        # If we can't parse the date, we can't filter by age, so we accept it
                        # (could be more strict and reject, but this is safer)

            return True, mime, size_kb

        except Exception as e:
            logger.debug(f"File validation failed: {url} - {e}")
            return False, None, None
