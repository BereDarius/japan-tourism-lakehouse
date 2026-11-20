from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.ingestion_result import IngestionResult
from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId

DATASET_ID = DatasetId("accommodation_foreign_guest_nights")
RUN_ID = uuid4()
STARTED_AT = datetime.now(UTC)
COMPLETED_AT = STARTED_AT + timedelta(seconds=10)


@pytest.fixture
def artifact_acquisition() -> ArtifactAcquisition:
    artifact = StoredArtifact(
        dataset_id=DATASET_ID,
        original_filename="source.xlsx",
        sha256="a" * 64,
        uri="file:///tmp/source.xlsx",
    )

    return ArtifactAcquisition(
        acquisition_id=uuid4(),
        artifact=artifact,
        source_url="https://example.com/source.xlsx",
        retrieved_at=STARTED_AT,
    )


def test_creates_successful_ingestion_result(
    artifact_acquisition: ArtifactAcquisition,
) -> None:
    result = IngestionResult(
        dataset_id=DATASET_ID,
        run_id=RUN_ID,
        status=IngestionStatus.SUCCEEDED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        artifact_acquisition=artifact_acquisition,
        bronze_records_written=48,
        error_message=None,
    )

    assert result.dataset_id == DATASET_ID
    assert result.run_id == RUN_ID
    assert result.status == IngestionStatus.SUCCEEDED
    assert result.bronze_records_written == 48


def test_creates_failed_result_without_artifact() -> None:
    result = IngestionResult(
        dataset_id=DATASET_ID,
        run_id=RUN_ID,
        status=IngestionStatus.FAILED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        artifact_acquisition=None,
        bronze_records_written=0,
        error_message="Source download failed.",
    )

    assert result.artifact_acquisition is None
    assert result.bronze_records_written == 0


def test_allows_unknown_bronze_write_outcome(
    artifact_acquisition: ArtifactAcquisition,
) -> None:
    result = IngestionResult(
        dataset_id=DATASET_ID,
        run_id=RUN_ID,
        status=IngestionStatus.RECONCILIATION_REQUIRED,
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
        artifact_acquisition=artifact_acquisition,
        bronze_records_written=None,
        error_message="Bronze write outcome could not be determined.",
    )

    assert result.bronze_records_written is None


@pytest.mark.parametrize(
    "status",
    [IngestionStatus.PENDING, IngestionStatus.RUNNING],
)
def test_rejects_non_terminal_status(status: IngestionStatus) -> None:
    with pytest.raises(ValueError, match="terminal status"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=status,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=None,
            bronze_records_written=0,
            error_message=None,
        )


def test_rejects_naive_start_timestamp() -> None:
    with pytest.raises(ValueError, match="started_at"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.FAILED,
            started_at=datetime.now(),
            completed_at=COMPLETED_AT,
            artifact_acquisition=None,
            bronze_records_written=0,
            error_message="Test failure.",
        )


def test_rejects_completion_before_start() -> None:
    with pytest.raises(ValueError, match="cannot precede"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.FAILED,
            started_at=COMPLETED_AT,
            completed_at=STARTED_AT,
            artifact_acquisition=None,
            bronze_records_written=0,
            error_message="Test failure.",
        )


def test_rejects_negative_bronze_record_count() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.FAILED,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=None,
            bronze_records_written=-1,
            error_message="Test failure.",
        )


def test_rejects_success_without_acquisition() -> None:
    with pytest.raises(ValueError, match="artifact acquisition"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.SUCCEEDED,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=None,
            bronze_records_written=48,
            error_message=None,
        )


def test_rejects_success_with_unknown_record_count(
    artifact_acquisition: ArtifactAcquisition,
) -> None:
    with pytest.raises(ValueError, match="known Bronze record count"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.SUCCEEDED,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=artifact_acquisition,
            bronze_records_written=None,
            error_message=None,
        )


def test_rejects_failure_without_error_message() -> None:
    with pytest.raises(ValueError, match="error message"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.FAILED,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=None,
            bronze_records_written=0,
            error_message=None,
        )


def test_rejects_success_with_error_message(
    artifact_acquisition: ArtifactAcquisition,
) -> None:
    with pytest.raises(ValueError, match="cannot have an error message"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.SUCCEEDED,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=artifact_acquisition,
            bronze_records_written=48,
            error_message="Unexpected error.",
        )


def test_rejects_failed_result_with_written_records(
    artifact_acquisition: ArtifactAcquisition,
) -> None:
    with pytest.raises(ValueError, match="zero Bronze records"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.FAILED,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=artifact_acquisition,
            bronze_records_written=10,
            error_message="Ingestion failed.",
        )


def test_rejects_reconciliation_result_with_known_record_count() -> None:
    with pytest.raises(ValueError, match="unknown Bronze record count"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.RECONCILIATION_REQUIRED,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=None,
            bronze_records_written=48,
            error_message="Write outcome unknown.",
        )


@pytest.mark.parametrize("error_message", [None, "", "   "])
def test_rejects_failed_result_without_valid_error_message(
    error_message: str | None,
) -> None:
    with pytest.raises(ValueError, match="error message"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.FAILED,
            started_at=STARTED_AT,
            completed_at=COMPLETED_AT,
            artifact_acquisition=None,
            bronze_records_written=0,
            error_message=error_message,
        )


@pytest.mark.parametrize("timestamp_field", ["started_at", "completed_at"])
def test_rejects_non_utc_timestamps(timestamp_field: str) -> None:
    non_utc_offset = timezone(timedelta(hours=2))

    timestamps = {
        "started_at": STARTED_AT.astimezone(non_utc_offset),
        "completed_at": COMPLETED_AT.astimezone(non_utc_offset),
    }

    with pytest.raises(ValueError, match="UTC"):
        IngestionResult(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.FAILED,
            started_at=timestamps["started_at"],
            completed_at=timestamps["completed_at"],
            artifact_acquisition=None,
            bronze_records_written=0,
            error_message="Test failure.",
        )
