"""Policies for versioning, selection, and acceptance."""

import re
from datetime import datetime
from typing import Any

from dateutil import parser as date_parser  # type: ignore[import-untyped]


class VersioningPolicy:
    """Policy for versioning discovered files."""

    @staticmethod
    def date_from_filename(
        filename: str,
        regex_groups: list[str] | None = None,
    ) -> str | None:
        """
        Extract date from filename using regex groups.

        Args:
            filename: Filename to extract date from
            regex_groups: List of captured groups from regex match

        Returns:
            Version string in format vYYYY-MM-DD or None
        """
        if not regex_groups:
            return None

        # Try to find date-like pattern in groups
        for group in regex_groups:
            # Try YYYY-MM-DD format
            date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", group)
            if date_match:
                return f"v{date_match.group(0)}"

            # Try YYYYMMDD format
            date_match = re.search(r"(\d{4})(\d{2})(\d{2})", group)
            if date_match:
                return f"v{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

        return None

    @staticmethod
    def year_month_from_spanish_month(
        filename: str,
        locale: str = "es",
    ) -> str | None:
        """
        Extract year-month from Spanish month name in filename.

        Args:
            filename: Filename containing month name
            locale: Locale hint (default: "es")

        Returns:
            Version string in format YYYY-MM or None
        """
        if locale != "es":
            return None

        # Spanish month names
        spanish_months = {
            "enero": "01",
            "febrero": "02",
            "marzo": "03",
            "abril": "04",
            "mayo": "05",
            "junio": "06",
            "julio": "07",
            "agosto": "08",
            "septiembre": "09",
            "octubre": "10",
            "noviembre": "11",
            "diciembre": "12",
            "sep": "09",
            "nov": "11",
            "dic": "12",
        }

        filename_lower = filename.lower()

        # Find year
        year_match = re.search(r"(\d{4})", filename)
        if not year_match:
            return None

        year = year_match.group(1)

        # Find month
        for month_name, month_num in spanish_months.items():
            if month_name in filename_lower:
                return f"{year}-{month_num}"

        # Try to find month number
        month_match = re.search(r"-(\d{2})-", filename)
        if month_match:
            return f"{year}-{month_match.group(1)}"

        return None

    @staticmethod
    def date_from_last_modified(headers: dict[str, Any]) -> str | None:
        """
        Extract date from Last-Modified header.

        Args:
            headers: HTTP response headers

        Returns:
            Version string in format vYYYY-MM-DD or None
        """
        last_modified = headers.get("Last-Modified")
        if not last_modified:
            return None

        try:
            dt = date_parser.parse(last_modified)
            return f"v{dt.strftime('%Y-%m-%d')}"
        except Exception:
            return None

    @staticmethod
    def date_from_filename_or_last_modified(
        filename: str,
        headers: dict[str, Any],
        regex_groups: list[str] | None = None,
    ) -> str | None:
        """
        Try to extract date from filename, fallback to Last-Modified.

        Args:
            filename: Filename to extract date from
            headers: HTTP response headers
            regex_groups: List of captured groups from regex match

        Returns:
            Version string in format vYYYY-MM-DD or None
        """
        # Try filename first
        version = VersioningPolicy.date_from_filename(filename, regex_groups)
        if version:
            return version

        # Fallback to Last-Modified
        return VersioningPolicy.date_from_last_modified(headers)

    @staticmethod
    def best_effort_date_or_last_modified(
        filename: str,
        headers: dict[str, Any],
        regex_groups: list[str] | None = None,
        locale: str = "es",
    ) -> str | None:
        """
        Best effort date extraction: filename (Spanish month) -> filename (date) -> Last-Modified.

        Args:
            filename: Filename to extract date from
            headers: HTTP response headers
            regex_groups: List of captured groups from regex match
            locale: Locale hint (default: "es")

        Returns:
            Version string in format vYYYY-MM-DD or YYYY-MM or None
        """
        # Try Spanish month pattern first
        if locale == "es":
            version = VersioningPolicy.year_month_from_spanish_month(filename, locale)
            if version:
                return version

        # Try date from filename
        version = VersioningPolicy.date_from_filename(filename, regex_groups)
        if version:
            return version

        # Fallback to Last-Modified
        return VersioningPolicy.date_from_last_modified(headers)

    @staticmethod
    def date_today() -> str:
        """
        Get today's date as version string.

        Returns:
            Version string in format vYYYY-MM-DD
        """
        return f"v{datetime.now().strftime('%Y-%m-%d')}"

    @staticmethod
    def none() -> str:
        """
        Return version 'none' for non-versioned sources.

        Returns:
            Version string "none"
        """
        return "none"


class SelectionPolicy:
    """Policy for selecting the best file from multiple candidates."""

    @staticmethod
    def prefer_newest_by(
        candidates: list[dict[str, Any]],
        strategy: str,
    ) -> dict[str, Any] | None:
        """
        Select newest candidate by given strategy.

        Args:
            candidates: List of candidate dicts with url, headers, filename, etc.
            strategy: Strategy name (last_modified, date_from_filename_or_last_modified, etc.)

        Returns:
            Selected candidate dict or None
        """
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Extract dates for each candidate
        scored = []
        for candidate in candidates:
            date_value = None
            headers = candidate.get("headers", {})
            filename = candidate.get("filename", "")
            regex_groups = candidate.get("regex_groups")

            if strategy == "last_modified":
                date_value = SelectionPolicy._parse_last_modified(headers)
            elif strategy == "date_from_filename_or_last_modified":
                date_value = SelectionPolicy._parse_date_from_filename_or_last_modified(
                    filename, headers, regex_groups
                )
            elif strategy == "best_effort_date_or_last_modified":
                date_value = SelectionPolicy._parse_best_effort_date(
                    filename, headers, regex_groups
                )

            if date_value:
                scored.append((date_value, candidate))
            else:
                # Candidates without date get lowest priority
                scored.append((datetime.min, candidate))

        # Sort by date descending (newest first)
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else None

    @staticmethod
    def prefer_ext(
        candidates: list[dict[str, Any]],
        preferred_extensions: list[str],
    ) -> list[dict[str, Any]]:
        """
        Filter and sort candidates by preferred extensions.

        Args:
            candidates: List of candidate dicts with url
            preferred_extensions: Ordered list of preferred extensions (e.g., [".xlsm", ".xlsx"])

        Returns:
            Filtered and sorted candidates (preferred first)
        """
        if not preferred_extensions:
            return candidates

        from urllib.parse import urlparse

        # Score candidates by extension preference
        scored = []
        for candidate in candidates:
            url = candidate.get("url", "")
            parsed = urlparse(url)
            path_lower = parsed.path.lower()

            # Find matching extension
            ext_score = len(preferred_extensions)
            for i, ext in enumerate(preferred_extensions):
                if path_lower.endswith(ext.lower()):
                    ext_score = i
                    break

            scored.append((ext_score, candidate))

        # Sort by extension preference (lower score = more preferred)
        scored.sort(key=lambda x: x[0])
        return [candidate for _, candidate in scored]

    @staticmethod
    def _parse_last_modified(headers: dict[str, Any]) -> datetime | None:
        """Parse Last-Modified header to datetime."""
        last_modified = headers.get("Last-Modified")
        if not last_modified:
            return None
        try:
            parsed = date_parser.parse(last_modified)
            if isinstance(parsed, datetime):
                return parsed
            return None
        except Exception:
            return None

    @staticmethod
    def _parse_date_from_filename_or_last_modified(
        filename: str,
        headers: dict[str, Any],
        regex_groups: list[str] | None,
    ) -> datetime | None:
        """Parse date from filename or Last-Modified."""
        # Try filename first
        version = VersioningPolicy.date_from_filename(filename, regex_groups)
        if version:
            try:
                date_str = version[1:]  # Remove 'v' prefix
                return datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                pass

        # Fallback to Last-Modified
        return SelectionPolicy._parse_last_modified(headers)

    @staticmethod
    def _parse_best_effort_date(
        filename: str,
        headers: dict[str, Any],
        regex_groups: list[str] | None,
    ) -> datetime | None:
        """Parse date using best effort strategy."""
        # Try various strategies
        version = VersioningPolicy.year_month_from_spanish_month(filename, "es")
        if version:
            try:
                return datetime.strptime(version, "%Y-%m")
            except Exception:
                pass

        version = VersioningPolicy.date_from_filename(filename, regex_groups)
        if version:
            try:
                date_str = version[1:]  # Remove 'v' prefix
                return datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                pass

        return SelectionPolicy._parse_last_modified(headers)


class AcceptancePolicy:
    """Policy for accepting or rejecting discovered files."""

    @staticmethod
    def mime_expected(
        mime: str,
        expected_mime_any: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Check if MIME type is acceptable.

        Args:
            mime: Actual MIME type
            expected_mime_any: List of acceptable MIME types

        Returns:
            Tuple of (is_acceptable, error_message)
        """
        if not expected_mime_any:
            return True, None

        mime_clean = mime.split(";")[0].strip().lower()
        for expected in expected_mime_any:
            if mime_clean == expected.lower():
                return True, None

        return False, f"MIME type {mime} not in expected list: {expected_mime_any}"

    @staticmethod
    def size_threshold(
        size_kb: float,
        min_size_kb: float | None = None,
    ) -> tuple[bool, str | None]:
        """
        Check if file size meets threshold.

        Args:
            size_kb: Actual size in KB
            min_size_kb: Minimum size in KB

        Returns:
            Tuple of (meets_threshold, error_message)
        """
        if min_size_kb is None:
            return True, None

        if size_kb < min_size_kb:
            return False, f"Size {size_kb:.2f} KB below minimum {min_size_kb} KB"

        return True, None
