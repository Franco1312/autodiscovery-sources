"""Domain entities."""

from datetime import datetime

from pydantic import BaseModel, Field

# Value objects imported but not used directly in entities (kept for future use)
# from autodiscovery.domain.value_objects import BytesSizeKB, MimeType, Sha256, Url


class SourceKey(BaseModel):
    """Source key value object."""

    value: str = Field(..., description="Source key identifier")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value == other
        if isinstance(other, SourceKey):
            return self.value == other.value
        return False


class Version(BaseModel):
    """Version value object."""

    value: str = Field(..., description="Version string (e.g., v2025-11-04)")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value == other
        if isinstance(other, Version):
            return self.value == other.value
        return False


class DiscoveredFile(BaseModel):
    """Represents a discovered file."""

    url: str  # Keep as str for simplicity, will be normalized by infrastructure
    version: str
    filename: str
    mime: str | None = None
    size_kb: float | None = None
    sha256: str | None = None
    last_modified: str | None = None  # Last-Modified header value
    regex_groups: list[str] | None = None  # Captured regex groups for versioning


class RegistryEntry(BaseModel):
    """Registry entry for a discovered source."""

    key: str
    url: str
    version: str
    mime: str
    size_kb: float
    sha256: str
    last_checked: str = Field(default_factory=lambda: datetime.now().isoformat() + "Z")
    status: str = Field(default="ok")  # ok, suspect, broken
    notes: str | None = None
    stored_path: str | None = None  # Local filesystem path
    s3_key: str | None = None  # S3 key if mirrored to S3
    related: list[str] | None = None  # Related source keys (e.g., ["bcra_rem_pdf"])

    model_config = {
        "json_encoders": {
            # Custom encoders if needed
        }
    }
