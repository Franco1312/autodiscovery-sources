"""Tests for ContractService."""

from unittest.mock import Mock

import pytest

from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.domain.interfaces import IContractRepository


def test_contract_service_load_contracts():
    """Test ContractService loading contracts."""
    mock_repository = Mock(spec=IContractRepository)
    mock_repository.load_contracts.return_value = [
        {"key": "test_key", "start_urls": ["https://example.com"]}
    ]

    service = ContractService(mock_repository)
    contracts = service.load_contracts()

    assert len(contracts) == 1
    assert contracts[0]["key"] == "test_key"
    mock_repository.load_contracts.assert_called_once()


def test_contract_service_get_contract():
    """Test ContractService getting a specific contract."""
    mock_repository = Mock(spec=IContractRepository)
    mock_repository.get_contract.return_value = {
        "key": "test_key",
        "start_urls": ["https://example.com"],
    }

    service = ContractService(mock_repository)
    contract = service.get_contract("test_key")

    assert contract is not None
    assert contract["key"] == "test_key"
    mock_repository.get_contract.assert_called_once_with("test_key")


def test_contract_service_get_all_keys():
    """Test ContractService getting all keys."""
    mock_repository = Mock(spec=IContractRepository)
    mock_repository.get_all_keys.return_value = ["test_key", "test_key2"]

    service = ContractService(mock_repository)
    keys = service.get_all_keys()

    assert len(keys) == 2
    assert "test_key" in keys
    assert "test_key2" in keys
    mock_repository.get_all_keys.assert_called_once()

