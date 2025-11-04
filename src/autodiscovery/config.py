"""Configuration management from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Application configuration from environment variables."""

    # Registry
    REGISTRY_PATH: Path = Path(os.getenv("REGISTRY_PATH", "registry/sources_registry.json"))
    MIRRORS_PATH: Path = Path(os.getenv("MIRRORS_PATH", "mirrors"))

    # HTTP
    TIMEOUT_SECS: int = int(os.getenv("TIMEOUT_SECS", "10"))
    RETRIES: int = int(os.getenv("RETRIES", "3"))
    USER_AGENT: str = os.getenv("USER_AGENT", "RadarAutodiscovery/1.0")
    VERIFY_SSL: bool = os.getenv("VERIFY_SSL", "true").lower() == "true"

    # S3 (optional)
    MIRRORS_S3_BUCKET: str | None = os.getenv("MIRRORS_S3_BUCKET")
    AWS_REGION: str | None = os.getenv("AWS_REGION")
    AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")

    # Contracts
    CONTRACTS_PATH: Path = Path(os.getenv("CONTRACTS_PATH", "contracts/sources.yml"))

    @classmethod
    def is_s3_enabled(cls) -> bool:
        """Check if S3 mirroring is enabled."""
        return all(
            [
                cls.MIRRORS_S3_BUCKET,
                cls.AWS_REGION,
                cls.AWS_ACCESS_KEY_ID,
                cls.AWS_SECRET_ACCESS_KEY,
            ]
        )
