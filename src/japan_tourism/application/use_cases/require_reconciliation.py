from uuid import UUID

from japan_tourism.application.exceptions import IngestionRunNotFoundError
from japan_tourism.application.ports.ingestion_run_repository import (
    IngestionRunRepository,
)
from japan_tourism.domain.models.ingestion_run import IngestionRun


class RequireReconciliation:
    """Use case for marking an ingestion run as requiring reconciliation."""

    def __init__(self, repository: IngestionRunRepository) -> None:
        self._repository = repository

    def execute(self, run_id: UUID, reason: str) -> IngestionRun:
        """Mark a run as requiring reconciliation and persist it."""
        run = self._repository.get_by_id(run_id)

        if run is None:
            raise IngestionRunNotFoundError(str(run_id))

        run.require_reconciliation(reason)
        self._repository.save(run)

        return run
