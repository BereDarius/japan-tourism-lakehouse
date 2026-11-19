from uuid import UUID

import pytest

from japan_tourism.application.exceptions import IngestionRunNotFoundError
from japan_tourism.application.use_cases.complete_ingestion_run import (
    CompleteIngestionRun,
)
from japan_tourism.application.use_cases.start_ingestion_run import (
    StartIngestionRun,
)
from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.persistence.in_memory_ingestion_run_repository import (
    InMemoryIngestionRunRepository,
)


def test_complete_ingestion_run_marks_run_as_succeeded() -> None:
    repository = InMemoryIngestionRunRepository()
    start_use_case = StartIngestionRun(repository)
    complete_use_case = CompleteIngestionRun(repository)

    run = start_use_case.execute(DatasetId("accommodation_foreign_guest_nights"))

    completed_run = complete_use_case.execute(run.run_id)

    assert completed_run.status == IngestionStatus.SUCCEEDED
    assert completed_run.completed_at is not None


def test_complete_ingestion_run_returns_persisted_run() -> None:
    repository = InMemoryIngestionRunRepository()
    start_use_case = StartIngestionRun(repository)
    complete_use_case = CompleteIngestionRun(repository)

    run = start_use_case.execute(DatasetId("accommodation_foreign_guest_nights"))

    completed_run = complete_use_case.execute(run.run_id)

    assert repository.get_by_id(run.run_id) is completed_run


def test_complete_ingestion_run_raises_when_run_does_not_exist() -> None:
    repository = InMemoryIngestionRunRepository()
    complete_use_case = CompleteIngestionRun(repository)
    missing_run_id = UUID(int=0)

    with pytest.raises(IngestionRunNotFoundError) as exc_info:
        complete_use_case.execute(missing_run_id)

    assert exc_info.value.run_id == str(missing_run_id)


def test_complete_ingestion_run_rejects_pending_run() -> None:
    repository = InMemoryIngestionRunRepository()
    complete_use_case = CompleteIngestionRun(repository)

    run = IngestionRun(dataset_id=DatasetId("accommodation_foreign_guest_nights"))
    repository.save(run)

    with pytest.raises(ValueError):
        complete_use_case.execute(run.run_id)

    assert run.status == IngestionStatus.PENDING
