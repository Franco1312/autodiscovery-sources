"""Versioning helpers for extracted files."""

from typing import Dict, Optional

from ..domain.policies import VersioningPolicy


class Versioning:
    """Versioning helpers."""

    @staticmethod
    def extract_version(
        versioning_strategy: str,
        filename: str,
        match_config: Dict,
        headers: Dict = None,
    ) -> str:
        """Extract version string based on strategy.
        
        Strategies:
        - date_today: Use today's date
        - date_from_filename_or_last_modified: Try filename then Last-Modified
        - best_effort_date_or_last_modified: Multiple strategies
        - none: Return "none"
        """
        headers = headers or {}
        patterns = match_config.get("patterns", [])
        
        if versioning_strategy == "date_today":
            return VersioningPolicy.date_today()
        
        elif versioning_strategy == "date_from_filename_or_last_modified":
            version = VersioningPolicy.date_from_filename_or_last_modified(
                filename, patterns, headers
            )
            return version or "unknown"
        
        elif versioning_strategy == "best_effort_date_or_last_modified":
            version = VersioningPolicy.best_effort_date_or_last_modified(
                filename, patterns, headers
            )
            return version or "unknown"
        
        elif versioning_strategy == "none":
            return "none"
        
        else:
            # Default: try best effort
            version = VersioningPolicy.best_effort_date_or_last_modified(
                filename, patterns, headers
            )
            return version or "unknown"

