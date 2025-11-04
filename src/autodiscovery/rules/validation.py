"""Validation rules per source key."""

# Expected MIME types and size constraints per source key
VALIDATION_RULES: dict[str, dict] = {
    "bcra_series": {
        "expected_mime": "application/vnd.ms-excel.sheet.macroEnabled.12",
        "min_size_kb": 100,
    },
    "bcra_infomodia": {
        "expected_mime": "application/vnd.ms-excel",
        "min_size_kb": 50,
    },
    "bcra_rem_pdf": {
        "expected_mime": "application/pdf",
        "min_size_kb": 200,
    },
    "indec_emae": {
        "expected_mime_any": [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "application/pdf",
            "text/csv",
        ],
        "min_size_kb": 50,
    },
}


def get_expected_mime(key: str) -> str | None:
    """Get expected MIME type for source key."""
    rule = VALIDATION_RULES.get(key, {})
    result = rule.get("expected_mime")
    return result if isinstance(result, str) else None


def get_expected_mime_any(key: str) -> list[str] | None:
    """Get list of acceptable MIME types for source key."""
    rule = VALIDATION_RULES.get(key, {})
    result = rule.get("expected_mime_any")
    return result if isinstance(result, list) else None


def get_min_size_kb(key: str) -> int | None:
    """Get minimum size in KB for source key."""
    rule = VALIDATION_RULES.get(key, {})
    result = rule.get("min_size_kb")
    return result if isinstance(result, int) else None


def validate_mime(key: str, mime: str) -> bool:
    """Validate MIME type against rules."""
    expected = get_expected_mime(key)
    if expected:
        return mime == expected

    expected_any = get_expected_mime_any(key)
    if expected_any:
        return mime in expected_any

    # No rule defined, accept any
    return True


def validate_size(key: str, size_kb: float) -> bool:
    """Validate file size against rules."""
    min_size = get_min_size_kb(key)
    if min_size is None:
        return True
    return size_kb >= min_size
