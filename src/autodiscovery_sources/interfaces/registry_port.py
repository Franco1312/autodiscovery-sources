"""Port for registry operations."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ..domain.entities import RegistryEntry


class RegistryPort(ABC):
    """Port for registry load/save operations."""

    @abstractmethod
    def load(self) -> Dict[str, RegistryEntry]:
        """Load all registry entries.
        
        Returns:
            Dictionary mapping key -> RegistryEntry
        """
        pass

    @abstractmethod
    def upsert(self, entry: RegistryEntry) -> None:
        """Insert or update registry entry (atomic operation)."""
        pass

    @abstractmethod
    def get_by_key(self, key: str) -> Optional[RegistryEntry]:
        """Get latest entry for a key."""
        pass

    @abstractmethod
    def list_keys(self) -> List[str]:
        """List all keys in registry."""
        pass

