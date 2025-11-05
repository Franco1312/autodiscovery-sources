"""Tests for crawler prefiltering."""

from unittest.mock import Mock, patch

from autodiscovery_sources.domain.entities import DiscoveredFile
from autodiscovery_sources.engine.crawler import Crawler


def test_prefilter_match():
    """Test prefilter matching logic."""
    http_mock = Mock()
    html_mock = Mock()
    logger_mock = Mock()
    
    crawler = Crawler(http_mock, html_mock, logger_mock)
    
    # Test link text match
    assert crawler._prefilter_match(
        "https://example.com/file.xlsx",
        "Download test file",
        ["test"],
        []
    ) is True
    
    # Test URL token match
    assert crawler._prefilter_match(
        "https://example.com/test-file.xlsx",
        "Download",
        [],
        ["test"]
    ) is True
    
    # Test no match
    assert crawler._prefilter_match(
        "https://example.com/other.xlsx",
        "Other file",
        ["test"],
        ["test"]
    ) is False
    
    # Test no filters (accept all)
    assert crawler._prefilter_match(
        "https://example.com/file.xlsx",
        "Any file",
        [],
        []
    ) is True


def test_extract_filename():
    """Test filename extraction."""
    http_mock = Mock()
    html_mock = Mock()
    logger_mock = Mock()
    
    crawler = Crawler(http_mock, html_mock, logger_mock)
    
    # Test from URL
    filename = crawler._extract_filename("https://example.com/test-file.xlsx")
    assert "test-file.xlsx" in filename
    
    # Test from Content-Disposition header
    headers = {"content-disposition": 'attachment; filename="test.xlsx"'}
    filename = crawler._extract_filename("https://example.com/file", headers)
    assert "test.xlsx" == filename

