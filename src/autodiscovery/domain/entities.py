"""Domain entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


@dataclass
class DiscoveredFile:
    """Represents a discovered file."""

    url: str
    version: str
    filename: str
    mime: Optional[str] = None
    size_kb: Optional[float] = None
    sha256: Optional[str] = None


class SourceEntry(BaseModel):
    """Registry entry for a discovered source."""

    url: str
    version: str
    mime: str
    size_kb: float
    sha256: str
    last_checked: str = Field(default_factory=lambda: datetime.now().isoformat() + "Z")
    status: str = Field(default="ok")  # ok, suspect, broken
    notes: Optional[str] = None
    stored_path: Optional[str] = None  # Local filesystem path
    s3_key: Optional[str] = None  # S3 key if mirrored to S3

