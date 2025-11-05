"""Tests for validator HEAD/GET fallback."""

from unittest.mock import Mock

from autodiscovery_sources.domain.entities import DiscoveredFile
from autodiscovery_sources.domain.value_objects import Url
from autodiscovery_sources.engine.validator import Validator


def test_validator_head_fallback():
    """Test validator HEAD failure with GET fallback."""
    http_mock = Mock()
    logger_mock = Mock()
    
    # Mock HEAD failure, GET success
    http_mock.head.return_value = (None, "HEAD failed")
    http_mock.get.return_value = (
        b"test content",
        {"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "content-length": "12"},
        None,
    )
    
    validator = Validator(http_mock, logger_mock)
    
    candidates = [
        DiscoveredFile(
            key="test",
            url=Url(value="https://example.com/test.xlsx"),
            filename="test.xlsx",
            score=50,
        )
    ]
    
    expect_config = {
        "mime_any": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        "min_size_kb": 0.01,  # 12 bytes = 0.01 KB
    }
    
    valid = validator.validate(candidates, expect_config)
    
    assert len(valid) == 1
    assert valid[0].notes == "head_failed_get_ok"
    assert valid[0].mime is not None


def test_validator_mime_mismatch():
    """Test validator MIME mismatch."""
    http_mock = Mock()
    logger_mock = Mock()
    
    http_mock.head.return_value = (
        {"content-type": "text/html", "content-length": "1000"},
        None,
    )
    
    validator = Validator(http_mock, logger_mock)
    
    candidates = [
        DiscoveredFile(
            key="test",
            url=Url(value="https://example.com/test.xlsx"),
            filename="test.xlsx",
            score=50,
        )
    ]
    
    expect_config = {
        "mime_any": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        "min_size_kb": 0,
    }
    
    valid = validator.validate(candidates, expect_config)
    
    # Should be filtered out due to MIME mismatch
    assert len(valid) == 0

