"""Tests for versioning policies."""

from autodiscovery_sources.domain.policies import VersioningPolicy


def test_date_from_filename_yyyy_mm_dd():
    """Test extracting date from filename in YYYY-MM-DD format."""
    filename = "test-2023-10-30.xlsx"
    regexes = [r"(\d{4}-\d{2}-\d{2})"]
    
    date = VersioningPolicy.date_from_filename(filename, regexes)
    assert date == "2023-10-30"


def test_date_from_filename_rem():
    """Test extracting date from REM format."""
    filename = "REM231030-Resultados.pdf"
    regexes = [r"REM(\d{2})(\d{2})(\d{2,4})"]
    
    date = VersioningPolicy.date_from_filename(filename, regexes)
    assert date == "2023-10-30"


def test_date_from_last_modified():
    """Test extracting date from Last-Modified header."""
    headers = {"Last-Modified": "Mon, 30 Oct 2023 12:00:00 GMT"}
    
    date = VersioningPolicy.from_last_modified(headers)
    assert date == "2023-10-30"


def test_date_today():
    """Test date_today strategy."""
    date = VersioningPolicy.date_today()
    assert len(date) == 10  # YYYY-MM-DD
    assert date.count("-") == 2


def test_best_effort_date_or_last_modified():
    """Test best effort date extraction."""
    filename = "REM231030-Resultados.pdf"
    regexes = [r"REM(\d{2})(\d{2})(\d{2,4})"]
    headers = {}
    
    date = VersioningPolicy.best_effort_date_or_last_modified(filename, regexes, headers)
    assert date == "2023-10-30"
    
    # Test fallback to last-modified
    filename_no_date = "test.pdf"
    headers_with_date = {"Last-Modified": "Mon, 30 Oct 2023 12:00:00 GMT"}
    
    date = VersioningPolicy.best_effort_date_or_last_modified(filename_no_date, regexes, headers_with_date)
    assert date == "2023-10-30"

