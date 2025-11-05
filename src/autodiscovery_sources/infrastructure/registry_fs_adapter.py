"""Filesystem adapter for registry operations."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from ..domain.entities import RegistryEntry
from ..domain.errors import RegistryError
from ..interfaces.registry_port import RegistryPort


class RegistryFsAdapter(RegistryPort):
    """Filesystem adapter for registry operations."""

    def __init__(self, registry_path: Optional[str] = None):
        """Initialize with path to registry JSON file."""
        if registry_path is None:
            # Default to registry/registry.json relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            registry_path = project_root / "registry" / "registry.json"
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize if doesn't exist
        if not self.registry_path.exists():
            self._write_registry({})

    def _read_registry(self) -> Dict:
        """Read registry from file."""
        try:
            if not self.registry_path.exists():
                return {}
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise RegistryError(f"Error parsing registry JSON: {e}")
        except Exception as e:
            raise RegistryError(f"Error reading registry: {e}")

    def _write_registry(self, data: Dict) -> None:
        """Write registry to file atomically."""
        try:
            # Atomic write: write to temp file then rename
            temp_path = self.registry_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            temp_path.replace(self.registry_path)
        except Exception as e:
            raise RegistryError(f"Error writing registry: {e}")

    def load(self) -> Dict[str, RegistryEntry]:
        """Load all registry entries."""
        data = self._read_registry()
        result = {}
        for key, entry_data in data.items():
            if key.startswith("_"):
                continue  # Skip metadata
            try:
                # Convert string values back to objects
                if isinstance(entry_data.get("url"), str):
                    from ..domain.value_objects import Url
                    entry_data["url"] = Url(value=entry_data["url"])
                if isinstance(entry_data.get("sha256"), str):
                    from ..domain.value_objects import Sha256
                    entry_data["sha256"] = Sha256(value=entry_data["sha256"])
                if isinstance(entry_data.get("mime"), str):
                    from ..domain.value_objects import MimeType
                    entry_data["mime"] = MimeType(value=entry_data["mime"])
                if isinstance(entry_data.get("size_kb"), (int, float)):
                    from ..domain.value_objects import BytesSizeKB
                    entry_data["size_kb"] = BytesSizeKB(value=entry_data["size_kb"])
                if isinstance(entry_data.get("last_checked"), str):
                    from datetime import datetime
                    entry_data["last_checked"] = datetime.fromisoformat(entry_data["last_checked"])
                result[key] = RegistryEntry(**entry_data)
            except Exception as e:
                # Skip invalid entries
                continue
        return result

    def upsert(self, entry: RegistryEntry) -> None:
        """Insert or update registry entry atomically."""
        data = self._read_registry()
        # Convert entry to dict
        entry_dict = entry.model_dump(mode="json")
        # Convert datetime and other objects to strings manually
        if isinstance(entry_dict.get("last_checked"), dict):
            entry_dict["last_checked"] = entry.last_checked.isoformat()
        if isinstance(entry_dict.get("url"), dict):
            entry_dict["url"] = entry.url.value
        if isinstance(entry_dict.get("sha256"), dict):
            entry_dict["sha256"] = entry.sha256.value
        if isinstance(entry_dict.get("mime"), dict):
            entry_dict["mime"] = entry.mime.value if entry.mime else None
        if isinstance(entry_dict.get("size_kb"), dict):
            entry_dict["size_kb"] = entry.size_kb.value if entry.size_kb else None
        data[entry.key] = entry_dict
        # Add metadata
        data["_metadata"] = {
            "updated_at": entry.last_checked.isoformat(),
            "version": "0.1.0",
        }
        self._write_registry(data)

    def get_by_key(self, key: str) -> Optional[RegistryEntry]:
        """Get latest entry for a key."""
        data = self._read_registry()
        entry_data = data.get(key)
        if not entry_data:
            return None
        try:
            # Convert string values back to objects
            if isinstance(entry_data.get("url"), str):
                from ..domain.value_objects import Url
                entry_data["url"] = Url(value=entry_data["url"])
            if isinstance(entry_data.get("sha256"), str):
                from ..domain.value_objects import Sha256
                entry_data["sha256"] = Sha256(value=entry_data["sha256"])
            if isinstance(entry_data.get("mime"), str):
                from ..domain.value_objects import MimeType
                entry_data["mime"] = MimeType(value=entry_data["mime"])
            if isinstance(entry_data.get("size_kb"), (int, float)):
                from ..domain.value_objects import BytesSizeKB
                entry_data["size_kb"] = BytesSizeKB(value=entry_data["size_kb"])
            if isinstance(entry_data.get("last_checked"), str):
                from datetime import datetime
                entry_data["last_checked"] = datetime.fromisoformat(entry_data["last_checked"])
            return RegistryEntry(**entry_data)
        except Exception:
            return None

    def list_keys(self) -> List[str]:
        """List all keys in registry."""
        data = self._read_registry()
        return [k for k in data.keys() if not k.startswith("_")]

