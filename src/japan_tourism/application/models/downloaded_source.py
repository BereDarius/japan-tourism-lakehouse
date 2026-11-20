from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True)
class DownloadedSource:
    """Represents a temporarily available artifact retrieved from a source."""

    stream: BinaryIO
    original_filename: str
    source_url: str
