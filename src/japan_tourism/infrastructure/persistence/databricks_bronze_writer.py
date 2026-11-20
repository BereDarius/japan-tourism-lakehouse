from collections.abc import Sequence

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from japan_tourism.application.models.bronze_record import BronzeRecord
from japan_tourism.application.ports.bronze_writer import BronzeWriter


class DatabricksBronzeWriter(BronzeWriter):
    """Persists Bronze records to a managed Delta table."""

    def __init__(
        self,
        spark: SparkSession,
        table_name: str,
    ) -> None:
        self._spark = spark
        self._table_name = table_name

    @staticmethod
    def _schema() -> StructType:
        """Return the explicit schema for Bronze records."""
        return StructType(
            [
                StructField("dataset_id", StringType(), nullable=False),
                StructField("ingestion_run_id", StringType(), nullable=False),
                StructField("artifact_acquisition_id", StringType(), nullable=False),
                StructField("artifact_sha256", StringType(), nullable=False),
                StructField("source_url", StringType(), nullable=False),
                StructField("retrieved_at", TimestampType(), nullable=False),
                StructField("worksheet_name", StringType(), nullable=False),
                StructField("source_row_number", IntegerType(), nullable=False),
                StructField("title", StringType(), nullable=False),
                StructField("unit", StringType(), nullable=False),
                StructField("reporting_year", IntegerType(), nullable=False),
                StructField("column_headers_json", StringType(), nullable=False),
                StructField("row_data_json", StringType(), nullable=False),
            ]
        )

    @staticmethod
    def _to_row(record: BronzeRecord) -> tuple[object, ...]:
        """Convert a domain-facing application record into Spark row values."""
        return (
            record.dataset_id.value,
            str(record.ingestion_run_id),
            str(record.artifact_acquisition_id),
            record.artifact_sha256,
            record.source_url,
            record.retrieved_at,
            record.worksheet_name,
            record.source_row_number,
            record.title,
            record.unit,
            record.reporting_year,
            record.column_headers_json,
            record.row_data_json,
        )

    def write(self, records: Sequence[BronzeRecord]) -> None:
        """Append records to the configured Delta table."""
        if not records:
            return

        rows = [self._to_row(record) for record in records]

        dataframe = self._spark.createDataFrame(
            rows,
            schema=self._schema(),
        )

        (dataframe.write.format("delta").mode("append").saveAsTable(self._table_name))
