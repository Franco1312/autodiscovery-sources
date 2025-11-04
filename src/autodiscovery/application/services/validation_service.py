"""Service for validating discovered files."""

import logging

from autodiscovery.domain.entities import DiscoveredFile
from autodiscovery.domain.interfaces import IFileValidator, IValidationRules

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating discovered files."""

    def __init__(
        self,
        file_validator: IFileValidator,
        validation_rules: IValidationRules,
    ):
        self.file_validator = file_validator
        self.validation_rules = validation_rules

    def validate_discovered_file(
        self,
        discovered: DiscoveredFile,
        key: str,
    ) -> tuple[bool, str, str | None]:
        """
        Validate a discovered file.

        Args:
            discovered: DiscoveredFile to validate
            key: Source key for validation rules

        Returns:
            (is_valid, status, notes) tuple
            - is_valid: True if file passes validation
            - status: "ok", "suspect", or "broken"
            - notes: Optional notes about discontinuities
        """
        # Get validation rules
        expected_mime = self.validation_rules.get_expected_mime(key)
        expected_mime_any = self.validation_rules.get_expected_mime_any(key)
        min_size_kb = self.validation_rules.get_min_size_kb(key)

        # Validate file accessibility
        is_accessible, mime, size_kb = self.file_validator.validate_file(
            discovered.url,
            key,
            expected_mime=expected_mime,
            expected_mime_any=expected_mime_any,
            min_size_kb=min_size_kb,
        )

        if not is_accessible:
            return False, "broken", None

        # Update discovered file with actual metadata
        discovered.mime = mime
        discovered.size_kb = size_kb

        # Validate MIME type
        mime_valid = self.validation_rules.validate_mime(key, mime or "")

        # Validate size
        size_valid = self.validation_rules.validate_size(key, size_kb or 0)

        # Determine status
        status = "ok" if mime_valid and size_valid else "suspect"

        # Get discontinuity notes
        notes = self.validation_rules.get_discontinuity_notes(key)

        return True, status, notes
