import os
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Protocol, cast
from uuid import UUID, uuid4

import pytest
from databricks.connect import DatabricksSession
from pyspark.sql import DataFrame, SparkSession

from japan_tourism.application.models.bronze_record import BronzeRecord
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.persistence.databricks_bronze_writer import (
    DatabricksBronzeWriter,
)

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABRICKS_INTEGRATION") != "1",
    reason="Databricks integration tests are opt-in.",
)


class SparkSqlExecutor(Protocol):
    """Minimal typed interface for executing Spark SQL statements."""

    def sql(self, sql_query: str) -> DataFrame: ...


def execute_spark_sql(
    spark: SparkSession,
    statement: str,
) -> DataFrame:
    """Execute SQL through a typed Databricks Connect boundary."""
    executor = cast(SparkSqlExecutor, spark)
    return executor.sql(statement)


@pytest.fixture(scope="module")
def spark() -> Generator[SparkSession, None, None]:
    """Create a Databricks Connect session for integration testing."""
    profile = os.getenv("DATABRICKS_CONFIG_PROFILE", "JAPAN_TOURISM")

    session = DatabricksSession.builder.serverless().profile(profile).getOrCreate()

    try:
        yield session
    finally:
        session.stop()


def create_bronze_record(
    source_row_number: int,
    row_data_json: str,
) -> BronzeRecord:
    """Create a representative Bronze record for integration testing."""
    return BronzeRecord(
        dataset_id=DatasetId("accommodation_foreign_guest_nights"),
        ingestion_run_id=UUID("11111111-1111-4111-8111-111111111111"),
        artifact_acquisition_id=UUID("22222222-2222-4222-8222-222222222222"),
        artifact_sha256="a" * 64,
        source_url="https://example.com/source.xlsx",
        retrieved_at=datetime(2026, 11, 20, 10, 30, tzinfo=UTC),
        worksheet_name="3-1",
        source_row_number=source_row_number,
        title="Monthly foreign guest-nights",
        unit="人泊",
        reporting_year=2026,
        column_headers_json='[null,"1月","2月"]',
        row_data_json=row_data_json,
    )


def test_databricks_bronze_writer_persists_and_appends(
    spark: SparkSession,
) -> None:
    """Verify managed Delta table creation, persistence, and append behavior."""
    table_name = f"workspace.bronze.integration_test_bronze_writer_{uuid4().hex}"

    writer = DatabricksBronzeWriter(
        spark=spark,
        table_name=table_name,
    )

    first_record = create_bronze_record(
        source_row_number=5,
        row_data_json='["全国",12833880,14037770]',
    )

    second_record = create_bronze_record(
        source_row_number=6,
        row_data_json='["北海道",120000,130000]',
    )

    try:
        # First write: create the managed Delta table.
        writer.write([first_record])

        # Second write: append another record.
        writer.write([second_record])

        # Read persisted records.
        rows = spark.table(table_name).orderBy("source_row_number").collect()

        assert len(rows) == 2

        first_row, second_row = rows

        assert first_row["dataset_id"] == "accommodation_foreign_guest_nights"
        assert first_row["source_row_number"] == 5
        assert first_row["worksheet_name"] == "3-1"
        assert first_row["unit"] == "人泊"
        assert first_row["row_data_json"] == '["全国",12833880,14037770]'

        assert second_row["source_row_number"] == 6
        assert second_row["row_data_json"] == '["北海道",120000,130000]'

        # Verify UUID serialization.
        assert first_row["ingestion_run_id"] == ("11111111-1111-4111-8111-111111111111")

        # Verify timestamp preservation as an instant.
        timestamp_rows = (
            spark.table(table_name)
            .selectExpr("unix_micros(retrieved_at) AS retrieved_at_micros")
            .collect()
        )

        expected_timestamp_micros = int(first_record.retrieved_at.timestamp() * 1_000_000)

        assert all(
            row["retrieved_at_micros"] == expected_timestamp_micros for row in timestamp_rows
        )

        # Verify that the table is actually stored as Delta.
        details = execute_spark_sql(
            spark,
            f"DESCRIBE DETAIL {table_name}",
        ).first()

        assert details is not None
        assert details["format"] == "delta"

    finally:
        # Never leave temporary integration-test tables behind.
        execute_spark_sql(
            spark,
            f"DROP TABLE IF EXISTS {table_name}",
        )
