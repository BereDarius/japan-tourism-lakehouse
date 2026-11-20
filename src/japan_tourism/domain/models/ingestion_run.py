from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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

    @classmethod
    def reconstitute(
        cls,
        *,
        dataset_id: DatasetId,
        run_id: UUID,
        status: object,
        started_at: datetime | None,
        completed_at: datetime | None,
        error_message: str | None,
    ) -> "IngestionRun":
        """Restore an ingestion run from persisted state."""

        if not isinstance(status, IngestionStatus):
            raise ValueError("Invalid ingestion status.")

        timestamps = (started_at, completed_at)

        for timestamp in timestamps:
            if timestamp is not None:
                if timestamp.utcoffset() is None:
                    raise ValueError("Ingestion timestamps must be timezone-aware.")

                if timestamp.utcoffset() != timedelta(0):
                    raise ValueError("Ingestion timestamps must be in UTC.")

        if status == IngestionStatus.PENDING:
            valid = started_at is None and completed_at is None and error_message is None

        elif status == IngestionStatus.RUNNING:
            valid = started_at is not None and completed_at is None and error_message is None

        elif status == IngestionStatus.SUCCEEDED:
            valid = started_at is not None and completed_at is not None and error_message is None

        else:
            valid = (
                started_at is not None
                and completed_at is not None
                and error_message is not None
                and bool(error_message.strip())
            )

        if not valid:
            raise ValueError(f"Invalid persisted state for ingestion status {status}.")

        if started_at is not None and completed_at is not None and completed_at < started_at:
            raise ValueError("Completion timestamp cannot precede start timestamp.")

        run = cls(dataset_id=dataset_id, run_id=run_id)
        run._status = status
        run._started_at = started_at
        run._completed_at = completed_at
        run._error_message = error_message

        return run

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
