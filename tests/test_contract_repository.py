"""Tests for ContractRepository."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from autodiscovery.domain.interfaces import IContractRepository
from autodiscovery.infrastructure.contract_repository import ContractRepository


def test_contract_repository_load_contracts():
    """Test loading contracts from YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_path = Path(tmpdir) / "contracts.yml"
        contracts_data = [
            {"key": "test_key", "start_urls": ["https://example.com"]},
            {"key": "test_key2", "start_urls": ["https://example2.com"]},
        ]
        with open(contracts_path, "w") as f:
            yaml.dump(contracts_data, f)

        repository = ContractRepository(contracts_path)
        contracts = repository.load_contracts()

        assert len(contracts) == 2
        assert contracts[0]["key"] == "test_key"
        assert contracts[1]["key"] == "test_key2"


def test_contract_repository_get_contract():
    """Test getting a specific contract."""
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_path = Path(tmpdir) / "contracts.yml"
        contracts_data = [
            {"key": "test_key", "start_urls": ["https://example.com"]},
            {"key": "test_key2", "start_urls": ["https://example2.com"]},
        ]
        with open(contracts_path, "w") as f:
            yaml.dump(contracts_data, f)

        repository = ContractRepository(contracts_path)
        contract = repository.get_contract("test_key")

        assert contract is not None
        assert contract["key"] == "test_key"
        assert contract["start_urls"] == ["https://example.com"]


def test_contract_repository_get_contract_not_found():
    """Test getting a non-existent contract."""
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_path = Path(tmpdir) / "contracts.yml"
        contracts_data = [{"key": "test_key", "start_urls": ["https://example.com"]}]
        with open(contracts_path, "w") as f:
            yaml.dump(contracts_data, f)

        repository = ContractRepository(contracts_path)
        contract = repository.get_contract("nonexistent")

        assert contract is None


def test_contract_repository_get_all_keys():
    """Test getting all contract keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_path = Path(tmpdir) / "contracts.yml"
        contracts_data = [
            {"key": "test_key", "start_urls": ["https://example.com"]},
            {"key": "test_key2", "start_urls": ["https://example2.com"]},
        ]
        with open(contracts_path, "w") as f:
            yaml.dump(contracts_data, f)

        repository = ContractRepository(contracts_path)
        keys = repository.get_all_keys()

        assert len(keys) == 2
        assert "test_key" in keys
        assert "test_key2" in keys


def test_contract_repository_file_not_found():
    """Test handling missing contracts file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_path = Path(tmpdir) / "nonexistent.yml"
        repository = ContractRepository(contracts_path)
        contracts = repository.load_contracts()

        assert contracts == []


def test_contract_repository_caching():
    """Test that contracts are cached after first load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_path = Path(tmpdir) / "contracts.yml"
        contracts_data = [{"key": "test_key", "start_urls": ["https://example.com"]}]
        with open(contracts_path, "w") as f:
            yaml.dump(contracts_data, f)

        repository = ContractRepository(contracts_path)
        contracts1 = repository.load_contracts()

        # Modify file
        with open(contracts_path, "w") as f:
            yaml.dump([{"key": "new_key", "start_urls": ["https://new.com"]}], f)

        # Should still return cached version
        contracts2 = repository.load_contracts()
        assert contracts1 == contracts2
        assert len(contracts2) == 1
        assert contracts2[0]["key"] == "test_key"

