"""Filesystem utilities with safe operations."""

import contextlib
import os
import tempfile
from pathlib import Path
from typing import BinaryIO


def safe_mkdirs(path: Path) -> None:
    """Create directory and parents safely."""
    path.mkdir(parents=True, exist_ok=True)


def atomic_write(file_path: Path, content: bytes) -> None:
    """Write file atomically using temp file + rename."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # Use temp file in same directory
    temp_fd, temp_path = tempfile.mkstemp(dir=file_path.parent, suffix=".tmp")
    try:
        with os.fdopen(temp_fd, "wb") as f:
            f.write(content)
        os.replace(temp_path, file_path)
    except Exception:
        # Clean up temp file on error
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise


def atomic_write_stream(file_path: Path, source: BinaryIO, chunk_size: int = 8192) -> None:
    """Write file atomically from a stream."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=file_path.parent, suffix=".tmp")
    try:
        with os.fdopen(temp_fd, "wb") as f:
            while True:
                chunk = source.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
        os.replace(temp_path, file_path)
    except Exception:
        # Clean up temp file on error
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise
