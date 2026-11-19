from japan_tourism.domain.models.ingestion_status import IngestionStatus


def test_ingestion_status_values() -> None:
    assert IngestionStatus.PENDING == "PENDING"
    assert IngestionStatus.RUNNING == "RUNNING"
    assert IngestionStatus.SUCCEEDED == "SUCCEEDED"
    assert IngestionStatus.FAILED == "FAILED"
    assert IngestionStatus.RECONCILIATION_REQUIRED == ("RECONCILIATION_REQUIRED")
