from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Immutable outcome of a completed dataset ingestion."""

    dataset_id: DatasetId
    run_id: UUID
    status: IngestionStatus
    started_at: datetime
    completed_at: datetime
    artifact_acquisition: ArtifactAcquisition | None
    bronze_records_written: int | None
    error_message: str | None

    def __post_init__(self) -> None:
        """Validate the consistency of the execution result."""
        terminal_statuses = {
            IngestionStatus.SUCCEEDED,
            IngestionStatus.FAILED,
            IngestionStatus.RECONCILIATION_REQUIRED,
        }

        if self.status not in terminal_statuses:
            raise ValueError("Ingestion result must have a terminal status.")

        if self.started_at.utcoffset() != timedelta(0):
            raise ValueError("started_at must be in UTC.")

        if self.completed_at.utcoffset() != timedelta(0):
            raise ValueError("completed_at must be in UTC.")

        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at must be timezone-aware.")

        if self.completed_at.tzinfo is None or self.completed_at.utcoffset() is None:
            raise ValueError("completed_at must be timezone-aware.")

        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at.")

        if self.bronze_records_written is not None and self.bronze_records_written < 0:
            raise ValueError("bronze_records_written cannot be negative.")

        if self.bronze_records_written is not None and type(self.bronze_records_written) is not int:
            raise ValueError("bronze_records_written must be an integer or None.")

        if self.status == IngestionStatus.SUCCEEDED:
            if self.artifact_acquisition is None:
                raise ValueError("A successful ingestion must have an artifact acquisition.")

            if self.bronze_records_written is None:
                raise ValueError("A successful ingestion must have a known Bronze record count.")

            if self.error_message is not None:
                raise ValueError("A successful ingestion cannot have an error message.")
        elif self.status == IngestionStatus.FAILED:
            if self.bronze_records_written != 0:
                raise ValueError("A failed ingestion must have zero Bronze records.")

            if self.error_message is None or not self.error_message.strip():
                raise ValueError("A failed ingestion must have an error message.")

        elif self.status == IngestionStatus.RECONCILIATION_REQUIRED:
            if self.bronze_records_written is not None:
                raise ValueError(
                    "A reconciliation-required ingestion must have an unknown Bronze record count."
                )

            if self.error_message is None or not self.error_message.strip():
                raise ValueError("A reconciliation-required ingestion must have an error message.")
