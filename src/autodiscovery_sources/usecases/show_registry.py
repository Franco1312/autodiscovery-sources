"""Use case: show registry entries."""

from datetime import datetime
from typing import Dict, List, Optional

from ..domain.entities import RegistryEntry
from ..interfaces.clock_port import ClockPort
from ..interfaces.logger_port import LoggerPort
from ..interfaces.registry_port import RegistryPort


class ShowRegistryUseCase:
    """Use case for showing registry entries."""

    def __init__(
        self,
        registry_port: RegistryPort,
        clock_port: ClockPort,
        logger: LoggerPort,
    ):
        """Initialize use case."""
        self.registry = registry_port
        self.clock = clock_port
        self.logger = logger

    def execute(self, key: Optional[str] = None) -> List[RegistryEntry]:
        """Show registry entries.
        
        Args:
            key: Optional key to filter by
        
        Returns:
            List of registry entries
        """
        if key:
            entry = self.registry.get_by_key(key)
            if entry:
                return [entry]
            return []
        else:
            # Return all entries
            entries_dict = self.registry.load()
            return list(entries_dict.values())

    def format_entry(self, entry: RegistryEntry) -> str:
        """Format registry entry for display."""
        now = self.clock.now()
        age_hours = (now - entry.last_checked).total_seconds() / 3600
        
        lines = [
            f"Key: {entry.key}",
            f"  URL: {entry.url.value}",
            f"  Version: {entry.version}",
            f"  Filename: {entry.filename}",
            f"  Status: {entry.status}",
            f"  Age: {age_hours:.1f} hours",
        ]
        
        if entry.mime:
            lines.append(f"  MIME: {entry.mime.value}")
        
        if entry.size_kb:
            lines.append(f"  Size: {entry.size_kb.value:.2f} KB")
        
        if entry.sha256:
            lines.append(f"  SHA256: {entry.sha256.value[:16]}...")
        
        if entry.notes:
            lines.append(f"  Notes: {entry.notes}")
        
        if entry.s3_key:
            lines.append(f"  S3 Key: {entry.s3_key}")
        
        return "\n".join(lines)

