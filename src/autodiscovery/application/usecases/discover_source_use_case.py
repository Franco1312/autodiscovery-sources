"""Use case for discovering and registering a source."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from autodiscovery.application.factories.discoverer_factory import DiscovererFactory
from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.application.services.discovery_service import DiscoveryService
from autodiscovery.application.services.validation_service import ValidationService
from autodiscovery.domain.entities import DiscoveredFile, SourceEntry
from autodiscovery.domain.interfaces import (
    IFileValidator,
    IHTTPClient,
    IMirrorService,
    IRegistryRepository,
    IValidationRules,
)

logger = logging.getLogger(__name__)


@dataclass
class DiscoverSourceResult:
    """Result of discover source use case."""

    key: str
    discovered: DiscoveredFile
    entry: SourceEntry
    success: bool
    error: Optional[str] = None


class DiscoverSourceUseCase:
    """Use case for discovering and registering a source."""

    def __init__(
        self,
        contract_service: ContractService,
        registry_repository: IRegistryRepository,
        mirror_service: IMirrorService,
        file_validator: IFileValidator,
        http_client: IHTTPClient,
        validation_rules: IValidationRules,
    ):
        self.contract_service = contract_service
        self.registry_repository = registry_repository
        self.mirror_service = mirror_service
        self.file_validator = file_validator
        self.http_client = http_client
        self.validation_rules = validation_rules

    def execute(
        self,
        key: str,
        mirror: bool = True,
    ) -> DiscoverSourceResult:
        """
        Execute the discover source use case.

        Args:
            key: Source key to discover
            mirror: Whether to mirror the file

        Returns:
            DiscoverSourceResult with discovered file and entry
        """
        # Get contract
        contract = self.contract_service.get_contract(key)
        if not contract:
            return DiscoverSourceResult(
                key=key,
                discovered=None,
                entry=None,
                success=False,
                error=f"Contract not found for key: {key}",
            )

        # Create discoverer
        discoverer = DiscovererFactory.create(key, self.http_client)
        if not discoverer:
            return DiscoverSourceResult(
                key=key,
                discovered=None,
                entry=None,
                success=False,
                error=f"Discoverer not found for key: {key}",
            )

        # Discover file
        discovery_service = DiscoveryService(discoverer)
        start_urls = contract.get("start_urls", [])
        discovered = discovery_service.discover(start_urls)

        if not discovered:
            return DiscoverSourceResult(
                key=key,
                discovered=None,
                entry=None,
                success=False,
                error=f"No file discovered for key: {key}",
            )

        # Validate file
        validation_service = ValidationService(self.file_validator, self.validation_rules)
        is_valid, status, notes = validation_service.validate_discovered_file(
            discovered, key
        )

        if not is_valid:
            return DiscoverSourceResult(
                key=key,
                discovered=discovered,
                entry=None,
                success=False,
                error=f"File validation failed for key: {key}",
            )

        # Mirror file if requested
        stored_path = None
        s3_key = None
        sha256 = None

        if mirror and contract.get("mirror", True):
            try:
                stored_path_obj, sha256 = self.mirror_service.mirror_file(
                    discovered.url,
                    key,
                    discovered.version,
                    discovered.filename,
                )
                stored_path = str(stored_path_obj)
            except Exception as e:
                logger.error(f"Failed to mirror file for {key}: {e}")
                status = "broken"

        # Create entry
        entry = SourceEntry(
            url=discovered.url,
            version=discovered.version,
            mime=discovered.mime or "",
            size_kb=discovered.size_kb or 0,
            sha256=sha256 or "",
            status=status,
            notes=notes,
            stored_path=stored_path,
            s3_key=s3_key,
        )

        # Save to registry
        self.registry_repository.set_entry(key, entry)

        return DiscoverSourceResult(
            key=key,
            discovered=discovered,
            entry=entry,
            success=True,
        )

