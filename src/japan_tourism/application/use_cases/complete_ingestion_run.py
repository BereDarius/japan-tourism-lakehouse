from uuid import UUID

from japan_tourism.application.exceptions import IngestionRunNotFoundError
from japan_tourism.application.ports.ingestion_run_repository import (
    IngestionRunRepository,
)
from japan_tourism.domain.models.ingestion_run import IngestionRun


class CompleteIngestionRun:
    """Use case for successfully completing an ingestion run."""

    def __init__(self, repository: IngestionRunRepository) -> None:
        self._repository = repository

    def execute(self, run_id: UUID) -> IngestionRun:
        """Complete and persist an existing ingestion run."""
        run = self._repository.get_by_id(run_id)

        if run is None:
            raise IngestionRunNotFoundError(str(run_id))

        run.succeed()
        self._repository.save(run)

        return run
