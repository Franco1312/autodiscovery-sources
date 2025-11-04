"""Domain layer: entities, value objects, and interfaces."""

from autodiscovery.domain.entities import DiscoveredFile, RegistryEntry
from autodiscovery.domain.interfaces import (
    IContractsPort,
    IHTMLPort,
    IHTTPPort,
    IMirrorPort,
    IRegistryPort,
    ISourceDiscovererPort,
)

__all__ = [
    "DiscoveredFile",
    "RegistryEntry",
    "IContractsPort",
    "IHTTPPort",
    "IHTMLPort",
    "IRegistryPort",
    "IMirrorPort",
    "ISourceDiscovererPort",
]
