"""Service for pattern matching in URLs."""

import re


class PatternMatcherService:
    """Service for matching URLs against patterns and keywords."""

    def extract_keywords_from_patterns(self, patterns: list[str] | None) -> list[str]:
        """Extract simple keywords from regex patterns to use for fast filtering."""
        if not patterns:
            return []

        keywords = []
        for pattern in patterns:
            simplified = pattern
            simplified = re.sub(r"\(\?i\)", "", simplified, flags=re.IGNORECASE)
            simplified = re.sub(r"[\$\^]", "", simplified)
            simplified = re.sub(
                r"\\.", lambda m: m.group(0)[-1] if m.group(0)[-1].isalnum() else "", simplified
            )
            words = re.findall(r"[a-zA-Z0-9]+", simplified)
            keywords.extend([w.lower() for w in words if len(w) >= 3])

        return list(set(keywords))

    def url_matches_patterns(self, url: str, patterns: list[str] | None) -> bool:
        """Check if URL matches any of the patterns."""
        if not patterns:
            return True

        url_lower = url.lower()
        for pattern in patterns:
            try:
                if re.search(pattern, url_lower, re.IGNORECASE):
                    return True
            except re.error:
                continue
        return False

    def url_contains_keywords(self, url: str, keywords: list[str] | None) -> bool:
        """Check if URL contains any of the keywords."""
        if not keywords:
            return True

        url_lower = url.lower()
        return any(keyword in url_lower for keyword in keywords)

    def should_crawl_link(
        self,
        link_url: str,
        match_keywords: list[str] | None,
        match_patterns: list[str] | None,
    ) -> bool:
        """Check if HTML link should be crawled based on keywords/patterns."""
        if not (match_keywords or match_patterns):
            return True

        if match_keywords and not self.url_contains_keywords(link_url, match_keywords):
            return False

        # If patterns don't match and keywords don't match either, don't crawl
        # Return True if patterns match OR (patterns don't match but keywords match)
        return not (
            match_patterns
            and not self.url_matches_patterns(link_url, match_patterns)
            and (not match_keywords or not self.url_contains_keywords(link_url, match_keywords))
        )
