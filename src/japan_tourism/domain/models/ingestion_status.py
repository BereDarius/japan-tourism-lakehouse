from enum import StrEnum


class IngestionStatus(StrEnum):
    """Lifecycle statuses for a dataset ingestion run."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
