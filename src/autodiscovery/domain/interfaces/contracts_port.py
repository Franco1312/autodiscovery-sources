"""Contracts port interface."""

from abc import ABC, abstractmethod
from typing import Any


class IContractsPort(ABC):
    """Port for reading contracts from YAML."""

    @abstractmethod
    def load_contracts(self) -> list[dict[str, Any]]:
        """Load all contracts from YAML file."""

    @abstractmethod
    def get_contract(self, key: str) -> dict[str, Any] | None:
        """Get contract for a specific key."""

    @abstractmethod
    def get_all_keys(self) -> list[str]:
        """Get all contract keys."""
