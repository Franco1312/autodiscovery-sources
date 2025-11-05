"""Domain-specific exceptions."""


class DiscoveryError(Exception):
    """Base exception for discovery errors."""

    pass


class ValidationError(DiscoveryError):
    """Exception for validation errors."""

    pass


class NetworkError(DiscoveryError):
    """Exception for network-related errors."""

    pass


class ContractError(DiscoveryError):
    """Exception for contract loading/parsing errors."""

    pass


class RegistryError(DiscoveryError):
    """Exception for registry operations."""

    pass


class MirrorError(DiscoveryError):
    """Exception for mirror operations."""

    pass

