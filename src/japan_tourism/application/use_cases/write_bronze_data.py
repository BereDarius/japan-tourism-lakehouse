import json
from uuid import UUID

from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.bronze_record import BronzeRecord
from japan_tourism.application.models.extracted_worksheet import (
    ExtractedWorksheet,
)
from japan_tourism.application.ports.bronze_writer import BronzeWriter


class WriteBronzeData:
    """Creates and persists source-shaped Bronze records."""

    def __init__(self, bronze_writer: BronzeWriter) -> None:
        self._bronze_writer = bronze_writer

    def execute(
        self,
        extracted_worksheet: ExtractedWorksheet,
        artifact_acquisition: ArtifactAcquisition,
        ingestion_run_id: UUID,
        data_start_row: int,
    ) -> int:
        """Convert an extracted worksheet into Bronze records and persist them."""
        if data_start_row < 1:
            raise ValueError("data_start_row must be positive.")

        if not extracted_worksheet.rows:
            raise ValueError("Cannot write an empty worksheet.")

        column_count = len(extracted_worksheet.column_headers)

        records: list[BronzeRecord] = []

        for index, row in enumerate(extracted_worksheet.rows):
            if len(row) != column_count:
                raise ValueError(
                    f"Row {index} contains {len(row)} values; expected {column_count}."
                )

            records.append(
                BronzeRecord(
                    dataset_id=artifact_acquisition.artifact.dataset_id,
                    ingestion_run_id=ingestion_run_id,
                    artifact_acquisition_id=(artifact_acquisition.acquisition_id),
                    artifact_sha256=artifact_acquisition.artifact.sha256,
                    source_url=artifact_acquisition.source_url,
                    retrieved_at=artifact_acquisition.retrieved_at,
                    worksheet_name=extracted_worksheet.worksheet_name,
                    source_row_number=data_start_row + index,
                    title=extracted_worksheet.title,
                    unit=extracted_worksheet.unit,
                    reporting_year=extracted_worksheet.reporting_year,
                    column_headers_json=json.dumps(
                        extracted_worksheet.column_headers,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        allow_nan=False,
                    ),
                    row_data_json=json.dumps(
                        row,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        allow_nan=False,
                    ),
                )
            )

        self._bronze_writer.write(records)

        return len(records)
