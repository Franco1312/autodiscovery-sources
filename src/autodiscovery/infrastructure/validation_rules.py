"""Validation rules implementation."""

from autodiscovery.domain.interfaces import IValidationRules
from autodiscovery.rules.discontinuities import get_discontinuity_notes
from autodiscovery.rules.validation import (
    get_expected_mime,
    get_expected_mime_any,
    get_min_size_kb,
    validate_mime,
    validate_size,
)


class ValidationRules(IValidationRules):
    """Implementation of validation rules."""

    def validate_mime(self, key: str, mime: str) -> bool:
        """Validate MIME type for key."""
        return validate_mime(key, mime)

    def validate_size(self, key: str, size_kb: float) -> bool:
        """Validate size for key."""
        return validate_size(key, size_kb)

    def get_expected_mime(self, key: str) -> str | None:
        """Get expected MIME type for key."""
        return get_expected_mime(key)

    def get_expected_mime_any(self, key: str) -> list[str] | None:
        """Get list of expected MIME types for key."""
        return get_expected_mime_any(key)

    def get_min_size_kb(self, key: str) -> float | None:
        """Get minimum size in KB for key."""
        return get_min_size_kb(key)

    def get_discontinuity_notes(self, key: str) -> str | None:
        """Get discontinuity notes for key."""
        return get_discontinuity_notes(key)
