"""Tests for ValidationService."""

from unittest.mock import Mock

import pytest

from autodiscovery.application.services.validation_service import ValidationService
from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.domain.interfaces import IFileValidator, IValidationRules


def test_validation_service_validate_ok():
    """Test validation with OK status."""
    mock_file_validator = Mock(spec=IFileValidator)
    mock_file_validator.validate_file.return_value = (True, "application/pdf", 100.0)

    mock_validation_rules = Mock(spec=IValidationRules)
    mock_validation_rules.get_expected_mime.return_value = "application/pdf"
    mock_validation_rules.get_expected_mime_any.return_value = None
    mock_validation_rules.get_min_size_kb.return_value = 50.0
    mock_validation_rules.validate_mime.return_value = True
    mock_validation_rules.validate_size.return_value = True
    mock_validation_rules.get_discontinuity_notes.return_value = None

    service = ValidationService(mock_file_validator, mock_validation_rules)
    discovered = DiscoveredFile(
        url="https://example.com/file.pdf",
        version="v2025-11-04",
        filename="file.pdf",
    )

    is_valid, status, notes = service.validate_discovered_file(discovered, "test_key")

    assert is_valid is True
    assert status == "ok"
    assert notes is None
    assert discovered.mime == "application/pdf"
    assert discovered.size_kb == 100.0


def test_validation_service_validate_suspect():
    """Test validation with suspect status."""
    mock_file_validator = Mock(spec=IFileValidator)
    mock_file_validator.validate_file.return_value = (True, "application/pdf", 100.0)

    mock_validation_rules = Mock(spec=IValidationRules)
    mock_validation_rules.get_expected_mime.return_value = "application/pdf"
    mock_validation_rules.get_expected_mime_any.return_value = None
    mock_validation_rules.get_min_size_kb.return_value = 50.0
    mock_validation_rules.validate_mime.return_value = False  # MIME doesn't match
    mock_validation_rules.validate_size.return_value = True
    mock_validation_rules.get_discontinuity_notes.return_value = "Some notes"

    service = ValidationService(mock_file_validator, mock_validation_rules)
    discovered = DiscoveredFile(
        url="https://example.com/file.pdf",
        version="v2025-11-04",
        filename="file.pdf",
    )

    is_valid, status, notes = service.validate_discovered_file(discovered, "test_key")

    assert is_valid is True
    assert status == "suspect"
    assert notes == "Some notes"


def test_validation_service_validate_broken():
    """Test validation with broken status."""
    mock_file_validator = Mock(spec=IFileValidator)
    mock_file_validator.validate_file.return_value = (False, None, None)

    mock_validation_rules = Mock(spec=IValidationRules)
    mock_validation_rules.get_expected_mime.return_value = "application/pdf"
    mock_validation_rules.get_expected_mime_any.return_value = None
    mock_validation_rules.get_min_size_kb.return_value = 50.0

    service = ValidationService(mock_file_validator, mock_validation_rules)
    discovered = DiscoveredFile(
        url="https://example.com/file.pdf",
        version="v2025-11-04",
        filename="file.pdf",
    )

    is_valid, status, notes = service.validate_discovered_file(discovered, "test_key")

    assert is_valid is False
    assert status == "broken"
    assert notes is None

