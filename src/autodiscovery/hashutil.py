"""Hash utilities for file integrity."""

import hashlib
from pathlib import Path
from typing import BinaryIO


def sha256_bytes(data: bytes) -> str:
    """Calculate SHA256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def sha256_stream(stream: BinaryIO, chunk_size: int = 4096) -> str:
    """Calculate SHA256 hash of a stream."""
    sha256 = hashlib.sha256()
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        sha256.update(chunk)
    return sha256.hexdigest()

