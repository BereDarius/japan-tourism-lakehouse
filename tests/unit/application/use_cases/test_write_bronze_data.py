import json
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.bronze_record import BronzeRecord
from japan_tourism.application.models.extracted_worksheet import (
    ExtractedWorksheet,
)
from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.application.use_cases.write_bronze_data import (
    WriteBronzeData,
)
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class FakeBronzeWriter:
    """Test double for the BronzeWriter port."""

    def __init__(self) -> None:
        self.written_records: Sequence[BronzeRecord] = ()

    def write(self, records: Sequence[BronzeRecord]) -> None:
        self.written_records = tuple(records)


@pytest.fixture
def writer() -> FakeBronzeWriter:
    return FakeBronzeWriter()


@pytest.fixture
def use_case(writer: FakeBronzeWriter) -> WriteBronzeData:
    return WriteBronzeData(bronze_writer=writer)


@pytest.fixture
def extracted_worksheet() -> ExtractedWorksheet:
    return ExtractedWorksheet(
        worksheet_name="3-1",
        title="都道府県別 外国人延べ宿泊者数",
        unit="（単位：人泊）",
        reporting_year=2026,
        column_headers=(None, "1月", "2月", "3月"),
        rows=(
            ("全　国", 12833880, 14037770, 14280740),
            ("01北海道", 1620430, 1685150, 1034080),
        ),
    )


@pytest.fixture
def artifact_acquisition() -> ArtifactAcquisition:
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    artifact = StoredArtifact(
        dataset_id=dataset_id,
        original_filename="002028776.xlsx",
        sha256="a" * 64,
        uri="file:///artifacts/source.xlsx",
    )

    return ArtifactAcquisition(
        acquisition_id=uuid4(),
        artifact=artifact,
        source_url="https://example.com/002028776.xlsx",
        retrieved_at=datetime(2026, 11, 20, tzinfo=UTC),
    )


@pytest.fixture
def ingestion_run_id() -> UUID:
    return uuid4()


def test_creates_and_writes_bronze_records(
    use_case: WriteBronzeData,
    writer: FakeBronzeWriter,
    extracted_worksheet: ExtractedWorksheet,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run_id: UUID,
) -> None:
    result = use_case.execute(
        extracted_worksheet=extracted_worksheet,
        artifact_acquisition=artifact_acquisition,
        ingestion_run_id=ingestion_run_id,
        data_start_row=5,
    )

    assert result == 2
    assert len(writer.written_records) == 2

    first_record = writer.written_records[0]

    assert first_record.dataset_id == artifact_acquisition.artifact.dataset_id
    assert first_record.ingestion_run_id == ingestion_run_id
    assert first_record.artifact_acquisition_id == (artifact_acquisition.acquisition_id)
    assert first_record.artifact_sha256 == artifact_acquisition.artifact.sha256
    assert first_record.source_url == artifact_acquisition.source_url
    assert first_record.retrieved_at == artifact_acquisition.retrieved_at


def test_preserves_original_excel_row_numbers(
    use_case: WriteBronzeData,
    writer: FakeBronzeWriter,
    extracted_worksheet: ExtractedWorksheet,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run_id: UUID,
) -> None:
    use_case.execute(
        extracted_worksheet,
        artifact_acquisition,
        ingestion_run_id,
        data_start_row=5,
    )

    assert writer.written_records[0].source_row_number == 5
    assert writer.written_records[1].source_row_number == 6


def test_serializes_headers_and_values_as_json(
    use_case: WriteBronzeData,
    writer: FakeBronzeWriter,
    extracted_worksheet: ExtractedWorksheet,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run_id: UUID,
) -> None:
    use_case.execute(
        extracted_worksheet,
        artifact_acquisition,
        ingestion_run_id,
        data_start_row=5,
    )

    first_record = writer.written_records[0]

    assert json.loads(first_record.column_headers_json) == [
        None,
        "1月",
        "2月",
        "3月",
    ]

    assert json.loads(first_record.row_data_json) == [
        "全　国",
        12833880,
        14037770,
        14280740,
    ]


def test_preserves_null_observations(
    use_case: WriteBronzeData,
    writer: FakeBronzeWriter,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run_id: UUID,
) -> None:
    worksheet = ExtractedWorksheet(
        worksheet_name="3-1",
        title="Foreign guest-nights",
        unit="人泊",
        reporting_year=2026,
        column_headers=(None, "1月", "2月"),
        rows=(("全　国", 1000, None),),
    )

    use_case.execute(
        worksheet,
        artifact_acquisition,
        ingestion_run_id,
        data_start_row=5,
    )

    assert json.loads(writer.written_records[0].row_data_json) == [
        "全　国",
        1000,
        None,
    ]


def test_rejects_invalid_data_start_row(
    use_case: WriteBronzeData,
    writer: FakeBronzeWriter,
    extracted_worksheet: ExtractedWorksheet,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run_id: UUID,
) -> None:
    with pytest.raises(ValueError, match="data_start_row"):
        use_case.execute(
            extracted_worksheet,
            artifact_acquisition,
            ingestion_run_id,
            data_start_row=0,
        )

    assert writer.written_records == ()


def test_rejects_empty_worksheet(
    use_case: WriteBronzeData,
    writer: FakeBronzeWriter,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run_id: UUID,
) -> None:
    worksheet = ExtractedWorksheet(
        worksheet_name="3-1",
        title="Foreign guest-nights",
        unit="人泊",
        reporting_year=2026,
        column_headers=(None, "1月"),
        rows=(),
    )

    with pytest.raises(ValueError, match="empty worksheet"):
        use_case.execute(
            worksheet,
            artifact_acquisition,
            ingestion_run_id,
            data_start_row=5,
        )

    assert writer.written_records == ()


def test_rejects_inconsistent_row_width(
    use_case: WriteBronzeData,
    writer: FakeBronzeWriter,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run_id: UUID,
) -> None:
    worksheet = ExtractedWorksheet(
        worksheet_name="3-1",
        title="Foreign guest-nights",
        unit="人泊",
        reporting_year=2026,
        column_headers=(None, "1月", "2月"),
        rows=(("全　国", 1000),),
    )

    with pytest.raises(ValueError, match="expected 3"):
        use_case.execute(
            worksheet,
            artifact_acquisition,
            ingestion_run_id,
            data_start_row=5,
        )

    assert writer.written_records == ()


def test_does_not_swallow_writer_errors(
    extracted_worksheet: ExtractedWorksheet,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run_id: UUID,
) -> None:
    class FailingBronzeWriter:
        def write(self, records: Sequence[BronzeRecord]) -> None:
            raise RuntimeError("Bronze storage unavailable.")

    use_case = WriteBronzeData(FailingBronzeWriter())

    with pytest.raises(RuntimeError, match="Bronze storage unavailable"):
        use_case.execute(
            extracted_worksheet,
            artifact_acquisition,
            ingestion_run_id,
            data_start_row=5,
        )
