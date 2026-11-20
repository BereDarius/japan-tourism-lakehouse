from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from japan_tourism.domain.value_objects.dataset_id import DatasetId


@dataclass(frozen=True)
class BronzeRecord:
    """Represents one source row prepared for Bronze persistence."""

    dataset_id: DatasetId
    ingestion_run_id: UUID
    artifact_acquisition_id: UUID
    artifact_sha256: str
    source_url: str
    retrieved_at: datetime

    worksheet_name: str
    source_row_number: int

    title: str
    unit: str
    reporting_year: int

    column_headers_json: str
    row_data_json: str

    def __post_init__(self) -> None:
        if not self.artifact_sha256.strip():
            raise ValueError("artifact_sha256 cannot be empty.")

        if not self.source_url.strip():
            raise ValueError("source_url cannot be empty.")

        if not self.worksheet_name.strip():
            raise ValueError("worksheet_name cannot be empty.")

        if self.source_row_number < 1:
            raise ValueError("source_row_number must be positive.")

        if self.reporting_year < 1:
            raise ValueError("reporting_year must be positive.")

        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware.")
