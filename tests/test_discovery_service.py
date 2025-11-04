"""Tests for DiscoveryService."""

from unittest.mock import Mock

from autodiscovery.application.services.discovery_service import DiscoveryService
from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.domain.interfaces import ISourceDiscoverer


def test_discovery_service_discover_success():
    """Test successful discovery."""
    mock_discoverer = Mock(spec=ISourceDiscoverer)
    mock_discoverer.discover.return_value = DiscoveredFile(
        url="https://example.com/file.xls",
        version="v2025-11-04",
        filename="file.xls",
    )

    service = DiscoveryService(mock_discoverer)
    result = service.discover(["https://example.com"])

    assert result is not None
    assert result.url == "https://example.com/file.xls"
    assert result.version == "v2025-11-04"
    mock_discoverer.discover.assert_called_once_with(["https://example.com"])


def test_discovery_service_discover_failure():
    """Test discovery failure."""
    mock_discoverer = Mock(spec=ISourceDiscoverer)
    mock_discoverer.discover.return_value = None

    service = DiscoveryService(mock_discoverer)
    result = service.discover(["https://example.com"])

    assert result is None
    mock_discoverer.discover.assert_called_once_with(["https://example.com"])


def test_discovery_service_discover_exception():
    """Test discovery with exception."""
    mock_discoverer = Mock(spec=ISourceDiscoverer)
    mock_discoverer.discover.side_effect = Exception("Network error")

    service = DiscoveryService(mock_discoverer)
    result = service.discover(["https://example.com"])

    assert result is None
    mock_discoverer.discover.assert_called_once_with(["https://example.com"])
