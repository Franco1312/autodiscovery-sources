"""Tests for FileValidator."""

from unittest.mock import Mock

from httpx import Response

from autodiscovery.domain.interfaces import IHTTPPort
from autodiscovery.infrastructure.file_validator import FileValidator


def test_file_validator_valid_file():
    """Test validation of a valid file."""
    mock_client = Mock(spec=IHTTPPort)
    mock_response = Mock(spec=Response)
    mock_response.headers = {
        "content-type": "application/pdf",
        "content-length": "102400",
    }
    mock_response.raise_for_status = Mock()
    mock_client.head.return_value = mock_response

    validator = FileValidator(mock_client)
    is_valid, mime, size_kb = validator.validate_file("https://example.com/file.pdf", "test_key")

    assert is_valid is True
    assert mime == "application/pdf"
    assert size_kb == 100.0
    mock_client.head.assert_called_once_with("https://example.com/file.pdf", headers=None)


def test_file_validator_html_page():
    """Test validation rejects HTML pages."""
    mock_client = Mock(spec=IHTTPPort)
    mock_response = Mock(spec=Response)
    mock_response.headers = {
        "content-type": "text/html",
        "content-length": "1024",
    }
    mock_response.raise_for_status = Mock()
    mock_client.head.return_value = mock_response

    validator = FileValidator(mock_client)
    is_valid, mime, size_kb = validator.validate_file("https://example.com/page.html", "test_key")

    assert is_valid is False
    assert mime is None
    assert size_kb is None


def test_file_validator_small_file():
    """Test validation rejects files that are too small."""
    mock_client = Mock(spec=IHTTPPort)
    mock_response = Mock(spec=Response)
    mock_response.headers = {
        "content-type": "application/pdf",
        "content-length": "512",  # Less than 1KB
    }
    mock_response.raise_for_status = Mock()
    mock_client.head.return_value = mock_response

    validator = FileValidator(mock_client)
    is_valid, mime, size_kb = validator.validate_file("https://example.com/file.pdf", "test_key")

    assert is_valid is False
    assert mime is None
    assert size_kb is None


def test_file_validator_with_attachment():
    """Test validation accepts files with Content-Disposition attachment."""
    mock_client = Mock(spec=IHTTPPort)
    mock_response = Mock(spec=Response)
    mock_response.headers = {
        "content-type": "application/octet-stream",
        "content-length": "512",
        "content-disposition": "attachment; filename=file.pdf",
    }
    mock_response.raise_for_status = Mock()
    mock_client.head.return_value = mock_response

    validator = FileValidator(mock_client)
    is_valid, mime, size_kb = validator.validate_file("https://example.com/file.pdf", "test_key")

    assert is_valid is True
    assert mime == "application/octet-stream"
    assert size_kb == 0.5


def test_file_validator_http_error():
    """Test validation handles HTTP errors."""
    mock_client = Mock(spec=IHTTPPort)
    mock_client.head.side_effect = Exception("Network error")

    validator = FileValidator(mock_client)
    is_valid, mime, size_kb = validator.validate_file("https://example.com/file.pdf", "test_key")

    assert is_valid is False
    assert mime is None
    assert size_kb is None


def test_file_validator_with_min_size():
    """Test validation with minimum size requirement."""
    mock_client = Mock(spec=IHTTPPort)
    mock_response = Mock(spec=Response)
    mock_response.headers = {
        "content-type": "application/pdf",
        "content-length": "51200",  # 50KB
    }
    mock_response.raise_for_status = Mock()
    mock_client.head.return_value = mock_response

    validator = FileValidator(mock_client)
    is_valid, mime, size_kb = validator.validate_file(
        "https://example.com/file.pdf", "test_key", min_size_kb=100.0
    )

    assert is_valid is False  # File is 50KB but minimum is 100KB
    assert mime is None
    assert size_kb is None
