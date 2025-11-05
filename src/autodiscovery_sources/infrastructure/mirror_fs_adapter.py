"""Filesystem adapter for mirror operations."""

import os
from pathlib import Path
from typing import Optional

from ..domain.errors import MirrorError
from ..interfaces.mirror_port import MirrorPort


class MirrorFsAdapter(MirrorPort):
    """Filesystem adapter for mirroring files."""

    def __init__(self, mirrors_path: Optional[str] = None):
        """Initialize with path to mirrors directory."""
        if mirrors_path is None:
            # Default to mirrors/ relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            mirrors_path = project_root / "mirrors"
        self.mirrors_path = Path(mirrors_path)
        self.mirrors_path.mkdir(parents=True, exist_ok=True)

    def write(self, key: str, version: str, filename: str, content: bytes) -> Optional[str]:
        """Write file to filesystem mirror."""
        try:
            # Create directory structure: mirrors/key/version/
            target_dir = self.mirrors_path / key / version
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Write file
            target_file = target_dir / filename
            with open(target_file, "wb") as f:
                f.write(content)
            
            # Return relative path
            return str(target_file.relative_to(self.mirrors_path))
        except Exception as e:
            raise MirrorError(f"Error writing file to mirror: {e}")

