"""YAML adapter for loading source contracts."""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from ..domain.errors import ContractError
from ..interfaces.contracts_port import ContractsPort


class ContractsYamlAdapter(ContractsPort):
    """YAML adapter for loading source contracts."""

    def __init__(self, contracts_path: Optional[str] = None):
        """Initialize with path to contracts YAML file."""
        if contracts_path is None:
            # Default to contracts/sources.yml relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            contracts_path = project_root / "contracts" / "sources.yml"
        self.contracts_path = Path(contracts_path)
        if not self.contracts_path.exists():
            raise ContractError(f"Contracts file not found: {self.contracts_path}")

    def load_all(self) -> List[Dict]:
        """Load all source contracts from YAML."""
        try:
            with open(self.contracts_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, list):
                    raise ContractError(f"Expected list in {self.contracts_path}")
                return data
        except yaml.YAMLError as e:
            raise ContractError(f"Error parsing YAML: {e}")
        except Exception as e:
            raise ContractError(f"Error loading contracts: {e}")

    def load_by_key(self, key: str) -> Optional[Dict]:
        """Load contract for a specific source key."""
        contracts = self.load_all()
        for contract in contracts:
            if contract.get("key") == key:
                return contract
        return None

