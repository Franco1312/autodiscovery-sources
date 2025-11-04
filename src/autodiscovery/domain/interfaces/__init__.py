"""Domain interfaces (ports)."""

from typing import TYPE_CHECKING, Any

# New Clean Architecture ports
from autodiscovery.domain.interfaces.contracts_port import IContractsPort
from autodiscovery.domain.interfaces.discoverer_factory_port import IDiscovererFactoryPort
from autodiscovery.domain.interfaces.html_port import IHTMLPort
from autodiscovery.domain.interfaces.http_port import IHTTPPort
from autodiscovery.domain.interfaces.mirror_port import IMirrorPort
from autodiscovery.domain.interfaces.registry_port import IRegistryPort
from autodiscovery.domain.interfaces.source_discoverer_port import ISourceDiscovererPort

if TYPE_CHECKING:
    HTTPResponse = Any  # Protocol for HTTP response
    HTTPStreamResponse = Any  # Protocol for HTTP stream response
    HTMLSoup = Any  # Protocol for HTML soup

__all__ = [
    "IContractsPort",
    "IDiscovererFactoryPort",
    "IHTTPPort",
    "IHTMLPort",
    "IRegistryPort",
    "IMirrorPort",
    "ISourceDiscovererPort",
]
