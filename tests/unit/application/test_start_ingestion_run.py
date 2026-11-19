from japan_tourism.application.use_cases.start_ingestion_run import (
    StartIngestionRun,
)
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.persistence.in_memory_ingestion_run_repository import (
    InMemoryIngestionRunRepository,
)


def test_start_ingestion_run_creates_running_run() -> None:
    repository = InMemoryIngestionRunRepository()
    use_case = StartIngestionRun(repository)
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    run = use_case.execute(dataset_id)

    assert run.dataset_id == dataset_id
    assert run.status == IngestionStatus.RUNNING
    assert run.started_at is not None
    assert run.completed_at is None


def test_start_ingestion_run_persists_created_run() -> None:
    repository = InMemoryIngestionRunRepository()
    use_case = StartIngestionRun(repository)
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    run = use_case.execute(dataset_id)

    assert repository.get_by_id(run.run_id) is run


def test_starting_multiple_runs_creates_unique_run_ids() -> None:
    repository = InMemoryIngestionRunRepository()
    use_case = StartIngestionRun(repository)
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    first_run = use_case.execute(dataset_id)
    second_run = use_case.execute(dataset_id)

    assert first_run.run_id != second_run.run_id
    assert len(repository.get_by_dataset_id(dataset_id)) == 2
