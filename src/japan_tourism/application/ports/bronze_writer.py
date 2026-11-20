from collections.abc import Sequence
from typing import Protocol

from japan_tourism.application.models.bronze_record import BronzeRecord


class BronzeWriter(Protocol):
    """Port for persisting records into the Bronze layer."""

    def write(self, records: Sequence[BronzeRecord]) -> None:
        """Append Bronze records to persistent storage."""
        ...
