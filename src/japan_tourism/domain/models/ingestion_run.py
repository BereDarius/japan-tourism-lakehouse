from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId


@dataclass(slots=True, init=False)
class IngestionRun:
    """Represents one execution of a dataset ingestion."""

    _dataset_id: DatasetId
    _run_id: UUID
    _status: IngestionStatus
    _started_at: datetime | None
    _completed_at: datetime | None
    _error_message: str | None

    def __init__(
        self,
        dataset_id: DatasetId,
        run_id: UUID | None = None,
    ) -> None:
        self._dataset_id = dataset_id
        self._run_id = run_id if run_id is not None else uuid4()
        self._status = IngestionStatus.PENDING
        self._started_at = None
        self._completed_at = None
        self._error_message = None

    @property
    def dataset_id(self) -> DatasetId:
        return self._dataset_id

    @property
    def run_id(self) -> UUID:
        return self._run_id

    @property
    def status(self) -> IngestionStatus:
        return self._status

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def error_message(self) -> str | None:
        return self._error_message

    def start(self) -> None:
        """Transition the run from PENDING to RUNNING."""
        self._ensure_status(IngestionStatus.PENDING)

        self._status = IngestionStatus.RUNNING
        self._started_at = datetime.now(UTC)

    def succeed(self) -> None:
        """Mark a running ingestion as successfully completed."""
        self._ensure_status(IngestionStatus.RUNNING)

        self._status = IngestionStatus.SUCCEEDED
        self._completed_at = datetime.now(UTC)

    def fail(self, error_message: str) -> None:
        """Mark a running ingestion as failed."""
        self._ensure_status(IngestionStatus.RUNNING)

        if not error_message.strip():
            raise ValueError("Error message cannot be empty.")

        self._status = IngestionStatus.FAILED
        self._error_message = error_message
        self._completed_at = datetime.now(UTC)

    def require_reconciliation(self, reason: str) -> None:
        """Mark an uncertain write outcome as requiring reconciliation."""
        self._ensure_status(IngestionStatus.RUNNING)

        if not reason.strip():
            raise ValueError("Reconciliation reason cannot be empty.")

        self._status = IngestionStatus.RECONCILIATION_REQUIRED
        self._error_message = reason
        self._completed_at = datetime.now(UTC)

    def _ensure_status(self, expected: IngestionStatus) -> None:
        if self._status != expected:
            raise ValueError(f"Cannot perform this transition from status {self._status}.")
