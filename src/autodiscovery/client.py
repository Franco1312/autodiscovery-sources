"""Client API for external integration."""

import json
import logging
from pathlib import Path
from typing import Optional

from autodiscovery.config import Config
from autodiscovery.registry.models import SourceEntry
from autodiscovery.registry.registry import RegistryManager

logger = logging.getLogger(__name__)


class AutodiscoveryClient:
    """Client for accessing autodiscovery registry."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_manager = RegistryManager(registry_path)

    def get_latest_url(self, key: str) -> Optional[str]:
        """Get latest URL for a source key."""
        entry = self.registry_manager.get_entry(key)
        if entry:
            return entry.url
        return None

    def get_latest_mirror_path(self, key: str) -> Optional[str]:
        """Get latest local mirror path for a source key."""
        entry = self.registry_manager.get_entry(key)
        if entry and entry.stored_path:
            return entry.stored_path
        return None

    def get_entry(self, key: str) -> Optional[SourceEntry]:
        """Get full entry for a source key."""
        return self.registry_manager.get_entry(key)

    def list_keys(self) -> list[str]:
        """List all registered source keys."""
        return self.registry_manager.list_keys()

    def get_entry_dict(self, key: str) -> Optional[dict]:
        """Get entry as dictionary (JSON-serializable)."""
        entry = self.get_entry(key)
        if entry:
            return entry.model_dump()
        return None


# Convenience functions
def get_latest_url(key: str) -> Optional[str]:
    """Get latest URL for a source key."""
    client = AutodiscoveryClient()
    return client.get_latest_url(key)


def get_latest_mirror_path(key: str) -> Optional[str]:
    """Get latest local mirror path for a source key."""
    client = AutodiscoveryClient()
    return client.get_latest_mirror_path(key)


def get_entry(key: str) -> Optional[SourceEntry]:
    """Get full entry for a source key."""
    client = AutodiscoveryClient()
    return client.get_entry(key)

