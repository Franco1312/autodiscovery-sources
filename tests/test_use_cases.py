"""Tests for use cases."""

from unittest.mock import Mock, patch

import pytest

from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.application.usecases.discover_source_use_case import (
    DiscoverSourceResult,
    DiscoverSourceUseCase,
)
from autodiscovery.application.usecases.validate_source_use_case import (
    ValidateSourceResult,
    ValidateSourceUseCase,
)
from autodiscovery.domain.entities import DiscoveredFile, SourceEntry
from autodiscovery.domain.interfaces import (
    IContractRepository,
    IFileValidator,
    IHTTPClient,
    IMirrorService,
    IRegistryRepository,
    ISourceDiscoverer,
    IValidationRules,
)
from autodiscovery.infrastructure.discoverer_factory import DiscovererFactory


@pytest.fixture
def mock_contract_repository():
    """Create mock contract repository."""
    mock = Mock(spec=IContractRepository)
    mock.get_contract.return_value = {
        "key": "test_key",
        "start_urls": ["https://example.com"],
        "mirror": True,
    }
    return mock


@pytest.fixture
def mock_registry_repository():
    """Create mock registry repository."""
    mock = Mock(spec=IRegistryRepository)
    mock.get_entry.return_value = None
    return mock


@pytest.fixture
def mock_discoverer():
    """Create mock discoverer."""
    mock = Mock(spec=ISourceDiscoverer)
    mock.discover.return_value = DiscoveredFile(
        url="https://example.com/file.xls",
        version="v2025-11-04",
        filename="file.xls",
    )
    return mock


@pytest.fixture
def mock_file_validator():
    """Create mock file validator."""
    mock = Mock(spec=IFileValidator)
    mock.validate_file.return_value = (True, "application/pdf", 100.0)
    return mock


@pytest.fixture
def mock_validation_rules():
    """Create mock validation rules."""
    mock = Mock(spec=IValidationRules)
    mock.get_expected_mime.return_value = "application/pdf"
    mock.get_expected_mime_any.return_value = None
    mock.get_min_size_kb.return_value = 50.0
    mock.validate_mime.return_value = True
    mock.validate_size.return_value = True
    mock.get_discontinuity_notes.return_value = None
    return mock


@pytest.fixture
def mock_mirror_service():
    """Create mock mirror service."""
    mock = Mock(spec=IMirrorService)
    from pathlib import Path

    mock.mirror_file.return_value = (Path("/tmp/file.xls"), "sha256hash")
    return mock


def test_discover_source_use_case_success(
    mock_contract_repository,
    mock_registry_repository,
    mock_discoverer,
    mock_file_validator,
    mock_validation_rules,
    mock_mirror_service,
):
    """Test successful source discovery."""
    mock_http_client = Mock(spec=IHTTPClient)

    # Mock discoverer factory
    with patch.object(DiscovererFactory, "create", return_value=mock_discoverer):
        use_case = DiscoverSourceUseCase(
            contract_service=ContractService(mock_contract_repository),
            registry_repository=mock_registry_repository,
            mirror_service=mock_mirror_service,
            file_validator=mock_file_validator,
            http_client=mock_http_client,
            validation_rules=mock_validation_rules,
        )

        result = use_case.execute("test_key", mirror=True)

        assert isinstance(result, DiscoverSourceResult)
        assert result.success is True
        assert result.key == "test_key"
        assert result.discovered is not None
        assert result.entry is not None
        mock_registry_repository.set_entry.assert_called_once()


def test_discover_source_use_case_contract_not_found(
    mock_registry_repository,
    mock_file_validator,
    mock_validation_rules,
    mock_mirror_service,
):
    """Test discovery when contract is not found."""
    mock_contract_repository = Mock(spec=IContractRepository)
    mock_contract_repository.get_contract.return_value = None
    mock_http_client = Mock(spec=IHTTPClient)

    use_case = DiscoverSourceUseCase(
        contract_service=ContractService(mock_contract_repository),
        registry_repository=mock_registry_repository,
        mirror_service=mock_mirror_service,
        file_validator=mock_file_validator,
        http_client=mock_http_client,
        validation_rules=mock_validation_rules,
    )

    result = use_case.execute("test_key")

    assert isinstance(result, DiscoverSourceResult)
    assert result.success is False
    assert "Contract not found" in result.error


def test_discover_source_use_case_discoverer_not_found(
    mock_contract_repository,
    mock_registry_repository,
    mock_file_validator,
    mock_validation_rules,
    mock_mirror_service,
):
    """Test discovery when discoverer is not found."""
    mock_http_client = Mock(spec=IHTTPClient)

    # Mock discoverer factory to return None
    with patch.object(DiscovererFactory, "create", return_value=None):
        use_case = DiscoverSourceUseCase(
            contract_service=ContractService(mock_contract_repository),
            registry_repository=mock_registry_repository,
            mirror_service=mock_mirror_service,
            file_validator=mock_file_validator,
            http_client=mock_http_client,
            validation_rules=mock_validation_rules,
        )

        result = use_case.execute("test_key")

        assert isinstance(result, DiscoverSourceResult)
        assert result.success is False
        assert "Discoverer not found" in result.error


def test_validate_source_use_case_success(
    mock_contract_repository,
    mock_registry_repository,
    mock_file_validator,
    mock_validation_rules,
):
    """Test successful source validation."""
    # Set up existing entry
    existing_entry = SourceEntry(
        url="https://example.com/file.xls",
        version="v2025-11-04",
        mime="application/pdf",
        size_kb=100.0,
        sha256="abc123",
        status="ok",
    )
    mock_registry_repository.get_entry.return_value = existing_entry

    mock_http_client = Mock(spec=IHTTPClient)

    use_case = ValidateSourceUseCase(
        registry_repository=mock_registry_repository,
        file_validator=mock_file_validator,
        contract_service=ContractService(mock_contract_repository),
        http_client=mock_http_client,
        validation_rules=mock_validation_rules,
    )

    result = use_case.execute("test_key")

    assert isinstance(result, ValidateSourceResult)
    assert result.success is True
    assert result.key == "test_key"
    assert result.mime_valid is True
    assert result.size_valid is True
    assert result.status == "ok"
    mock_registry_repository.set_entry.assert_called_once()


def test_validate_source_use_case_entry_not_found(
    mock_contract_repository,
    mock_registry_repository,
    mock_file_validator,
    mock_validation_rules,
):
    """Test validation when entry is not found."""
    mock_registry_repository.get_entry.return_value = None
    mock_http_client = Mock(spec=IHTTPClient)

    use_case = ValidateSourceUseCase(
        registry_repository=mock_registry_repository,
        file_validator=mock_file_validator,
        contract_service=ContractService(mock_contract_repository),
        http_client=mock_http_client,
        validation_rules=mock_validation_rules,
    )

    result = use_case.execute("test_key")

    assert isinstance(result, ValidateSourceResult)
    assert result.success is False
    assert "Entry not found" in result.error


def test_validate_source_use_case_file_not_accessible(
    mock_contract_repository,
    mock_registry_repository,
    mock_validation_rules,
):
    """Test validation when file is not accessible."""
    # Set up existing entry
    existing_entry = SourceEntry(
        url="https://example.com/file.xls",
        version="v2025-11-04",
        mime="application/pdf",
        size_kb=100.0,
        sha256="abc123",
        status="ok",
    )
    mock_registry_repository.get_entry.return_value = existing_entry

    # Mock file validator to return not accessible
    mock_file_validator = Mock(spec=IFileValidator)
    mock_file_validator.validate_file.return_value = (False, None, None)

    mock_http_client = Mock(spec=IHTTPClient)

    use_case = ValidateSourceUseCase(
        registry_repository=mock_registry_repository,
        file_validator=mock_file_validator,
        contract_service=ContractService(mock_contract_repository),
        http_client=mock_http_client,
        validation_rules=mock_validation_rules,
    )

    result = use_case.execute("test_key")

    assert isinstance(result, ValidateSourceResult)
    assert result.success is False
    assert result.status == "broken"
    mock_registry_repository.set_entry.assert_called_once()
