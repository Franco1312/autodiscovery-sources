"""Use case for discovering and registering a source."""

import logging
from dataclasses import dataclass

from autodiscovery.application.services.contract_service import ContractService
from autodiscovery.application.services.discovery_service import DiscoveryService
from autodiscovery.application.services.validation_service import ValidationService
from autodiscovery.application.usecases.helpers import RegistryEntryBuilder
from autodiscovery.domain.entities import DiscoveredFile, RegistryEntry
from autodiscovery.domain.interfaces.discoverer_factory_port import IDiscovererFactoryPort
from autodiscovery.domain.interfaces.http_port import IHTTPPort
from autodiscovery.domain.interfaces.mirror_port import IMirrorPort
from autodiscovery.domain.interfaces.registry_port import IRegistryPort

logger = logging.getLogger(__name__)


@dataclass
class DiscoverSourceResult:
    """Result of discover source use case."""

    key: str
    discovered: DiscoveredFile | None
    entry: RegistryEntry | None
    success: bool
    error: str | None = None


class DiscoverSourceUseCase:
    """Use case for discovering and registering a source."""

    def __init__(
        self,
        contract_service: ContractService,
        registry_repository: IRegistryPort,
        mirror_service: IMirrorPort,
        file_validator,  # FileValidator service (no port needed)
        http_client: IHTTPPort,
        validation_rules,  # ValidationRules service (no port needed)
        discoverer_factory: IDiscovererFactoryPort,
    ):
        self.contract_service = contract_service
        self.registry_repository = registry_repository
        self.mirror_service = mirror_service
        self.file_validator = file_validator
        self.http_client = http_client
        self.validation_rules = validation_rules
        self.discoverer_factory = discoverer_factory

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
        discoverer = self.discoverer_factory.create(key, self.http_client)
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
        is_valid, status, notes = validation_service.validate_discovered_file(discovered, key)

        if not is_valid:
            return DiscoverSourceResult(
                key=key,
                discovered=discovered,
                entry=None,
                success=False,
                error=f"File validation failed for key: {key}",
            )

        # Mirror file if requested
        mirror_result = self._mirror_file_if_needed(
            discovered, key, mirror and contract.get("mirror", True)
        )

        # Create entry using builder pattern
        entry = (
            RegistryEntryBuilder(key, discovered.url, discovered.version)
            .from_discovered_file(discovered)
            .with_status(status)
            .with_notes(notes)
            .with_sha256(mirror_result["sha256"])
            .with_stored_path(mirror_result["stored_path"])
            .with_s3_key(mirror_result["s3_key"])
            .build()
        )

        # Save to registry
        self.registry_repository.set_entry(key, entry)

        return DiscoverSourceResult(
            key=key,
            discovered=discovered,
            entry=entry,
            success=True,
        )

    def _mirror_file_if_needed(
        self, discovered: DiscoveredFile, key: str, should_mirror: bool
    ) -> dict[str, str | None]:
        """Mirror file if requested, return mirror result."""
        if not should_mirror:
            return {"stored_path": None, "s3_key": None, "sha256": None}

        try:
            stored_path_obj, sha256 = self.mirror_service.mirror_file(
                discovered.url,
                key,
                discovered.version,
                discovered.filename,
            )
            return {
                "stored_path": str(stored_path_obj),
                "s3_key": None,  # S3 is handled separately if needed
                "sha256": sha256,
            }
        except Exception as e:
            logger.error(f"Failed to mirror file for {key}: {e}")
            return {"stored_path": None, "s3_key": None, "sha256": None}
