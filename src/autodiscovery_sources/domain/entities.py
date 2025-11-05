"""Domain entities."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .value_objects import BytesSizeKB, MimeType, Sha256, Url


class DiscoveredFile(BaseModel):
    """Represents a discovered file candidate."""

    key: str = Field(..., description="Source key")
    url: Url = Field(..., description="File URL")
    filename: str = Field(..., description="Filename extracted from URL")
    mime: Optional[MimeType] = Field(None, description="MIME type if known")
    size_kb: Optional[BytesSizeKB] = Field(None, description="Size in KB if known")
    last_modified: Optional[datetime] = Field(None, description="Last-Modified header if available")
    score: int = Field(0, ge=0, le=100, description="Ranking score 0-100")
    notes: Optional[str] = Field(None, description="Additional notes")


class RegistryEntry(BaseModel):
    """Registry entry for a discovered and versioned source."""

    key: str = Field(..., description="Source key")
    url: Url = Field(..., description="File URL")
    version: str = Field(..., description="Version string (date or identifier)")
    filename: str = Field(..., description="Filename")
    mime: Optional[MimeType] = Field(None, description="MIME type")
    size_kb: Optional[BytesSizeKB] = Field(None, description="Size in KB")
    sha256: Sha256 = Field(..., description="SHA256 hash")
    last_checked: datetime = Field(..., description="Last check timestamp")
    status: Literal["ok", "suspect", "broken"] = Field("ok", description="Status")
    notes: Optional[str] = Field(None, description="Additional notes")
    s3_key: Optional[str] = Field(None, description="S3 key if mirrored to S3")


class Version(BaseModel):
    """Version value object."""

    value: str = Field(..., description="Version string")

    def __str__(self) -> str:
        return self.value


class SourceKey(BaseModel):
    """Source key value object."""

    value: str = Field(..., description="Source key string")

    @classmethod
    def validate(cls, v: str) -> "SourceKey":
        """Validate source key."""
        if not v or not v.strip():
            raise ValueError("Source key cannot be empty")
        return cls(value=v.strip())

    def __str__(self) -> str:
        return self.value

