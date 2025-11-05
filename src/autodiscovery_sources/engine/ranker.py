"""Heuristic ranker for discovered file candidates."""

import re
from typing import Dict, List

from ..domain.entities import DiscoveredFile
from ..domain.policies import VersioningPolicy


class Ranker:
    """Heuristic ranker for scoring candidates."""

    # Strong tokens for scoring
    STRONG_TOKENS = [
        "rem",
        "infomondia",
        "infomodia",
        "series",
        "publicacionesestadisticas",
        "tablas",
        "resultados",
        "informe",
        "monetario",
    ]

    def __init__(self):
        """Initialize ranker."""
        pass

    def rank(self, candidates: List[DiscoveredFile], match_config: Dict) -> List[DiscoveredFile]:
        """Rank candidates by heuristic score (0-100).
        
        Scoring:
        - +30 if extension matches (xlsx/xlsm/xls/pdf)
        - +10 per strong token in URL
        - +10 if anchor text contains strong tokens
        - +20 if date detected in filename
        - +10 if path matches allow_paths_any
        """
        patterns = match_config.get("patterns", [])
        
        for candidate in candidates:
            score = 0
            url_lower = candidate.url.value.lower()
            filename_lower = candidate.filename.lower()
            
            # Extension bonus
            if any(
                filename_lower.endswith(ext)
                for ext in [".xlsx", ".xlsm", ".xls", ".pdf"]
            ):
                score += 30
            
            # Strong token bonus
            for token in self.STRONG_TOKENS:
                if token in url_lower:
                    score += 10
            
            # Date detection bonus
            date = VersioningPolicy.date_from_filename(candidate.filename, patterns)
            if date:
                score += 20
            
            # Path bonus (if path contains strong tokens)
            from urllib.parse import urlparse
            parsed = urlparse(candidate.url.value)
            path_lower = parsed.path.lower()
            for token in self.STRONG_TOKENS:
                if token in path_lower:
                    score += 5
            
            # Cap at 100
            candidate.score = min(score, 100)
        
        # Sort by score descending
        ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
        
        return ranked

