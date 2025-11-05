"""Tests for contracts loading."""

import pytest

from autodiscovery_sources.domain.errors import ContractError
from autodiscovery_sources.infrastructure.contracts_yaml_adapter import ContractsYamlAdapter


def test_load_all_contracts(contracts_adapter):
    """Test loading all contracts."""
    contracts = contracts_adapter.load_all()
    assert isinstance(contracts, list)
    assert len(contracts) > 0
    assert contracts[0]["key"] == "test_source"


def test_load_by_key(contracts_adapter):
    """Test loading contract by key."""
    contract = contracts_adapter.load_by_key("test_source")
    assert contract is not None
    assert contract["key"] == "test_source"
    assert "start_urls" in contract


def test_load_by_key_not_found(contracts_adapter):
    """Test loading non-existent key."""
    contract = contracts_adapter.load_by_key("nonexistent")
    assert contract is None


def test_load_invalid_yaml():
    """Test loading invalid YAML."""
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_path = Path(tmpdir) / "invalid.yml"
        invalid_path.write_text("invalid: yaml: [")
        
        with pytest.raises(ContractError):
            ContractsYamlAdapter(str(invalid_path)).load_all()

