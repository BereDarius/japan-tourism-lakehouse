from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from japan_tourism.application.models.bronze_record import BronzeRecord
from japan_tourism.domain.value_objects.dataset_id import DatasetId


@pytest.fixture
def bronze_record() -> BronzeRecord:
    return BronzeRecord(
        dataset_id=DatasetId("accommodation_foreign_guest_nights"),
        ingestion_run_id=uuid4(),
        artifact_acquisition_id=uuid4(),
        artifact_sha256="a" * 64,
        source_url="https://example.com/source.xlsx",
        retrieved_at=datetime.now(UTC),
        worksheet_name="3-1",
        source_row_number=5,
        title="Foreign guest-nights",
        unit="人泊",
        reporting_year=2026,
        column_headers_json='[null,"1月","2月"]',
        row_data_json='["全国",12833880,14037770]',
    )


def test_rejects_empty_artifact_checksum(
    bronze_record: BronzeRecord,
) -> None:
    with pytest.raises(ValueError, match="artifact_sha256"):
        replace(bronze_record, artifact_sha256="")


def test_rejects_empty_source_url(
    bronze_record: BronzeRecord,
) -> None:
    with pytest.raises(ValueError, match="source_url"):
        replace(bronze_record, source_url="")


def test_rejects_invalid_source_row_number(
    bronze_record: BronzeRecord,
) -> None:
    with pytest.raises(ValueError, match="source_row_number"):
        replace(bronze_record, source_row_number=0)


def test_rejects_invalid_reporting_year(
    bronze_record: BronzeRecord,
) -> None:
    with pytest.raises(ValueError, match="reporting_year"):
        replace(bronze_record, reporting_year=0)


def test_rejects_naive_retrieval_timestamp(
    bronze_record: BronzeRecord,
) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        replace(
            bronze_record,
            retrieved_at=datetime(2026, 1, 1),
        )
