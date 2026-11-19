from japan_tourism.application.ports.ingestion_run_repository import (
    IngestionRunRepository,
)
from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class StartIngestionRun:
    """Use case for creating and starting an ingestion run."""

    def __init__(self, repository: IngestionRunRepository) -> None:
        self._repository = repository

    def execute(self, dataset_id: DatasetId) -> IngestionRun:
        """Create, start, and persist an ingestion run."""
        run = IngestionRun(dataset_id=dataset_id)
        run.start()

        self._repository.save(run)

        return run
