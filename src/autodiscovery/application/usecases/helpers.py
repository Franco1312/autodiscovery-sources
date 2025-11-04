"""Shared helpers for use cases to reduce duplication and complexity."""

from datetime import datetime

from autodiscovery.domain.entities import DiscoveredFile, RegistryEntry


class RegistryEntryBuilder:
    """Builder for RegistryEntry to reduce duplication and complexity."""

    def __init__(self, key: str, url: str, version: str):
        """Initialize builder with required fields."""
        self.key = key
        self.url = url
        self.version = version
        self.mime = ""
        self.size_kb = 0.0
        self.sha256 = ""
        self.status = "ok"
        self.notes: str | None = None
        self.stored_path: str | None = None
        self.s3_key: str | None = None
        self.last_checked: str | None = None
        self.related: list[str] | None = None

    def from_discovered_file(self, discovered: DiscoveredFile) -> "RegistryEntryBuilder":
        """Set fields from DiscoveredFile."""
        self.mime = discovered.mime or ""
        self.size_kb = discovered.size_kb or 0.0
        return self

    def from_existing_entry(self, entry: RegistryEntry) -> "RegistryEntryBuilder":
        """Copy fields from existing entry."""
        self.mime = entry.mime
        self.size_kb = entry.size_kb
        self.sha256 = entry.sha256
        self.notes = entry.notes
        self.stored_path = entry.stored_path
        self.s3_key = entry.s3_key
        return self

    def with_mime(self, mime: str) -> "RegistryEntryBuilder":
        """Set MIME type."""
        self.mime = mime or ""
        return self

    def with_size(self, size_kb: float) -> "RegistryEntryBuilder":
        """Set size in KB."""
        self.size_kb = size_kb or 0.0
        return self

    def with_sha256(self, sha256: str | None) -> "RegistryEntryBuilder":
        """Set SHA256 hash."""
        self.sha256 = sha256 or ""
        return self

    def with_status(self, status: str) -> "RegistryEntryBuilder":
        """Set status."""
        self.status = status
        return self

    def with_notes(self, notes: str | None) -> "RegistryEntryBuilder":
        """Set notes."""
        self.notes = notes
        return self

    def with_stored_path(self, stored_path: str | None) -> "RegistryEntryBuilder":
        """Set stored path."""
        self.stored_path = stored_path
        return self

    def with_s3_key(self, s3_key: str | None) -> "RegistryEntryBuilder":
        """Set S3 key."""
        self.s3_key = s3_key
        return self

    def with_last_checked_now(self) -> "RegistryEntryBuilder":
        """Set last_checked to current time."""
        self.last_checked = datetime.now().isoformat() + "Z"
        return self

    def build(self) -> RegistryEntry:
        """Build RegistryEntry from builder."""
        # Use default_factory if last_checked is None
        from datetime import datetime

        last_checked = (
            self.last_checked if self.last_checked is not None else datetime.now().isoformat() + "Z"
        )

        return RegistryEntry(
            key=self.key,
            url=self.url,
            version=self.version,
            mime=self.mime,
            size_kb=self.size_kb,
            sha256=self.sha256,
            status=self.status,
            notes=self.notes,
            stored_path=self.stored_path,
            s3_key=self.s3_key,
            last_checked=last_checked,
            related=self.related,
        )


def create_error_result(
    key: str,
    error_msg: str,
    discovered: DiscoveredFile | None = None,
    entry: RegistryEntry | None = None,
) -> tuple[DiscoveredFile | None, RegistryEntry | None, bool, str]:
    """Create standardized error result tuple."""
    return (discovered, entry, False, error_msg)
