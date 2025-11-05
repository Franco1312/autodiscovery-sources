"""Selector for choosing best candidate from validated files."""

from typing import Dict, List, Optional

from ..domain.entities import DiscoveredFile
from ..domain.policies import SelectionPolicy, VersioningPolicy
from ..interfaces.logger_port import LoggerPort


class Selector:
    """Selector for choosing best candidate."""

    def __init__(self, logger: LoggerPort):
        """Initialize selector."""
        self.logger = logger

    def select(
        self, candidates: List[DiscoveredFile], select_config: Dict, match_config: Dict
    ) -> Optional[DiscoveredFile]:
        """Select best candidate using selection policies.
        
        Args:
            candidates: List of validated candidates
            select_config: Selection configuration (prefer_ext, prefer_newest_by)
            match_config: Match configuration (for date extraction patterns)
        
        Returns:
            Selected candidate or None
        """
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Apply prefer_ext
        prefer_ext = select_config.get("prefer_ext", [])
        if prefer_ext:
            candidates = SelectionPolicy.prefer_ext(candidates, prefer_ext)
        
        # Apply prefer_newest_by
        prefer_newest_by = select_config.get("prefer_newest_by", "last_modified")
        
        # Get patterns for date extraction
        patterns = match_config.get("patterns", [])
        
        # Create headers dict from candidates (for date extraction)
        # Extract last_modified from candidates if available
        headers = {}
        for candidate in candidates:
            if candidate.last_modified:
                # Convert datetime to HTTP date format
                headers["last-modified"] = candidate.last_modified.strftime(
                    "%a, %d %b %Y %H:%M:%S %Z"
                )
                break
        
        # Select using prefer_newest_by
        selected = SelectionPolicy.prefer_newest_by(
            candidates,
            prefer_newest_by,
            filename=candidates[0].filename if candidates else "",
            headers=headers,
            regexes=patterns,
        )
        
        if selected:
            self.logger.info(
                "Candidate selected",
                url=selected.url.value,
                filename=selected.filename,
                score=selected.score,
            )
        
        return selected

