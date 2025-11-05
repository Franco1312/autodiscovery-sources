"""Use case: sync all sources."""

from typing import List, Optional

from ..interfaces.contracts_port import ContractsPort
from ..interfaces.logger_port import LoggerPort
from ..interfaces.metrics_port import MetricsPort
from .discover_source import DiscoverSourceUseCase


class SyncAllUseCase:
    """Use case for syncing all sources."""

    def __init__(
        self,
        discover_use_case: DiscoverSourceUseCase,
        contracts_port: ContractsPort,
        metrics_port: MetricsPort,
        logger: LoggerPort,
    ):
        """Initialize use case."""
        self.discover = discover_use_case
        self.contracts = contracts_port
        self.metrics = metrics_port
        self.logger = logger

    def execute(
        self,
        only_keys: Optional[List[str]] = None,
        fast: bool = False,
    ) -> dict:
        """Sync all sources.
        
        Args:
            only_keys: List of keys to sync (if None, sync all)
            fast: Fast mode
        
        Returns:
            Dictionary with results
        """
        self.logger.info("Starting sync all", only_keys=only_keys, fast=fast)
        
        # Load all contracts
        contracts = self.contracts.load_all()
        
        # Filter by only_keys if specified
        if only_keys:
            contracts = [c for c in contracts if c.get("key") in only_keys]
        
        results = {
            "total": len(contracts),
            "success": 0,
            "failed": 0,
            "errors": [],
        }
        
        for contract in contracts:
            key = contract.get("key")
            if not key:
                continue
            
            try:
                self.logger.info("Syncing source", key=key)
                entry = self.discover.execute(key, fast=fast)
                if entry:
                    results["success"] += 1
                    self.logger.info("Source synced", key=key, version=entry.version)
                else:
                    results["failed"] += 1
                    results["errors"].append({"key": key, "error": "Discovery returned None"})
                    self.logger.warning("Source sync failed", key=key)
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"key": key, "error": str(e)})
                self.logger.error("Source sync error", key=key, error=str(e))
        
        self.logger.info(
            "Sync all completed",
            total=results["total"],
            success=results["success"],
            failed=results["failed"],
        )
        
        return results

