"""Tests for autodiscovery."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from autodiscovery.config import Config
from autodiscovery.registry.models import Registry, SourceEntry
from autodiscovery.registry.registry import RegistryManager
from autodiscovery.util.date import (
    normalize_spanish_month,
    version_from_date_filename,
    version_from_date_today,
    version_from_year_month,
)


def test_normalize_spanish_month():
    """Test Spanish month normalization."""
    assert normalize_spanish_month("enero") == "01"
    assert normalize_spanish_month("noviembre") == "11"
    assert normalize_spanish_month("sep") == "09"
    assert normalize_spanish_month("dic") == "12"
    assert normalize_spanish_month("unknown") is None


def test_version_from_date_today():
    """Test version generation from today's date."""
    version = version_from_date_today()
    assert version.startswith("v")
    assert len(version) == 11  # vYYYY-MM-DD


def test_version_from_date_filename():
    """Test version generation from date in filename."""
    assert version_from_date_filename("2025-11-04") == "v2025-11-04"


def test_version_from_year_month():
    """Test version generation from year and month."""
    assert version_from_year_month("2025", "11") == "2025-11"
    assert version_from_year_month("2025", "noviembre") == "2025-11"
    assert version_from_year_month("2025", "sep") == "2025-09"


def test_registry_atomic_write():
    """Test registry atomic write operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        manager = RegistryManager(registry_path)

        # Create entry
        entry = SourceEntry(
            url="https://example.com/file.xls",
            version="v2025-11-04",
            mime="application/vnd.ms-excel",
            size_kb=100.0,
            sha256="abc123",
        )

        # Save
        manager.set_entry("test_key", entry)

        # Verify file exists
        assert registry_path.exists()

        # Load and verify
        loaded_entry = manager.get_entry("test_key")
        assert loaded_entry is not None
        assert loaded_entry.url == entry.url
        assert loaded_entry.version == entry.version
        assert loaded_entry.sha256 == entry.sha256

        # Verify JSON structure
        with open(registry_path, "r") as f:
            data = json.load(f)
            assert "entries" in data
            assert "test_key" in data["entries"]


def test_registry_list_keys():
    """Test registry key listing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        manager = RegistryManager(registry_path)

        # Add multiple entries
        for i in range(3):
            entry = SourceEntry(
                url=f"https://example.com/file{i}.xls",
                version="v2025-11-04",
                mime="application/vnd.ms-excel",
                size_kb=100.0,
                sha256="abc123",
            )
            manager.set_entry(f"key_{i}", entry)

        # List keys
        keys = manager.list_keys()
        assert len(keys) == 3
        assert "key_0" in keys
        assert "key_1" in keys
        assert "key_2" in keys


def test_registry_has_entry():
    """Test registry entry existence check."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        manager = RegistryManager(registry_path)

        entry = SourceEntry(
            url="https://example.com/file.xls",
            version="v2025-11-04",
            mime="application/vnd.ms-excel",
            size_kb=100.0,
            sha256="abc123",
        )

        manager.set_entry("test_key", entry)

        assert manager.has_entry("test_key")
        assert not manager.has_entry("nonexistent_key")


@patch("autodiscovery.html.fetch_html")
def test_bcra_series_discoverer(mock_fetch_html):
    """Test BCRA series discoverer."""
    from bs4 import BeautifulSoup
    from autodiscovery.http import HTTPClient
    from autodiscovery.sources.bcra_series import BCRASeriesDiscoverer

    # Mock HTML with series.xlsm link
    html_content = """
    <html>
    <body>
        <a href="/Pdfs/PublicacionesEstadisticas/series.xlsm">Series</a>
    </body>
    </html>
    """
    mock_soup = BeautifulSoup(html_content, "lxml")
    mock_fetch_html.return_value = mock_soup

    with HTTPClient() as client:
        discoverer = BCRASeriesDiscoverer(client)
        result = discoverer.discover(["https://example.com/page"])

        # Should find series.xlsm
        assert result is not None
        assert "series.xlsm" in result.url.lower()


@patch("autodiscovery.html.fetch_html")
def test_bcra_infomodia_discoverer(mock_fetch_html):
    """Test BCRA infomodia discoverer."""
    from bs4 import BeautifulSoup
    from autodiscovery.http import HTTPClient
    from autodiscovery.sources.bcra_infomodia import BCRAInfomodiaDiscoverer

    # Mock HTML with multiple infomodia files
    html_content = """
    <html>
    <body>
        <a href="/infomodia-2025-10-01.xls">Infomodia Oct</a>
        <a href="/infomodia-2025-11-04.xls">Infomodia Nov</a>
        <a href="/infomodia-2025-09-15.xls">Infomodia Sep</a>
    </body>
    </html>
    """
    mock_soup = BeautifulSoup(html_content, "lxml")
    mock_fetch_html.return_value = mock_soup

    with HTTPClient() as client:
        discoverer = BCRAInfomodiaDiscoverer(client)
        result = discoverer.discover(["https://example.com/page"])

        # Should find the most recent (2025-11-04)
        assert result is not None
        assert "2025-11-04" in result.url


def test_registry_model():
    """Test Pydantic registry models."""
    entry = SourceEntry(
        url="https://example.com/file.xls",
        version="v2025-11-04",
        mime="application/vnd.ms-excel",
        size_kb=100.0,
        sha256="abc123",
        notes="Test notes",
    )

    # Test serialization
    data = entry.model_dump()
    assert data["url"] == "https://example.com/file.xls"
    assert data["version"] == "v2025-11-04"
    assert data["sha256"] == "abc123"

    # Test deserialization
    registry = Registry(entries={"test_key": entry})
    assert registry.has("test_key")
    assert registry.get("test_key") == entry

