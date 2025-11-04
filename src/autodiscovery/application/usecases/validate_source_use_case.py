"""Use case for validating an existing source entry."""

import logging
from dataclasses import dataclass
from datetime import datetime

from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.domain.entities import RegistryEntry
from autodiscovery.domain.interfaces.http_port import IHTTPPort
from autodiscovery.domain.interfaces.registry_port import IRegistryPort

logger = logging.getLogger(__name__)


@dataclass
class ValidateSourceResult:
    """Result of validate source use case."""

    key: str
    entry: RegistryEntry
    mime: str
    size_kb: float
    mime_valid: bool
    size_valid: bool
    status: str
    success: bool
    error: str | None = None


class ValidateSourceUseCase:
    """Use case for validating an existing source entry."""

    def __init__(
        self,
        registry_repository: IRegistryPort,
        file_validator,  # FileValidator service (no port needed)
        contract_service: ContractService,
        http_client: IHTTPPort,
        validation_rules,  # ValidationRules service (no port needed)
    ):
        self.registry_repository = registry_repository
        self.file_validator = file_validator
        self.contract_service = contract_service
        self.http_client = http_client
        self.validation_rules = validation_rules

    def execute(self, key: str) -> ValidateSourceResult:
        """
        Execute the validate source use case.

        Args:
            key: Source key to validate

        Returns:
            ValidateSourceResult with validation details
        """
        # Get entry from registry
        entry = self.registry_repository.get_entry(key)
        if not entry:
            return ValidateSourceResult(
                key=key,
                entry=None,
                mime="",
                size_kb=0.0,
                mime_valid=False,
                size_valid=False,
                status="",
                success=False,
                error=f"Entry not found for key: {key}",
            )

        # Get contract for validation rules
        contract = self.contract_service.get_contract(key)
        if not contract:
            return ValidateSourceResult(
                key=key,
                entry=entry,
                mime="",
                size_kb=0.0,
                mime_valid=False,
                size_valid=False,
                status="",
                success=False,
                error=f"Contract not found for key: {key}",
            )

        try:
            # Validate file accessibility
            expected_mime = self.validation_rules.get_expected_mime(key)
            expected_mime_any = self.validation_rules.get_expected_mime_any(key)

            is_valid, mime, size_kb = self.file_validator.validate_file(
                entry.url,
                key,
                expected_mime=expected_mime,
                expected_mime_any=expected_mime_any,
            )

            if not is_valid:
                # File is not accessible
                updated_entry = RegistryEntry(
                    key=key,
                    url=entry.url,
                    version=entry.version,
                    mime=entry.mime,
                    size_kb=entry.size_kb,
                    sha256=entry.sha256,
                    last_checked=datetime.now().isoformat() + "Z",
                    status="broken",
                    notes=entry.notes,
                    stored_path=entry.stored_path,
                    s3_key=entry.s3_key,
                )
                self.registry_repository.set_entry(key, updated_entry)
                return ValidateSourceResult(
                    key=key,
                    entry=updated_entry,
                    mime=mime or "",
                    size_kb=size_kb or 0.0,
                    mime_valid=False,
                    size_valid=False,
                    status="broken",
                    success=False,
                    error="File is not accessible",
                )

            # Validate MIME type and size
            mime_valid = self.validation_rules.validate_mime(key, mime or "")
            size_valid = self.validation_rules.validate_size(key, size_kb or 0)

            # Determine status
            status = "ok"
            if not mime_valid or not size_valid:
                status = "suspect"

            # Update entry
            updated_entry = RegistryEntry(
                key=key,
                url=entry.url,
                version=entry.version,
                mime=mime or "",
                size_kb=size_kb or 0.0,
                sha256=entry.sha256,
                last_checked=datetime.now().isoformat() + "Z",
                status=status,
                notes=entry.notes,
                stored_path=entry.stored_path,
                s3_key=entry.s3_key,
            )

            self.registry_repository.set_entry(key, updated_entry)

            return ValidateSourceResult(
                key=key,
                entry=updated_entry,
                mime=mime or "",
                size_kb=size_kb or 0.0,
                mime_valid=mime_valid,
                size_valid=size_valid,
                status=status,
                success=True,
            )

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            # Update entry with broken status
            broken_entry = RegistryEntry(
                key=key,
                url=entry.url,
                version=entry.version,
                mime=entry.mime,
                size_kb=entry.size_kb,
                sha256=entry.sha256,
                last_checked=datetime.now().isoformat() + "Z",
                status="broken",
                notes=entry.notes,
                stored_path=entry.stored_path,
                s3_key=entry.s3_key,
            )
            self.registry_repository.set_entry(key, broken_entry)
            return ValidateSourceResult(
                key=key,
                entry=broken_entry,
                mime="",
                size_kb=0.0,
                mime_valid=False,
                size_valid=False,
                status="broken",
                success=False,
                error=str(e),
            )
