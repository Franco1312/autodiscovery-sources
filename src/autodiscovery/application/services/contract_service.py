"""Service for loading and managing contracts."""

from autodiscovery.domain.interfaces import IContractRepository


class ContractService:
    """Service for managing source discovery contracts."""

    def __init__(self, contract_repository: IContractRepository):
        self.contract_repository = contract_repository

    def load_contracts(self) -> list[dict]:
        """Load contracts from repository."""
        return self.contract_repository.load_contracts()

    def get_contract(self, key: str) -> dict | None:
        """Get contract for a specific key."""
        return self.contract_repository.get_contract(key)

    def get_all_keys(self) -> list[str]:
        """Get all contract keys."""
        return self.contract_repository.get_all_keys()
