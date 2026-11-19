from typing import Protocol
from uuid import UUID

from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class IngestionRunRepository(Protocol):
    """Port for persisting and querying ingestion runs."""

    def save(self, run: IngestionRun) -> None:
        """Persist an ingestion run."""
        ...

    def get_by_id(self, run_id: UUID) -> IngestionRun | None:
        """Retrieve an ingestion run by its unique identifier."""
        ...

    def get_by_dataset_id(self, dataset_id: DatasetId) -> list[IngestionRun]:
        """Retrieve all runs belonging to a dataset."""
        ...

    def get_by_status(self, status: IngestionStatus) -> list[IngestionRun]:
        """Retrieve all runs with a given status."""
        ...
