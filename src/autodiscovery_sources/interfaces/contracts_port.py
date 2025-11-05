"""Port for loading source contracts."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class ContractsPort(ABC):
    """Port for loading and parsing source contracts."""

    @abstractmethod
    def load_all(self) -> List[Dict]:
        """Load all source contracts."""
        pass

    @abstractmethod
    def load_by_key(self, key: str) -> Optional[Dict]:
        """Load contract for a specific source key."""
        pass

