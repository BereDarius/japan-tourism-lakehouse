from datetime import UTC
from uuid import UUID

import pytest

from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId


@pytest.fixture
def ingestion_run() -> IngestionRun:
    return IngestionRun(dataset_id=DatasetId("accommodation_foreign_guest_nights"))


def test_new_run_starts_as_pending(ingestion_run: IngestionRun) -> None:
    assert ingestion_run.status == IngestionStatus.PENDING
    assert isinstance(ingestion_run.run_id, UUID)
    assert ingestion_run.started_at is None
    assert ingestion_run.completed_at is None
    assert ingestion_run.error_message is None


def test_start_transitions_run_to_running(
    ingestion_run: IngestionRun,
) -> None:
    ingestion_run.start()

    assert ingestion_run.status == IngestionStatus.RUNNING
    assert ingestion_run.started_at is not None
    assert ingestion_run.started_at.tzinfo == UTC


def test_succeed_completes_running_run(
    ingestion_run: IngestionRun,
) -> None:
    ingestion_run.start()
    ingestion_run.succeed()

    assert ingestion_run.status == IngestionStatus.SUCCEEDED
    assert ingestion_run.completed_at is not None
    assert ingestion_run.completed_at.tzinfo == UTC


def test_fail_records_error_message(
    ingestion_run: IngestionRun,
) -> None:
    ingestion_run.start()
    ingestion_run.fail("Source file could not be read.")

    assert ingestion_run.status == IngestionStatus.FAILED
    assert ingestion_run.error_message == "Source file could not be read."
    assert ingestion_run.completed_at is not None


def test_reconciliation_required_records_reason(
    ingestion_run: IngestionRun,
) -> None:
    ingestion_run.start()
    ingestion_run.require_reconciliation("Bronze write outcome is uncertain.")

    assert ingestion_run.status == IngestionStatus.RECONCILIATION_REQUIRED
    assert ingestion_run.error_message == "Bronze write outcome is uncertain."
    assert ingestion_run.completed_at is not None


def test_cannot_start_run_twice(ingestion_run: IngestionRun) -> None:
    ingestion_run.start()

    with pytest.raises(ValueError):
        ingestion_run.start()


def test_cannot_complete_pending_run(ingestion_run: IngestionRun) -> None:
    with pytest.raises(ValueError):
        ingestion_run.succeed()


def test_cannot_modify_completed_run(ingestion_run: IngestionRun) -> None:
    ingestion_run.start()
    ingestion_run.succeed()

    with pytest.raises(ValueError):
        ingestion_run.fail("Late failure")


@pytest.mark.parametrize("message", ["", "   "])
def test_failure_requires_non_empty_message(
    ingestion_run: IngestionRun,
    message: str,
) -> None:
    ingestion_run.start()

    with pytest.raises(ValueError):
        ingestion_run.fail(message)


def test_reconciliation_requires_non_empty_reason(
    ingestion_run: IngestionRun,
) -> None:
    ingestion_run.start()

    with pytest.raises(ValueError):
        ingestion_run.require_reconciliation("   ")


def test_run_id_cannot_be_modified(ingestion_run: IngestionRun) -> None:
    with pytest.raises(AttributeError):
        setattr(ingestion_run, "run_id", UUID(int=1))  # noqa: B010


def test_dataset_id_cannot_be_modified(ingestion_run: IngestionRun) -> None:
    with pytest.raises(AttributeError):
        setattr(ingestion_run, "dataset_id", DatasetId("another_dataset"))  # noqa: B010


def test_status_cannot_be_modified_directly(
    ingestion_run: IngestionRun,
) -> None:
    with pytest.raises(AttributeError):
        setattr(ingestion_run, "status", IngestionStatus.SUCCEEDED)  # noqa: B010


def test_timestamps_cannot_be_modified_directly(
    ingestion_run: IngestionRun,
) -> None:
    with pytest.raises(AttributeError):
        setattr(ingestion_run, "started_at", None)  # noqa: B010


def test_error_message_cannot_be_modified_directly(
    ingestion_run: IngestionRun,
) -> None:
    with pytest.raises(AttributeError):
        setattr(ingestion_run, "error_message", "Manipulated error")  # noqa: B010
