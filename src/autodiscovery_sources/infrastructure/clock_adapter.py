"""Clock adapter for time operations."""

from datetime import datetime

from ..interfaces.clock_port import ClockPort


class ClockAdapter(ClockPort):
    """Clock adapter using system time."""

    def now(self) -> datetime:
        """Get current datetime."""
        return datetime.now()

