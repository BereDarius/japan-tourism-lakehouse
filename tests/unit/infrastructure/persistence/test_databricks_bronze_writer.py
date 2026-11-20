from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from japan_tourism.application.exceptions import BronzeWriteOutcomeUnknownError
from japan_tourism.application.models.bronze_record import BronzeRecord
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.persistence.databricks_bronze_writer import (
    DatabricksBronzeWriter,
)


@pytest.fixture
def bronze_record() -> BronzeRecord:
    return BronzeRecord(
        dataset_id=DatasetId("accommodation_foreign_guest_nights"),
        ingestion_run_id=UUID("11111111-1111-4111-8111-111111111111"),
        artifact_acquisition_id=UUID("22222222-2222-4222-8222-222222222222"),
        artifact_sha256="a" * 64,
        source_url="https://example.com/source.xlsx",
        retrieved_at=datetime(2026, 11, 20, 10, 30, tzinfo=UTC),
        worksheet_name="3-1",
        source_row_number=5,
        title="Monthly foreign guest-nights",
        unit="人泊",
        reporting_year=2026,
        column_headers_json='[null,"1月","2月"]',
        row_data_json='["全国",12833880,14037770]',
    )


@pytest.fixture
def spark() -> MagicMock:
    return MagicMock()


@pytest.fixture
def writer(spark: MagicMock) -> DatabricksBronzeWriter:
    return DatabricksBronzeWriter(
        spark=spark,
        table_name="workspace.bronze.accommodation_foreign_guest_nights",
    )


def test_write_appends_records_to_delta_table(
    writer: DatabricksBronzeWriter,
    spark: MagicMock,
    bronze_record: BronzeRecord,
) -> None:
    writer.write([bronze_record])

    spark.createDataFrame.assert_called_once()

    dataframe = spark.createDataFrame.return_value

    dataframe.write.format.assert_called_once_with("delta")
    dataframe.write.format.return_value.mode.assert_called_once_with("append")
    (dataframe.write.format.return_value.mode.return_value.saveAsTable).assert_called_once_with(
        "workspace.bronze.accommodation_foreign_guest_nights"
    )


def test_write_passes_explicit_schema_to_spark(
    writer: DatabricksBronzeWriter,
    spark: MagicMock,
    bronze_record: BronzeRecord,
) -> None:
    writer.write([bronze_record])

    rows = spark.createDataFrame.call_args.args[0]
    schema = spark.createDataFrame.call_args.kwargs["schema"]

    assert len(schema.fields) == 13

    assert schema.fieldNames() == [
        "dataset_id",
        "ingestion_run_id",
        "artifact_acquisition_id",
        "artifact_sha256",
        "source_url",
        "retrieved_at",
        "worksheet_name",
        "source_row_number",
        "title",
        "unit",
        "reporting_year",
        "column_headers_json",
        "row_data_json",
    ]

    assert [field.dataType.simpleString() for field in schema.fields] == [
        "string",
        "string",
        "string",
        "string",
        "string",
        "timestamp",
        "string",
        "int",
        "string",
        "string",
        "int",
        "string",
        "string",
    ]

    assert rows[0] == (
        "accommodation_foreign_guest_nights",
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
        "a" * 64,
        "https://example.com/source.xlsx",
        datetime(2026, 11, 20, 10, 30, tzinfo=UTC),
        "3-1",
        5,
        "Monthly foreign guest-nights",
        "人泊",
        2026,
        '[null,"1月","2月"]',
        '["全国",12833880,14037770]',
    )


def test_empty_records_do_not_create_dataframe(
    writer: DatabricksBronzeWriter,
    spark: MagicMock,
) -> None:
    writer.write([])

    spark.createDataFrame.assert_not_called()


def test_write_failure_raises_outcome_unknown_error(
    writer: DatabricksBronzeWriter,
    spark: MagicMock,
    bronze_record: BronzeRecord,
) -> None:
    dataframe = spark.createDataFrame.return_value
    original_error = RuntimeError("Delta write failed")

    dataframe.write.format.return_value.mode.return_value.saveAsTable.side_effect = original_error

    with pytest.raises(
        BronzeWriteOutcomeUnknownError,
        match="outcome is unknown",
    ) as exc_info:
        writer.write([bronze_record])

    assert exc_info.value.__cause__ is original_error

    dataframe.write.format.return_value.mode.return_value.saveAsTable.assert_called_once()


def test_dataframe_creation_failure_is_propagated(
    writer: DatabricksBronzeWriter,
    spark: MagicMock,
    bronze_record: BronzeRecord,
) -> None:
    original_error = RuntimeError("DataFrame creation failed")
    spark.createDataFrame.side_effect = original_error

    with pytest.raises(RuntimeError, match="DataFrame creation failed") as exc_info:
        writer.write([bronze_record])

    assert exc_info.value is original_error
