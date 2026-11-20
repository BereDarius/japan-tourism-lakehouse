from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId

DATASET_ID = DatasetId("accommodation_foreign_guest_nights")
RUN_ID = uuid4()

STARTED_AT = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
COMPLETED_AT = datetime(2026, 1, 15, 10, 5, tzinfo=UTC)
ERROR_MESSAGE = "Source extraction failed."


@pytest.mark.parametrize(
    ("status", "started_at", "completed_at", "error_message"),
    [
        (IngestionStatus.PENDING, None, None, None),
        (IngestionStatus.RUNNING, STARTED_AT, None, None),
        (IngestionStatus.SUCCEEDED, STARTED_AT, COMPLETED_AT, None),
        (
            IngestionStatus.FAILED,
            STARTED_AT,
            COMPLETED_AT,
            ERROR_MESSAGE,
        ),
        (
            IngestionStatus.RECONCILIATION_REQUIRED,
            STARTED_AT,
            COMPLETED_AT,
            ERROR_MESSAGE,
        ),
    ],
)
def test_reconstitute_restores_valid_state(
    status: IngestionStatus,
    started_at: datetime | None,
    completed_at: datetime | None,
    error_message: str | None,
) -> None:
    run = IngestionRun.reconstitute(
        dataset_id=DATASET_ID,
        run_id=RUN_ID,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message,
    )

    assert run.dataset_id == DATASET_ID
    assert run.run_id == RUN_ID
    assert run.status == status
    assert run.started_at == started_at
    assert run.completed_at == completed_at
    assert run.error_message == error_message


@pytest.mark.parametrize(
    ("status", "started_at", "completed_at", "error_message"),
    [
        # PENDING must not contain lifecycle metadata.
        (IngestionStatus.PENDING, STARTED_AT, None, None),
        (IngestionStatus.PENDING, None, COMPLETED_AT, None),
        (IngestionStatus.PENDING, None, None, ERROR_MESSAGE),
        # RUNNING requires a start but no completion or error.
        (IngestionStatus.RUNNING, None, None, None),
        (IngestionStatus.RUNNING, STARTED_AT, COMPLETED_AT, None),
        (IngestionStatus.RUNNING, STARTED_AT, None, ERROR_MESSAGE),
        # SUCCEEDED requires both timestamps and no error.
        (IngestionStatus.SUCCEEDED, None, COMPLETED_AT, None),
        (IngestionStatus.SUCCEEDED, STARTED_AT, None, None),
        (
            IngestionStatus.SUCCEEDED,
            STARTED_AT,
            COMPLETED_AT,
            ERROR_MESSAGE,
        ),
        # FAILED requires both timestamps and a non-empty error.
        (IngestionStatus.FAILED, None, COMPLETED_AT, ERROR_MESSAGE),
        (IngestionStatus.FAILED, STARTED_AT, None, ERROR_MESSAGE),
        (IngestionStatus.FAILED, STARTED_AT, COMPLETED_AT, None),
        (IngestionStatus.FAILED, STARTED_AT, COMPLETED_AT, "  "),
        # RECONCILIATION_REQUIRED has the same metadata requirements.
        (
            IngestionStatus.RECONCILIATION_REQUIRED,
            None,
            COMPLETED_AT,
            ERROR_MESSAGE,
        ),
        (
            IngestionStatus.RECONCILIATION_REQUIRED,
            STARTED_AT,
            None,
            ERROR_MESSAGE,
        ),
        (
            IngestionStatus.RECONCILIATION_REQUIRED,
            STARTED_AT,
            COMPLETED_AT,
            None,
        ),
        (
            IngestionStatus.RECONCILIATION_REQUIRED,
            STARTED_AT,
            COMPLETED_AT,
            "  ",
        ),
    ],
)
def test_reconstitute_rejects_invalid_state(
    status: IngestionStatus,
    started_at: datetime | None,
    completed_at: datetime | None,
    error_message: str | None,
) -> None:
    with pytest.raises(ValueError, match="Invalid persisted state"):
        IngestionRun.reconstitute(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
        )


@pytest.mark.parametrize("timestamp_field", ["started_at", "completed_at"])
def test_reconstitute_rejects_naive_timestamps(
    timestamp_field: str,
) -> None:
    naive_timestamp = datetime(2026, 1, 15, 10, 0)

    timestamps = {
        "started_at": STARTED_AT,
        "completed_at": COMPLETED_AT,
    }
    timestamps[timestamp_field] = naive_timestamp

    with pytest.raises(ValueError, match="timezone-aware"):
        IngestionRun.reconstitute(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.SUCCEEDED,
            started_at=timestamps["started_at"],
            completed_at=timestamps["completed_at"],
            error_message=None,
        )


def test_reconstitute_rejects_completion_before_start() -> None:
    with pytest.raises(ValueError, match="cannot precede"):
        IngestionRun.reconstitute(
            dataset_id=DATASET_ID,
            run_id=RUN_ID,
            status=IngestionStatus.SUCCEEDED,
            started_at=COMPLETED_AT,
            completed_at=STARTED_AT,
            error_message=None,
        )


def test_reconstitute_preserves_original_timestamps_and_run_id() -> None:
    run_id = uuid4()
    started_at = datetime(2026, 2, 1, 8, 30, tzinfo=UTC)
    completed_at = started_at + timedelta(minutes=12)

    run = IngestionRun.reconstitute(
        dataset_id=DATASET_ID,
        run_id=run_id,
        status=IngestionStatus.FAILED,
        started_at=started_at,
        completed_at=completed_at,
        error_message=ERROR_MESSAGE,
    )

    assert run.run_id == run_id
    assert run.started_at is started_at
    assert run.completed_at is completed_at
    assert run.error_message == ERROR_MESSAGE
