from uuid import UUID

import pytest

from japan_tourism.application.exceptions import IngestionRunNotFoundError
from japan_tourism.application.use_cases.require_reconciliation import (
    RequireReconciliation,
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


def test_require_reconciliation_updates_run_status() -> None:
    repository = InMemoryIngestionRunRepository()
    run = StartIngestionRun(repository).execute(DatasetId("accommodation_foreign_guest_nights"))

    updated_run = RequireReconciliation(repository).execute(
        run.run_id,
        "Bronze write outcome could not be determined.",
    )

    assert updated_run.status == IngestionStatus.RECONCILIATION_REQUIRED
    assert updated_run.error_message == ("Bronze write outcome could not be determined.")
    assert updated_run.completed_at is not None


def test_require_reconciliation_persists_updated_run() -> None:
    repository = InMemoryIngestionRunRepository()
    run = StartIngestionRun(repository).execute(DatasetId("accommodation_foreign_guest_nights"))

    updated_run = RequireReconciliation(repository).execute(
        run.run_id,
        "Write outcome uncertain.",
    )

    assert repository.get_by_id(run.run_id) is updated_run


def test_require_reconciliation_raises_when_run_does_not_exist() -> None:
    repository = InMemoryIngestionRunRepository()

    with pytest.raises(IngestionRunNotFoundError):
        RequireReconciliation(repository).execute(
            UUID(int=0),
            "Write outcome uncertain.",
        )


def test_require_reconciliation_rejects_pending_run() -> None:
    repository = InMemoryIngestionRunRepository()
    run = IngestionRun(dataset_id=DatasetId("accommodation_foreign_guest_nights"))
    repository.save(run)

    with pytest.raises(ValueError):
        RequireReconciliation(repository).execute(
            run.run_id,
            "Write outcome uncertain.",
        )

    assert run.status == IngestionStatus.PENDING


def test_require_reconciliation_rejects_empty_reason() -> None:
    repository = InMemoryIngestionRunRepository()
    run = StartIngestionRun(repository).execute(DatasetId("accommodation_foreign_guest_nights"))

    with pytest.raises(ValueError):
        RequireReconciliation(repository).execute(run.run_id, "  ")

    assert run.status == IngestionStatus.RUNNING
