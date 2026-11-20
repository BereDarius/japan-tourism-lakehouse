from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.persistence.sqlite_ingestion_run_repository import (
    SQLiteIngestionRunRepository,
)

DATASET_ID = DatasetId("accommodation_foreign_guest_nights")
OTHER_DATASET_ID = DatasetId("international_visitor_survey")

STARTED_AT = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
COMPLETED_AT = datetime(2026, 1, 15, 10, 5, tzinfo=UTC)
ERROR_MESSAGE = "Source extraction failed."


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "metadata.sqlite"


@pytest.fixture
def repository(
    database_path: Path,
) -> SQLiteIngestionRunRepository:
    return SQLiteIngestionRunRepository(database_path)


def create_run(
    status: IngestionStatus,
    dataset_id: DatasetId = DATASET_ID,
    run_id: UUID | None = None,
) -> IngestionRun:
    started_at = None
    completed_at = None
    error_message = None

    if status != IngestionStatus.PENDING:
        started_at = STARTED_AT

    if status in (
        IngestionStatus.SUCCEEDED,
        IngestionStatus.FAILED,
        IngestionStatus.RECONCILIATION_REQUIRED,
    ):
        completed_at = COMPLETED_AT

    if status in (
        IngestionStatus.FAILED,
        IngestionStatus.RECONCILIATION_REQUIRED,
    ):
        error_message = ERROR_MESSAGE

    return IngestionRun.reconstitute(
        dataset_id=dataset_id,
        run_id=run_id or uuid4(),
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message,
    )


@pytest.mark.parametrize(
    "status",
    list(IngestionStatus),
)
def test_save_and_get_by_id_preserves_run_state(
    repository: SQLiteIngestionRunRepository,
    status: IngestionStatus,
) -> None:
    run = create_run(status)

    repository.save(run)

    result = repository.get_by_id(run.run_id)

    assert result is not None
    assert result.run_id == run.run_id
    assert result.dataset_id == run.dataset_id
    assert result.status == run.status
    assert result.started_at == run.started_at
    assert result.completed_at == run.completed_at
    assert result.error_message == run.error_message


def test_get_by_id_returns_none_for_unknown_run(
    repository: SQLiteIngestionRunRepository,
) -> None:
    assert repository.get_by_id(uuid4()) is None


def test_save_updates_existing_run(
    repository: SQLiteIngestionRunRepository,
) -> None:
    run = IngestionRun(dataset_id=DATASET_ID)
    run.start()

    repository.save(run)

    run.succeed()
    repository.save(run)

    result = repository.get_by_id(run.run_id)

    assert result is not None
    assert result.status == IngestionStatus.SUCCEEDED
    assert result.started_at is not None
    assert result.completed_at is not None


def test_get_by_dataset_id_returns_only_matching_runs(
    repository: SQLiteIngestionRunRepository,
) -> None:
    first_run = create_run(IngestionStatus.SUCCEEDED)
    second_run = create_run(IngestionStatus.FAILED)
    other_run = create_run(
        IngestionStatus.SUCCEEDED,
        dataset_id=OTHER_DATASET_ID,
    )

    for run in (first_run, second_run, other_run):
        repository.save(run)

    results = repository.get_by_dataset_id(DATASET_ID)

    assert {run.run_id for run in results} == {
        first_run.run_id,
        second_run.run_id,
    }


def test_get_by_status_returns_only_matching_runs(
    repository: SQLiteIngestionRunRepository,
) -> None:
    succeeded_run = create_run(IngestionStatus.SUCCEEDED)
    failed_run = create_run(IngestionStatus.FAILED)
    another_succeeded_run = create_run(IngestionStatus.SUCCEEDED)

    for run in (succeeded_run, failed_run, another_succeeded_run):
        repository.save(run)

    results = repository.get_by_status(IngestionStatus.SUCCEEDED)

    assert {run.run_id for run in results} == {
        succeeded_run.run_id,
        another_succeeded_run.run_id,
    }


def test_repository_preserves_runs_after_reopening_database(
    database_path: Path,
) -> None:
    run = create_run(IngestionStatus.RECONCILIATION_REQUIRED)

    first_repository = SQLiteIngestionRunRepository(database_path)
    first_repository.save(run)

    second_repository = SQLiteIngestionRunRepository(database_path)
    result = second_repository.get_by_id(run.run_id)

    assert result is not None
    assert result.status == IngestionStatus.RECONCILIATION_REQUIRED
    assert result.error_message == ERROR_MESSAGE
    assert result.started_at == STARTED_AT
    assert result.completed_at == COMPLETED_AT


def test_get_by_dataset_id_returns_deterministic_order(
    repository: SQLiteIngestionRunRepository,
) -> None:
    later_run = create_run(
        IngestionStatus.RUNNING,
        run_id=UUID(int=2),
    )
    earlier_run = create_run(
        IngestionStatus.RUNNING,
        run_id=UUID(int=1),
    )

    for run in (later_run, earlier_run):
        repository.save(run)

    results = repository.get_by_dataset_id(DATASET_ID)

    assert [run.run_id for run in results] == [
        earlier_run.run_id,
        later_run.run_id,
    ]


def test_get_by_dataset_id_returns_empty_list_when_no_matches(
    repository: SQLiteIngestionRunRepository,
) -> None:
    assert repository.get_by_dataset_id(DATASET_ID) == []


def test_get_by_status_returns_empty_list_when_no_matches(
    repository: SQLiteIngestionRunRepository,
) -> None:
    assert repository.get_by_status(IngestionStatus.FAILED) == []
