"""Tests for DiscovererFactory."""

from unittest.mock import Mock

from autodiscovery.domain.interfaces import IHTTPPort, ISourceDiscovererPort
from autodiscovery.infrastructure.discoverer_factory import DiscovererFactory


def test_discoverer_factory_create_bcra_series():
    """Test creating BCRA series discoverer."""
    mock_client = Mock(spec=IHTTPPort)
    discoverer = DiscovererFactory.create("bcra_series", mock_client)

    assert discoverer is not None
    assert isinstance(discoverer, ISourceDiscovererPort)


def test_discoverer_factory_create_bcra_infomodia():
    """Test creating BCRA infomodia discoverer."""
    mock_client = Mock(spec=IHTTPPort)
    discoverer = DiscovererFactory.create("bcra_infomodia", mock_client)

    assert discoverer is not None
    assert isinstance(discoverer, ISourceDiscovererPort)


def test_discoverer_factory_create_bcra_rem():
    """Test creating BCRA REM discoverer."""
    mock_client = Mock(spec=IHTTPPort)
    discoverer = DiscovererFactory.create("bcra_rem_pdf", mock_client)

    assert discoverer is not None
    assert isinstance(discoverer, ISourceDiscovererPort)


def test_discoverer_factory_create_indec_emae():
    """Test creating INDEC EMAE discoverer."""
    mock_client = Mock(spec=IHTTPPort)
    discoverer = DiscovererFactory.create("indec_emae", mock_client)

    assert discoverer is not None
    assert isinstance(discoverer, ISourceDiscovererPort)


def test_discoverer_factory_create_unknown():
    """Test creating unknown discoverer."""
    mock_client = Mock(spec=IHTTPPort)
    discoverer = DiscovererFactory.create("unknown_key", mock_client)

    assert discoverer is None


def test_discoverer_factory_get_available_keys():
    """Test getting available discoverer keys."""
    keys = DiscovererFactory.get_available_keys()

    assert len(keys) > 0
    assert "bcra_series" in keys
    assert "bcra_infomodia" in keys
    assert "bcra_rem_pdf" in keys
    assert "indec_emae" in keys


def test_discoverer_factory_register():
    """Test registering a new discoverer."""
    mock_client = Mock(spec=IHTTPPort)
    mock_discoverer_class = Mock(spec=ISourceDiscovererPort)
    mock_discoverer_class.return_value = Mock(spec=ISourceDiscovererPort)

    # Register new discoverer
    DiscovererFactory.register("test_discoverer", mock_discoverer_class)

    # Create it
    discoverer = DiscovererFactory.create("test_discoverer", mock_client)
    assert discoverer is not None

    # Clean up
    DiscovererFactory._discoverers.pop("test_discoverer", None)
