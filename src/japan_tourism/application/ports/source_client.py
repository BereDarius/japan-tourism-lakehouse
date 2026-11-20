from contextlib import AbstractContextManager
from typing import Protocol

from japan_tourism.application.models.downloaded_source import (
    DownloadedSource,
)


class SourceClient(Protocol):
    """Port for retrieving source artifacts."""

    def open(
        self,
        source_url: str,
    ) -> AbstractContextManager[DownloadedSource]:
        """Open a source artifact as a managed streaming resource."""
        ...
