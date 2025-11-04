"""Documentation of known discontinuities and metadata."""

# Known discontinuities per source key
DISCONTINUITIES: dict[str, dict] = {
    "bcra_series": {
        "notes": [
            "LELIQ TNA = s/o desde 2024-07-19",
            "Pases stock dejó de publicarse en series.xlsm desde 2024-07-19 → usar PV/API",
        ],
    },
}


def get_discontinuity_notes(key: str) -> str | None:
    """Get discontinuity notes for source key."""
    disc = DISCONTINUITIES.get(key)
    if not disc:
        return None

    notes = disc.get("notes", [])
    if notes:
        return "; ".join(notes)

    return None
