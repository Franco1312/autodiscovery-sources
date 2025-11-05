"""Tests for atomic registry operations."""

import json
from datetime import datetime
from pathlib import Path

from autodiscovery_sources.domain.entities import RegistryEntry
from autodiscovery_sources.domain.value_objects import Sha256, Url
from autodiscovery_sources.infrastructure.registry_fs_adapter import RegistryFsAdapter


def test_registry_atomic_write(temp_dir):
    """Test atomic write to registry."""
    registry_path = temp_dir / "registry.json"
    registry = RegistryFsAdapter(str(registry_path))
    
    entry = RegistryEntry(
        key="test_key",
        url=Url(value="https://example.com/test.xlsx"),
        version="2023-10-30",
        filename="test.xlsx",
        sha256=Sha256(value="a" * 64),
        last_checked=datetime.now(),
        status="ok",
    )
    
    # Upsert
    registry.upsert(entry)
    
    # Verify file exists and is valid JSON
    assert registry_path.exists()
    data = json.loads(registry_path.read_text())
    assert "test_key" in data
    assert data["test_key"]["key"] == "test_key"


def test_registry_load():
    """Test loading registry."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create initial registry
        initial_data = {
            "test_key": {
                "key": "test_key",
                "url": {"value": "https://example.com/test.xlsx"},
                "version": "2023-10-30",
                "filename": "test.xlsx",
                "sha256": {"value": "a" * 64},
                "last_checked": "2023-10-30T12:00:00",
                "status": "ok",
            }
        }
        registry_path.write_text(json.dumps(initial_data))
        
        registry = RegistryFsAdapter(str(registry_path))
        entries = registry.load()
        
        assert "test_key" in entries
        assert entries["test_key"].key == "test_key"


def test_registry_get_by_key(temp_dir):
    """Test getting entry by key."""
    registry_path = temp_dir / "registry.json"
    registry = RegistryFsAdapter(str(registry_path))
    
    entry = RegistryEntry(
        key="test_key",
        url=Url(value="https://example.com/test.xlsx"),
        version="2023-10-30",
        filename="test.xlsx",
        sha256=Sha256(value="a" * 64),
        last_checked=datetime.now(),
        status="ok",
    )
    
    registry.upsert(entry)
    
    retrieved = registry.get_by_key("test_key")
    assert retrieved is not None
    assert retrieved.key == "test_key"
    assert retrieved.version == "2023-10-30"

