"""Client API for external integration."""

import logging
from pathlib import Path

from autodiscovery.registry.models import SourceEntry
from autodiscovery.registry.registry import RegistryManager

logger = logging.getLogger(__name__)


class AutodiscoveryClient:
    """Client for accessing autodiscovery registry."""

    def __init__(self, registry_path: Path | None = None):
        self.registry_manager = RegistryManager(registry_path)

    def get_latest_url(self, key: str) -> str | None:
        """Get latest URL for a source key."""
        entry = self.registry_manager.get_entry(key)
        if entry:
            return entry.url
        return None

    def get_latest_mirror_path(self, key: str) -> str | None:
        """Get latest local mirror path for a source key."""
        entry = self.registry_manager.get_entry(key)
        if entry and entry.stored_path:
            return entry.stored_path
        return None

    def get_entry(self, key: str) -> SourceEntry | None:
        """Get full entry for a source key."""
        return self.registry_manager.get_entry(key)

    def list_keys(self) -> list[str]:
        """List all registered source keys."""
        return self.registry_manager.list_keys()

    def get_entry_dict(self, key: str) -> dict | None:
        """Get entry as dictionary (JSON-serializable)."""
        entry = self.get_entry(key)
        if entry:
            return entry.model_dump()
        return None


# Convenience functions
def get_latest_url(key: str) -> str | None:
    """Get latest URL for a source key."""
    client = AutodiscoveryClient()
    return client.get_latest_url(key)


def get_latest_mirror_path(key: str) -> str | None:
    """Get latest local mirror path for a source key."""
    client = AutodiscoveryClient()
    return client.get_latest_mirror_path(key)


def get_entry(key: str) -> SourceEntry | None:
    """Get full entry for a source key."""
    client = AutodiscoveryClient()
    return client.get_entry(key)
