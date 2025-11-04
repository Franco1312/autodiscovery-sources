"""Domain entities."""

from datetime import datetime

from pydantic import BaseModel, Field


class DiscoveredFile(BaseModel):
    """Represents a discovered file."""

    url: str
    version: str
    filename: str
    mime: str | None = None
    size_kb: float | None = None
    sha256: str | None = None


class SourceEntry(BaseModel):
    """Registry entry for a discovered source."""

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
