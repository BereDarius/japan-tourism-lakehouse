from uuid import UUID

import pytest

from japan_tourism.application.exceptions import IngestionRunNotFoundError
from japan_tourism.application.use_cases.fail_ingestion_run import FailIngestionRun
from japan_tourism.application.use_cases.start_ingestion_run import StartIngestionRun
from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.persistence.in_memory_ingestion_run_repository import (
    InMemoryIngestionRunRepository,
)


def test_fail_ingestion_run_marks_run_as_failed() -> None:
    repository = InMemoryIngestionRunRepository()
    run = StartIngestionRun(repository).execute(DatasetId("accommodation_foreign_guest_nights"))

    failed_run = FailIngestionRun(repository).execute(
        run.run_id,
        "Source file could not be downloaded.",
    )

    assert failed_run.status == IngestionStatus.FAILED
    assert failed_run.error_message == "Source file could not be downloaded."
    assert failed_run.completed_at is not None


def test_fail_ingestion_run_persists_updated_run() -> None:
    repository = InMemoryIngestionRunRepository()
    run = StartIngestionRun(repository).execute(DatasetId("accommodation_foreign_guest_nights"))

    failed_run = FailIngestionRun(repository).execute(
        run.run_id,
        "Extraction failed.",
    )

    assert repository.get_by_id(run.run_id) is failed_run


def test_fail_ingestion_run_raises_when_run_does_not_exist() -> None:
    repository = InMemoryIngestionRunRepository()

    with pytest.raises(IngestionRunNotFoundError):
        FailIngestionRun(repository).execute(
            UUID(int=0),
            "Extraction failed.",
        )


def test_fail_ingestion_run_rejects_pending_run() -> None:
    repository = InMemoryIngestionRunRepository()
    run = IngestionRun(dataset_id=DatasetId("accommodation_foreign_guest_nights"))
    repository.save(run)

    with pytest.raises(ValueError):
        FailIngestionRun(repository).execute(
            run.run_id,
            "Extraction failed.",
        )

    assert run.status == IngestionStatus.PENDING


def test_fail_ingestion_run_rejects_empty_error_message() -> None:
    repository = InMemoryIngestionRunRepository()
    run = StartIngestionRun(repository).execute(DatasetId("accommodation_foreign_guest_nights"))

    with pytest.raises(ValueError):
        FailIngestionRun(repository).execute(run.run_id, "  ")

    assert run.status == IngestionStatus.RUNNING
