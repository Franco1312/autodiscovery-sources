"""Value objects for domain entities."""

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class Url(BaseModel):
    """URL value object with validation."""

    value: str = Field(..., description="URL string")

    @field_validator("value")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Basic URL validation."""
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: {v}")
        return v.strip()

    def __str__(self) -> str:
        return self.value


class Sha256(BaseModel):
    """SHA256 hash value object."""

    value: str = Field(..., description="SHA256 hash string")

    @field_validator("value")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        """Validate SHA256 format (64 hex chars)."""
        if not v or len(v) != 64:
            raise ValueError(f"Invalid SHA256 format: {v}")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError(f"Invalid SHA256 format: {v}")
        return v.lower()

    def __str__(self) -> str:
        return self.value


class BytesSizeKB(BaseModel):
    """Size in KB value object."""

    value: float = Field(..., ge=0, description="Size in kilobytes")

    @classmethod
    def from_bytes(cls, bytes_size: int) -> "BytesSizeKB":
        """Create from bytes."""
        return cls(value=bytes_size / 1024.0)

    def __str__(self) -> str:
        return f"{self.value:.2f}KB"


class MimeType(BaseModel):
    """MIME type value object."""

    value: str = Field(..., description="MIME type string")

    @field_validator("value")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        """Basic MIME validation."""
        if not v or not v.strip():
            raise ValueError("MIME type cannot be empty")
        # Basic format: type/subtype
        parts = v.strip().split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid MIME format: {v}")
        return v.strip().lower()

    def __str__(self) -> str:
        return self.value

