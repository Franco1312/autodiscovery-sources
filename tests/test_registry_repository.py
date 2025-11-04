"""Tests for RegistryRepository."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from autodiscovery.domain.entities import SourceEntry
from autodiscovery.domain.interfaces import IRegistryRepository
from autodiscovery.infrastructure.registry_repository import RegistryRepository
from autodiscovery.registry.registry import RegistryManager


def test_registry_repository_get_entry():
    """Test getting an entry from registry."""
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

        repository = RegistryRepository(manager)
        retrieved_entry = repository.get_entry("test_key")

        assert retrieved_entry is not None
        assert retrieved_entry.url == entry.url
        assert retrieved_entry.version == entry.version
        assert retrieved_entry.sha256 == entry.sha256


def test_registry_repository_get_entry_not_found():
    """Test getting a non-existent entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        manager = RegistryManager(registry_path)
        repository = RegistryRepository(manager)

        entry = repository.get_entry("nonexistent")

        assert entry is None


def test_registry_repository_set_entry():
    """Test setting an entry in registry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        manager = RegistryManager(registry_path)
        repository = RegistryRepository(manager)

        entry = SourceEntry(
            url="https://example.com/file.xls",
            version="v2025-11-04",
            mime="application/vnd.ms-excel",
            size_kb=100.0,
            sha256="abc123",
        )
        repository.set_entry("test_key", entry)

        retrieved_entry = repository.get_entry("test_key")
        assert retrieved_entry is not None
        assert retrieved_entry.url == entry.url


def test_registry_repository_has_entry():
    """Test checking if entry exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        manager = RegistryManager(registry_path)
        repository = RegistryRepository(manager)

        entry = SourceEntry(
            url="https://example.com/file.xls",
            version="v2025-11-04",
            mime="application/vnd.ms-excel",
            size_kb=100.0,
            sha256="abc123",
        )
        repository.set_entry("test_key", entry)

        assert repository.has_entry("test_key") is True
        assert repository.has_entry("nonexistent") is False


def test_registry_repository_list_keys():
    """Test listing all keys in registry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        manager = RegistryManager(registry_path)
        repository = RegistryRepository(manager)

        entry1 = SourceEntry(
            url="https://example.com/file1.xls",
            version="v2025-11-04",
            mime="application/vnd.ms-excel",
            size_kb=100.0,
            sha256="abc123",
        )
        entry2 = SourceEntry(
            url="https://example.com/file2.xls",
            version="v2025-11-04",
            mime="application/vnd.ms-excel",
            size_kb=100.0,
            sha256="def456",
        )
        repository.set_entry("key1", entry1)
        repository.set_entry("key2", entry2)

        keys = repository.list_keys()
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

