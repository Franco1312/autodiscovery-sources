"""Value objects for domain layer."""

from pydantic import BaseModel, Field, field_validator


class MimeType(BaseModel):
    """MIME type value object."""

    value: str = Field(..., description="MIME type string")

    @field_validator("value")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        """Validate MIME type format."""
        if not v or not isinstance(v, str):
            raise ValueError("MIME type must be a non-empty string")
        # Remove charset parameters
        return v.split(";")[0].strip()

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value == other
        if isinstance(other, MimeType):
            return self.value == other.value
        return False


class Url(BaseModel):
    """URL value object with normalization."""

    value: str = Field(..., description="Normalized URL string")

    @field_validator("value")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate and normalize URL."""
        if not v or not isinstance(v, str):
            raise ValueError("URL must be a non-empty string")
        # Basic validation - full normalization done in infrastructure
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value == other
        if isinstance(other, Url):
            return self.value == other.value
        return False


class Sha256(BaseModel):
    """SHA256 hash value object."""

    value: str = Field(..., description="SHA256 hash string (64 hex chars)")

    @field_validator("value")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        """Validate SHA256 format."""
        if not v or not isinstance(v, str):
            raise ValueError("SHA256 must be a non-empty string")
        v = v.lower().strip()
        if len(v) != 64:
            raise ValueError("SHA256 must be exactly 64 hex characters")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("SHA256 must contain only hex characters")
        return v

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value == other.lower().strip()
        if isinstance(other, Sha256):
            return self.value == other.value
        return False


class BytesSizeKB(BaseModel):
    """File size in KB value object."""

    value: float = Field(..., ge=0, description="Size in kilobytes")

    @field_validator("value")
    @classmethod
    def validate_size(cls, v: float) -> float:
        """Validate size is non-negative."""
        if v < 0:
            raise ValueError("Size must be non-negative")
        return round(v, 2)

    def __str__(self) -> str:
        return f"{self.value:.2f} KB"

    def __float__(self) -> float:
        return self.value

    def __lt__(self, other: "BytesSizeKB") -> bool:
        return self.value < other.value

    def __le__(self, other: "BytesSizeKB") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "BytesSizeKB") -> bool:
        return self.value > other.value

    def __ge__(self, other: "BytesSizeKB") -> bool:
        return self.value >= other.value
