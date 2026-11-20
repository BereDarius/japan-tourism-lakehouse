from typing import BinaryIO, Protocol

from japan_tourism.application.models.dataset_manifest import (
    ExcelReaderConfig,
)
from japan_tourism.application.models.extracted_worksheet import (
    ExtractedWorksheet,
)


class SourceReader(Protocol):
    """Port for extracting data from source artifacts."""

    def read(
        self,
        source: BinaryIO,
        config: ExcelReaderConfig,
    ) -> ExtractedWorksheet:
        """Extract source-shaped data using the supplied configuration."""
        ...
