"""Date and version utilities."""

import re
from datetime import datetime
from typing import Optional

# Spanish month names mapping
SPANISH_MONTHS = {
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
    # Abbreviated
    "ene": "01",
    "feb": "02",
    "mar": "03",
    "abr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "ago": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dic": "12",
}


def normalize_spanish_month(month_str: str) -> Optional[str]:
    """Normalize Spanish month name/abbreviation to MM."""
    month_lower = month_str.lower().strip()
    return SPANISH_MONTHS.get(month_lower)


def version_from_date_today() -> str:
    """Generate version string from today's date: vYYYY-MM-DD."""
    today = datetime.now().date()
    return f"v{today.strftime('%Y-%m-%d')}"


def version_from_date_filename(date_str: str) -> str:
    """Generate version from date string in filename: YYYY-MM-DD -> vYYYY-MM-DD."""
    return f"v{date_str}"


def version_from_year_month(year: str, month: str) -> str:
    """Generate version from year and month: YYYY-MM."""
    # Normalize month if it's Spanish
    month_num = normalize_spanish_month(month)
    if month_num:
        month = month_num
    elif len(month) == 1:
        month = f"0{month}"
    return f"{year}-{month}"


def extract_date_from_filename(filename: str, pattern: str) -> Optional[str]:
    """Extract date from filename using regex pattern."""
    match = re.search(pattern, filename)
    if match:
        # Try to extract YYYY-MM-DD format
        groups = match.groups()
        if len(groups) >= 3:
            year, month, day = groups[0], groups[1], groups[2]
            return f"{year}-{month}-{day}"
        elif len(groups) >= 2:
            year, month = groups[0], groups[1]
            return f"{year}-{month}"
    return None

