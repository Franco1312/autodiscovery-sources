"""Pytest configuration and fixtures."""

import json
import tempfile
from pathlib import Path

import pytest

from autodiscovery_sources.infrastructure.bs4_adapter import Bs4Adapter
from autodiscovery_sources.infrastructure.clock_adapter import ClockAdapter
from autodiscovery_sources.infrastructure.contracts_yaml_adapter import ContractsYamlAdapter
from autodiscovery_sources.infrastructure.httpx_adapter import HttpxAdapter
from autodiscovery_sources.infrastructure.logger_structlog_adapter import LoggerStructlogAdapter
from autodiscovery_sources.infrastructure.metrics_memory_adapter import MetricsMemoryAdapter
from autodiscovery_sources.infrastructure.mirror_fs_adapter import MirrorFsAdapter
from autodiscovery_sources.infrastructure.registry_fs_adapter import RegistryFsAdapter


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def contracts_file(temp_dir):
    """Create a test contracts YAML file."""
    contracts_path = temp_dir / "contracts" / "sources.yml"
    contracts_path.parent.mkdir(parents=True, exist_ok=True)
    
    contracts_data = [
        {
            "key": "test_source",
            "start_urls": ["https://example.com/test"],
            "scope": {"allow_domains": ["example.com"], "max_depth": 1, "max_candidates": 1},
            "find": {"link_text_any": ["test"], "url_tokens_any": ["test"]},
            "match": {"kind": "regex_any", "patterns": ["(?i)test\\.xlsx$"]},
            "select": {"prefer_ext": [".xlsx"], "prefer_newest_by": "last_modified"},
            "expect": {"mime_any": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"], "min_size_kb": 10},
            "versioning": "date_today",
            "mirror": True,
        }
    ]
    
    import yaml
    with open(contracts_path, "w") as f:
        yaml.dump(contracts_data, f)
    
    return str(contracts_path)


@pytest.fixture
def registry_file(temp_dir):
    """Create a test registry JSON file."""
    registry_path = temp_dir / "registry" / "registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    return str(registry_path)


@pytest.fixture
def mirrors_dir(temp_dir):
    """Create a test mirrors directory."""
    mirrors_path = temp_dir / "mirrors"
    mirrors_path.mkdir(parents=True, exist_ok=True)
    return str(mirrors_path)


@pytest.fixture
def contracts_adapter(contracts_file):
    """Create contracts adapter."""
    return ContractsYamlAdapter(contracts_file)


@pytest.fixture
def registry_adapter(registry_file):
    """Create registry adapter."""
    return RegistryFsAdapter(registry_file)


@pytest.fixture
def mirror_adapter(mirrors_dir):
    """Create mirror adapter."""
    return MirrorFsAdapter(mirrors_dir)


@pytest.fixture
def http_adapter():
    """Create HTTP adapter."""
    return HttpxAdapter()


@pytest.fixture
def html_adapter():
    """Create HTML adapter."""
    return Bs4Adapter()


@pytest.fixture
def logger_adapter():
    """Create logger adapter."""
    return LoggerStructlogAdapter()


@pytest.fixture
def metrics_adapter():
    """Create metrics adapter."""
    return MetricsMemoryAdapter()


@pytest.fixture
def clock_adapter():
    """Create clock adapter."""
    return ClockAdapter()

