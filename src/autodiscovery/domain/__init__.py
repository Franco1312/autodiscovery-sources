"""Domain layer: entities, value objects, and interfaces."""

from autodiscovery.domain.entities import DiscoveredFile, SourceEntry
from autodiscovery.domain.interfaces import (
    IContractRepository,
    IFileValidator,
    IHTMLParser,
    IHTTPClient,
    IMirrorService,
    IRegistryRepository,
    ISourceDiscoverer,
    IValidationRules,
)

__all__ = [
    "DiscoveredFile",
    "SourceEntry",
    "ISourceDiscoverer",
    "IRegistryRepository",
    "IMirrorService",
    "IFileValidator",
    "IHTTPClient",
    "IHTMLParser",
    "IValidationRules",
    "IContractRepository",
]

