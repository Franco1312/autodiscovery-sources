"""Registry port interface."""

from abc import ABC, abstractmethod

from autodiscovery.domain.entities import RegistryEntry


class IRegistryPort(ABC):
    """Port for registry operations (atomic, idempotent)."""

    @abstractmethod
    def get_entry(self, key: str) -> RegistryEntry | None:
        """Get registry entry by key."""

    @abstractmethod
    def set_entry(self, key: str, entry: RegistryEntry) -> None:
        """
        Set registry entry atomically.

        Args:
            key: Source key
            entry: Registry entry to save
        """

    @abstractmethod
    def has_entry(self, key: str) -> bool:
        """Check if entry exists."""

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all keys in registry."""

    @abstractmethod
    def get_all_entries(self) -> dict[str, RegistryEntry]:
        """Get all entries as dictionary."""
