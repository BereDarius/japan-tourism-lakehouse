from uuid import UUID

from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class InMemoryIngestionRunRepository:
    """In-memory repository intended for tests and local development.

    Stores references to mutable ingestion run objects and provides
    no durability or transaction guarantees.
    """

    def __init__(self) -> None:
        self._runs: dict[UUID, IngestionRun] = {}

    def save(self, run: IngestionRun) -> None:
        """Persist or update an ingestion run."""
        self._runs[run.run_id] = run

    def get_by_id(self, run_id: UUID) -> IngestionRun | None:
        """Retrieve an ingestion run by its unique identifier."""
        return self._runs.get(run_id)

    def get_by_dataset_id(self, dataset_id: DatasetId) -> list[IngestionRun]:
        """Retrieve all runs belonging to a dataset."""
        return [run for run in self._runs.values() if run.dataset_id == dataset_id]

    def get_by_status(self, status: IngestionStatus) -> list[IngestionRun]:
        """Retrieve all runs with a given status."""
        return [run for run in self._runs.values() if run.status == status]
