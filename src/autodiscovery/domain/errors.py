"""Domain errors."""


class DiscoveryError(Exception):
    """Base error for discovery operations."""


class ValidationError(Exception):
    """Error during validation."""


class NetworkError(Exception):
    """Network-related error."""


class RegistryError(Exception):
    """Registry operation error."""


class MirrorError(Exception):
    """Mirror operation error."""


class ContractError(Exception):
    """Contract-related error."""
