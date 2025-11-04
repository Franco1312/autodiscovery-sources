"""Registry repository implementation."""

import logging
from typing import Optional

from autodiscovery.domain.entities import SourceEntry
from autodiscovery.domain.interfaces import IRegistryRepository
from autodiscovery.registry.models import SourceEntry as RegistrySourceEntry
from autodiscovery.registry.registry import RegistryManager

logger = logging.getLogger(__name__)


class RegistryRepository(IRegistryRepository):
    """Implementation of registry repository."""

    def __init__(self, registry_manager: Optional[RegistryManager] = None):
        self.registry_manager = registry_manager or RegistryManager()

    def _to_domain_entry(self, entry: RegistrySourceEntry) -> SourceEntry:
        """Convert registry SourceEntry to domain SourceEntry."""
        return SourceEntry(
            url=entry.url,
            version=entry.version,
            mime=entry.mime,
            size_kb=entry.size_kb,
            sha256=entry.sha256,
            last_checked=entry.last_checked,
            status=entry.status,
            notes=entry.notes,
            stored_path=entry.stored_path,
            s3_key=entry.s3_key,
        )

    def _to_registry_entry(self, entry: SourceEntry) -> RegistrySourceEntry:
        """Convert domain SourceEntry to registry SourceEntry."""
        return RegistrySourceEntry(
            url=entry.url,
            version=entry.version,
            mime=entry.mime,
            size_kb=entry.size_kb,
            sha256=entry.sha256,
            last_checked=entry.last_checked,
            status=entry.status,
            notes=entry.notes,
            stored_path=entry.stored_path,
            s3_key=entry.s3_key,
        )

    def get_entry(self, key: str) -> Optional[SourceEntry]:
        """Get entry by key."""
        registry_entry = self.registry_manager.get_entry(key)
        if registry_entry:
            return self._to_domain_entry(registry_entry)
        return None

    def set_entry(self, key: str, entry: SourceEntry) -> None:
        """Set entry by key."""
        registry_entry = self._to_registry_entry(entry)
        self.registry_manager.set_entry(key, registry_entry)

    def has_entry(self, key: str) -> bool:
        """Check if entry exists."""
        return self.registry_manager.has_entry(key)

    def list_keys(self) -> list[str]:
        """List all keys in registry."""
        return self.registry_manager.list_keys()

