"""Domain policies for versioning, selection, and acceptance."""

import re
from datetime import datetime
from typing import List, Optional

from .value_objects import MimeType


class VersioningPolicy:
    """Policy for extracting version from files."""

    # Map Spanish month names to numbers
    MONTH_ES = {
        "ene": 1, "enero": 1,
        "feb": 2, "febrero": 2,
        "mar": 3, "marzo": 3,
        "abr": 4, "abril": 4,
        "may": 5, "mayo": 5,
        "jun": 6, "junio": 6,
        "jul": 7, "julio": 7,
        "ago": 8, "agosto": 8,
        "sep": 9, "septiembre": 9, "sept": 9,
        "oct": 10, "octubre": 10,
        "nov": 11, "noviembre": 11,
        "dic": 12, "diciembre": 12,
    }

    @classmethod
    def date_from_filename(cls, filename: str, regexes: List[str]) -> Optional[str]:
        """Extract date from filename using regex patterns.
        
        Returns YYYY-MM-DD format or None.
        """
        for pattern in regexes:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                # Try YYYY-MM-DD
                if len(match.groups()) >= 1:
                    date_str = match.group(1)
                    # Check if it's YYYY-MM-DD
                    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
                        return date_str
                    # Check if it's REMYYMMDD
                    rem_match = re.search(r"REM(\d{2})(\d{2})(\d{2,4})", date_str, re.IGNORECASE)
                    if rem_match:
                        yy = rem_match.group(1)
                        mm = rem_match.group(2)
                        dd = rem_match.group(3)
                        # Convert 2-digit year to 4-digit (assuming 2000s)
                        year = int(f"20{yy}") if len(yy) == 2 else int(yy)
                        return f"{year}-{mm}-{dd}"
                # Try to extract date from full match
                full_match = match.group(0)
                # Check for REM format in full match
                rem_match = re.search(r"REM(\d{2})(\d{2})(\d{2,4})", full_match, re.IGNORECASE)
                if rem_match:
                    yy = rem_match.group(1)
                    mm = rem_match.group(2)
                    dd = rem_match.group(3)
                    year = int(f"20{yy}") if len(yy) == 2 else int(yy)
                    return f"{year}-{mm}-{dd}"
                # Look for YYYY-MM-DD in full match
                date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", full_match)
                if date_match:
                    return date_match.group(0)
                # Look for Spanish month format: mes-ES YYYY or mes-ES-YYYY
                for month_name, month_num in cls.MONTH_ES.items():
                    pattern_es = rf"({month_name})[-_ ]?(\d{{4}})"
                    es_match = re.search(pattern_es, full_match, re.IGNORECASE)
                    if es_match:
                        year = es_match.group(2)
                        # Try to find day if present
                        day_match = re.search(rf"(\d{{1,2}})[-_ ]{month_name}", full_match, re.IGNORECASE)
                        day = day_match.group(1) if day_match else "01"
                        return f"{year}-{month_num:02d}-{int(day):02d}"
        return None

    @classmethod
    def from_last_modified(cls, headers: dict) -> Optional[str]:
        """Extract date from Last-Modified header.
        
        Returns YYYY-MM-DD format or None.
        """
        last_modified = headers.get("Last-Modified") or headers.get("last-modified")
        if not last_modified:
            return None
        try:
            # Parse HTTP date format
            dt = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            # Try alternative formats
            try:
                dt = datetime.strptime(last_modified, "%Y-%m-%d")
                return last_modified
            except ValueError:
                return None

    @classmethod
    def date_from_filename_or_last_modified(
        cls, filename: str, regexes: List[str], headers: dict
    ) -> Optional[str]:
        """Try filename first, then Last-Modified."""
        date = cls.date_from_filename(filename, regexes)
        if date:
            return date
        return cls.from_last_modified(headers)

    @classmethod
    def best_effort_date_or_last_modified(
        cls, filename: str, regexes: List[str], headers: dict
    ) -> Optional[str]:
        """Best effort: try multiple strategies."""
        # Try filename with regexes
        date = cls.date_from_filename(filename, regexes)
        if date:
            return date
        # Try common date patterns in filename
        common_patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"REM(\d{2})(\d{2})(\d{2,4})",
            r"(\d{4})(\d{2})(\d{2})",
        ]
        date = cls.date_from_filename(filename, common_patterns)
        if date:
            return date
        # Fall back to Last-Modified
        return cls.from_last_modified(headers)

    @classmethod
    def date_today(cls) -> str:
        """Return today's date in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")


class SelectionPolicy:
    """Policy for selecting best candidate from discovered files."""

    @classmethod
    def prefer_ext(cls, candidates: List, extensions: List[str]) -> List:
        """Filter candidates by preferred extensions, preserving order."""
        if not extensions:
            return candidates
        # Normalize extensions (ensure they start with .)
        normalized = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]
        result = []
        for ext in normalized:
            for candidate in candidates:
                if candidate.filename.lower().endswith(ext.lower()):
                    if candidate not in result:
                        result.append(candidate)
        # Add any remaining candidates not in preferred list
        for candidate in candidates:
            if candidate not in result:
                result.append(candidate)
        return result

    @classmethod
    def prefer_newest_by(
        cls, candidates: List, method: str, filename: str = "", headers: dict = None, regexes: List[str] = None
    ) -> Optional:
        """Select newest candidate by specified method.
        
        Methods:
        - last_modified: Use Last-Modified header
        - date_from_filename_or_last_modified: Try filename regex then Last-Modified
        - best_effort_date_or_last_modified: Multiple strategies
        """
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        headers = headers or {}
        regexes = regexes or []  # Will be populated by caller if needed

        if method == "last_modified":
            # Sort by last_modified descending
            sorted_candidates = sorted(
                candidates,
                key=lambda c: c.last_modified or datetime.min,
                reverse=True,
            )
            return sorted_candidates[0]

        elif method == "date_from_filename_or_last_modified":
            # Extract dates and sort
            candidates_with_dates = []
            for candidate in candidates:
                date = VersioningPolicy.date_from_filename_or_last_modified(
                    candidate.filename, regexes, headers
                )
                if date:
                    try:
                        dt = datetime.strptime(date, "%Y-%m-%d")
                        candidates_with_dates.append((dt, candidate))
                    except ValueError:
                        pass
            if candidates_with_dates:
                candidates_with_dates.sort(key=lambda x: x[0], reverse=True)
                return candidates_with_dates[0][1]
            # Fallback to last_modified
            return cls.prefer_newest_by(candidates, "last_modified")

        elif method == "best_effort_date_or_last_modified":
            # Similar but with best_effort strategy
            candidates_with_dates = []
            for candidate in candidates:
                date = VersioningPolicy.best_effort_date_or_last_modified(
                    candidate.filename, regexes, headers
                )
                if date:
                    try:
                        dt = datetime.strptime(date, "%Y-%m-%d")
                        candidates_with_dates.append((dt, candidate))
                    except ValueError:
                        pass
            if candidates_with_dates:
                candidates_with_dates.sort(key=lambda x: x[0], reverse=True)
                return candidates_with_dates[0][1]
            # Fallback to last_modified
            return cls.prefer_newest_by(candidates, "last_modified")

        # Default: return first candidate
        return candidates[0]


class AcceptancePolicy:
    """Policy for accepting discovered files."""

    @classmethod
    def check_mime(cls, expected_any: List[str], got: Optional[str]) -> bool:
        """Check if MIME type matches any expected value."""
        if not expected_any:
            return True
        if not got:
            return False
        got_lower = got.lower()
        for expected in expected_any:
            if expected.lower() == got_lower:
                return True
        return False

    @classmethod
    def check_min_size(cls, min_kb: float, got_kb: Optional[float]) -> bool:
        """Check if size meets minimum requirement."""
        if min_kb is None or min_kb <= 0:
            return True
        if got_kb is None:
            return False
        return got_kb >= min_kb

