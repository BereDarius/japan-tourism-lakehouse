from uuid import UUID

from japan_tourism.application.ports.ingestion_run_repository import (
    IngestionRunRepository,
)
from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.persistence.in_memory_ingestion_run_repository import (
    InMemoryIngestionRunRepository,
)


def test_repository_implements_repository_port() -> None:
    repository: IngestionRunRepository = InMemoryIngestionRunRepository()

    assert repository is not None


def test_save_and_retrieve_run_by_id() -> None:
    repository = InMemoryIngestionRunRepository()
    run = IngestionRun(dataset_id=DatasetId("accommodation_foreign_guest_nights"))

    repository.save(run)

    assert repository.get_by_id(run.run_id) is run


def test_get_by_id_returns_none_when_run_does_not_exist() -> None:
    repository = InMemoryIngestionRunRepository()

    assert repository.get_by_id(UUID(int=0)) is None


def test_saving_same_run_twice_does_not_create_duplicates() -> None:
    repository = InMemoryIngestionRunRepository()
    run = IngestionRun(dataset_id=DatasetId("accommodation_foreign_guest_nights"))

    repository.save(run)
    repository.save(run)

    assert len(repository.get_by_dataset_id(run.dataset_id)) == 1


def test_get_by_dataset_id_returns_only_matching_runs() -> None:
    repository = InMemoryIngestionRunRepository()
    dataset_id = DatasetId("accommodation_foreign_guest_nights")
    other_dataset_id = DatasetId("visitor_survey")

    matching_run = IngestionRun(dataset_id=dataset_id)
    other_run = IngestionRun(dataset_id=other_dataset_id)

    repository.save(matching_run)
    repository.save(other_run)

    assert repository.get_by_dataset_id(dataset_id) == [matching_run]


def test_get_by_status_returns_only_matching_runs() -> None:
    repository = InMemoryIngestionRunRepository()

    pending_run = IngestionRun(dataset_id=DatasetId("accommodation_foreign_guest_nights"))
    running_run = IngestionRun(dataset_id=DatasetId("visitor_survey"))
    running_run.start()

    repository.save(pending_run)
    repository.save(running_run)

    assert repository.get_by_status(IngestionStatus.PENDING) == [pending_run]
    assert repository.get_by_status(IngestionStatus.RUNNING) == [running_run]


def test_filters_return_empty_lists_when_no_runs_match() -> None:
    repository = InMemoryIngestionRunRepository()

    assert repository.get_by_dataset_id(DatasetId("accommodation_foreign_guest_nights")) == []
    assert repository.get_by_status(IngestionStatus.FAILED) == []


def test_saving_existing_run_id_replaces_stored_run() -> None:
    repository = InMemoryIngestionRunRepository()
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    original_run = IngestionRun(dataset_id=dataset_id)
    repository.save(original_run)

    updated_run = IngestionRun(
        dataset_id=dataset_id,
        run_id=original_run.run_id,
    )
    updated_run.start()

    repository.save(updated_run)

    assert repository.get_by_id(original_run.run_id) is updated_run
    assert repository.get_by_status(IngestionStatus.RUNNING) == [updated_run]
    assert repository.get_by_status(IngestionStatus.PENDING) == []
    assert repository.get_by_dataset_id(dataset_id) == [updated_run]


def test_get_by_dataset_id_returns_all_matching_runs() -> None:
    repository = InMemoryIngestionRunRepository()
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    first_run = IngestionRun(dataset_id=dataset_id)
    second_run = IngestionRun(dataset_id=dataset_id)
    third_run = IngestionRun(dataset_id=DatasetId("visitor_survey"))

    repository.save(first_run)
    repository.save(second_run)
    repository.save(third_run)

    results = repository.get_by_dataset_id(dataset_id)

    assert len(results) == 2
    assert first_run in results
    assert second_run in results
    assert third_run not in results
