"""Service for loading and managing contracts."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from autodiscovery.config import Config

logger = logging.getLogger(__name__)


class ContractService:
    """Service for managing source discovery contracts."""

    def __init__(self, contracts_path: Optional[Path] = None):
        self.contracts_path = contracts_path or Config.CONTRACTS_PATH
        self._contracts: Optional[List[Dict]] = None

    def load_contracts(self) -> List[Dict]:
        """Load contracts from YAML file."""
        if self._contracts is not None:
            return self._contracts

        if not self.contracts_path.exists():
            logger.error(f"Contracts file not found: {self.contracts_path}")
            self._contracts = []
            return self._contracts

        try:
            with open(self.contracts_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._contracts = data or []
            logger.debug(f"Loaded {len(self._contracts)} contracts")
            return self._contracts
        except Exception as e:
            logger.error(f"Failed to load contracts: {e}")
            self._contracts = []
            return self._contracts

    def get_contract(self, key: str) -> Optional[Dict]:
        """Get contract for a specific key."""
        contracts = self.load_contracts()
        for contract in contracts:
            if contract.get("key") == key:
                return contract
        return None

    def get_all_keys(self) -> List[str]:
        """Get all contract keys."""
        contracts = self.load_contracts()
        return [c.get("key") for c in contracts if c.get("key")]

