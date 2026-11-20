from contextlib import nullcontext
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from japan_tourism.application.exceptions import BronzeWriteOutcomeUnknownError
from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.dataset_manifest import (
    DatasetManifest,
    ExcelLayout,
    ExcelReaderConfig,
)
from japan_tourism.application.models.extracted_worksheet import (
    ExtractedWorksheet,
)
from japan_tourism.application.models.ingestion_result import IngestionResult
from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.application.services.ingestion_engine import IngestionEngine
from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId

DATASET_ID = DatasetId("accommodation_foreign_guest_nights")
SOURCE_URL = "https://example.com/source.xlsx"
PUBLICATION_STAGE = "preliminary"

RUN_ID = uuid4()
ACQUISITION_ID = uuid4()
RETRIEVED_AT = datetime(2026, 11, 20, 10, 1, tzinfo=UTC)


@pytest.fixture
def manifest() -> DatasetManifest:
    return DatasetManifest(
        dataset_id=DATASET_ID,
        reader=ExcelReaderConfig(
            worksheet="3-1",
            layout=ExcelLayout(
                title_row=1,
                unit_row=2,
                reporting_year_row=3,
                month_header_row=4,
                data_start_row=5,
                expected_data_rows=48,
            ),
        ),
    )


@pytest.fixture
def artifact_acquisition() -> ArtifactAcquisition:
    return ArtifactAcquisition(
        acquisition_id=ACQUISITION_ID,
        artifact=StoredArtifact(
            dataset_id=DATASET_ID,
            original_filename="source.xlsx",
            sha256="a" * 64,
            uri="file:///tmp/source.xlsx",
        ),
        source_url=SOURCE_URL,
        retrieved_at=RETRIEVED_AT,
        publication_stage=PUBLICATION_STAGE,
    )


@pytest.fixture
def extracted_worksheet() -> ExtractedWorksheet:
    return ExtractedWorksheet(
        worksheet_name="3-1",
        title="Monthly foreign guest-nights",
        unit="人泊",
        reporting_year=2026,
        column_headers=(None, "1月", "2月"),
        rows=(
            ("全国", 12833880, 14037770),
            ("北海道", 500000, 550000),
        ),
    )


@pytest.fixture
def ingestion_run() -> IngestionRun:
    run = IngestionRun(dataset_id=DATASET_ID, run_id=RUN_ID)
    run.start()
    return run


@pytest.fixture
def dependencies() -> dict[str, MagicMock]:
    return {
        "manifest_repository": MagicMock(),
        "start_ingestion_run": MagicMock(),
        "acquire_source_artifact": MagicMock(),
        "artifact_reader": MagicMock(),
        "source_reader": MagicMock(),
        "write_bronze_data": MagicMock(),
        "complete_ingestion_run": MagicMock(),
        "fail_ingestion_run": MagicMock(),
        "require_reconciliation": MagicMock(),
    }


@pytest.fixture
def engine(dependencies: dict[str, MagicMock]) -> IngestionEngine:
    return IngestionEngine(**dependencies)


def test_successful_execution(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    artifact_acquisition: ArtifactAcquisition,
    extracted_worksheet: ExtractedWorksheet,
    ingestion_run: IngestionRun,
) -> None:
    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.return_value = artifact_acquisition
    source_stream = BytesIO(b"workbook")
    dependencies["artifact_reader"].open.return_value = nullcontext(source_stream)
    dependencies["source_reader"].read.return_value = extracted_worksheet
    dependencies["write_bronze_data"].execute.return_value = 48

    def complete_run(run_id: UUID) -> IngestionRun:
        assert run_id == RUN_ID
        ingestion_run.succeed()
        return ingestion_run

    dependencies["complete_ingestion_run"].execute.side_effect = complete_run

    result = engine.execute(
        dataset_id=DATASET_ID,
        source_url=SOURCE_URL,
        publication_stage=PUBLICATION_STAGE,
    )

    assert isinstance(result, IngestionResult)
    assert result.dataset_id == DATASET_ID
    assert result.run_id == RUN_ID
    assert result.status == IngestionStatus.SUCCEEDED
    assert result.started_at.tzinfo is not None
    assert result.completed_at.tzinfo is not None
    assert result.completed_at >= result.started_at
    assert result.artifact_acquisition == artifact_acquisition
    assert result.bronze_records_written == 48
    assert result.error_message is None

    dependencies["manifest_repository"].get.assert_called_once_with(DATASET_ID)
    dependencies["start_ingestion_run"].execute.assert_called_once_with(DATASET_ID)

    dependencies["acquire_source_artifact"].execute.assert_called_once_with(
        source_url=SOURCE_URL,
        dataset_id=DATASET_ID,
        publication_stage=PUBLICATION_STAGE,
    )

    dependencies["artifact_reader"].open.assert_called_once_with(artifact_acquisition.artifact)

    dependencies["source_reader"].read.assert_called_once_with(
        source=source_stream,
        config=manifest.reader,
    )

    dependencies["write_bronze_data"].execute.assert_called_once_with(
        extracted_worksheet=extracted_worksheet,
        artifact_acquisition=artifact_acquisition,
        ingestion_run_id=RUN_ID,
        data_start_row=5,
    )

    dependencies["complete_ingestion_run"].execute.assert_called_once_with(RUN_ID)
    dependencies["fail_ingestion_run"].execute.assert_not_called()
    dependencies["require_reconciliation"].execute.assert_not_called()


def test_manifest_failure_does_not_start_run(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
) -> None:
    error = ValueError("Manifest not found")
    dependencies["manifest_repository"].get.side_effect = error

    with pytest.raises(ValueError, match="Manifest not found"):
        engine.execute(DATASET_ID, SOURCE_URL)

    dependencies["start_ingestion_run"].execute.assert_not_called()


def test_artifact_acquisition_failure_marks_run_failed(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    ingestion_run: IngestionRun,
) -> None:
    error = RuntimeError("Source download failed")

    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.side_effect = error

    def fail_run(run_id: UUID, message: str) -> IngestionRun:
        assert run_id == RUN_ID
        ingestion_run.fail(message)
        return ingestion_run

    dependencies["fail_ingestion_run"].execute.side_effect = fail_run

    result = engine.execute(DATASET_ID, SOURCE_URL)

    assert result.status == IngestionStatus.FAILED
    assert result.artifact_acquisition is None
    assert result.bronze_records_written == 0
    assert result.error_message == str(error)
    dependencies["fail_ingestion_run"].execute.assert_called_once()
    dependencies["require_reconciliation"].execute.assert_not_called()


def test_artifact_read_failure_marks_run_failed(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run: IngestionRun,
) -> None:
    error = OSError("Artifact checksum verification failed")

    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.return_value = artifact_acquisition
    dependencies["artifact_reader"].open.side_effect = error

    def fail_run(run_id: UUID, message: str) -> IngestionRun:
        assert run_id == RUN_ID
        ingestion_run.fail(message)
        return ingestion_run

    dependencies["fail_ingestion_run"].execute.side_effect = fail_run

    result = engine.execute(DATASET_ID, SOURCE_URL)

    assert result.status == IngestionStatus.FAILED
    assert result.artifact_acquisition == artifact_acquisition
    assert result.bronze_records_written == 0
    assert result.error_message == str(error)
    dependencies["source_reader"].read.assert_not_called()
    dependencies["write_bronze_data"].execute.assert_not_called()


def test_extraction_failure_marks_run_failed(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run: IngestionRun,
) -> None:
    error = ValueError("Invalid worksheet structure")

    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.return_value = artifact_acquisition
    source_stream = BytesIO(b"workbook")
    dependencies["artifact_reader"].open.return_value = nullcontext(source_stream)
    dependencies["source_reader"].read.side_effect = error

    def fail_run(run_id: UUID, message: str) -> IngestionRun:
        assert run_id == RUN_ID
        ingestion_run.fail(message)
        return ingestion_run

    dependencies["fail_ingestion_run"].execute.side_effect = fail_run

    result = engine.execute(DATASET_ID, SOURCE_URL)

    assert result.status == IngestionStatus.FAILED
    assert result.bronze_records_written == 0
    assert result.error_message == str(error)
    dependencies["write_bronze_data"].execute.assert_not_called()


def test_bronze_preparation_failure_marks_run_failed(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run: IngestionRun,
    extracted_worksheet: ExtractedWorksheet,
) -> None:
    error = ValueError("Cannot serialize Bronze records")

    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.return_value = artifact_acquisition
    source_stream = BytesIO(b"workbook")
    dependencies["artifact_reader"].open.return_value = nullcontext(source_stream)
    dependencies["source_reader"].read.return_value = extracted_worksheet
    dependencies["write_bronze_data"].execute.side_effect = error

    def fail_run(run_id: UUID, message: str) -> IngestionRun:
        assert run_id == RUN_ID
        ingestion_run.fail(message)
        return ingestion_run

    dependencies["fail_ingestion_run"].execute.side_effect = fail_run

    result = engine.execute(DATASET_ID, SOURCE_URL)

    assert result.status == IngestionStatus.FAILED
    assert result.bronze_records_written == 0
    assert result.error_message == str(error)
    dependencies["complete_ingestion_run"].execute.assert_not_called()


def test_uncertain_bronze_write_requires_reconciliation(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run: IngestionRun,
    extracted_worksheet: ExtractedWorksheet,
) -> None:
    error = BronzeWriteOutcomeUnknownError("Delta commit outcome unknown")

    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.return_value = artifact_acquisition
    source_stream = BytesIO(b"workbook")
    dependencies["artifact_reader"].open.return_value = nullcontext(source_stream)
    dependencies["source_reader"].read.return_value = extracted_worksheet
    dependencies["write_bronze_data"].execute.side_effect = error

    def require_reconciliation(
        run_id: UUID,
        reason: str,
    ) -> IngestionRun:
        assert run_id == RUN_ID
        ingestion_run.require_reconciliation(reason)
        return ingestion_run

    dependencies["require_reconciliation"].execute.side_effect = require_reconciliation

    result = engine.execute(DATASET_ID, SOURCE_URL)

    assert result.status == IngestionStatus.RECONCILIATION_REQUIRED
    assert result.bronze_records_written is None
    assert result.error_message == str(error)
    assert result.artifact_acquisition == artifact_acquisition

    dependencies["require_reconciliation"].execute.assert_called_once_with(
        RUN_ID,
        str(error),
    )
    dependencies["fail_ingestion_run"].execute.assert_not_called()
    dependencies["complete_ingestion_run"].execute.assert_not_called()


def test_failure_tracking_error_preserves_original_error(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    ingestion_run: IngestionRun,
) -> None:
    original_error = RuntimeError("Source download failed")
    tracking_error = RuntimeError("Run repository unavailable")

    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.side_effect = original_error
    dependencies["fail_ingestion_run"].execute.side_effect = tracking_error

    with pytest.raises(RuntimeError, match="Source download failed") as exc_info:
        engine.execute(DATASET_ID, SOURCE_URL)

    assert exc_info.value is original_error
    assert exc_info.value.__cause__ is tracking_error
    assert any("failure tracking failed" in note for note in exc_info.value.__notes__)


def test_reconciliation_tracking_error_preserves_original_error(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    ingestion_run: IngestionRun,
    artifact_acquisition: ArtifactAcquisition,
    extracted_worksheet: ExtractedWorksheet,
) -> None:
    original_error = BronzeWriteOutcomeUnknownError("Delta outcome unknown")
    tracking_error = RuntimeError("Run repository unavailable")

    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.return_value = artifact_acquisition
    source_stream = BytesIO(b"workbook")
    dependencies["artifact_reader"].open.return_value = nullcontext(source_stream)
    dependencies["source_reader"].read.return_value = extracted_worksheet
    dependencies["write_bronze_data"].execute.side_effect = original_error
    dependencies["require_reconciliation"].execute.side_effect = tracking_error

    with pytest.raises(
        BronzeWriteOutcomeUnknownError,
        match="Delta outcome unknown",
    ) as exc_info:
        engine.execute(DATASET_ID, SOURCE_URL)

    assert exc_info.value is original_error
    assert exc_info.value.__cause__ is tracking_error
    assert any("failure tracking failed" in note for note in exc_info.value.__notes__)


def test_completion_failure_propagates_without_marking_run_failed(
    engine: IngestionEngine,
    dependencies: dict[str, MagicMock],
    manifest: DatasetManifest,
    artifact_acquisition: ArtifactAcquisition,
    ingestion_run: IngestionRun,
    extracted_worksheet: ExtractedWorksheet,
) -> None:
    error = RuntimeError("Run completion persistence failed")

    dependencies["manifest_repository"].get.return_value = manifest
    dependencies["start_ingestion_run"].execute.return_value = ingestion_run
    dependencies["acquire_source_artifact"].execute.return_value = artifact_acquisition
    source_stream = BytesIO(b"workbook")
    dependencies["artifact_reader"].open.return_value = nullcontext(source_stream)
    dependencies["source_reader"].read.return_value = extracted_worksheet
    dependencies["write_bronze_data"].execute.return_value = 48
    dependencies["complete_ingestion_run"].execute.side_effect = error

    with pytest.raises(
        RuntimeError,
        match="Run completion persistence failed",
    ):
        engine.execute(DATASET_ID, SOURCE_URL)

    dependencies["fail_ingestion_run"].execute.assert_not_called()
    dependencies["require_reconciliation"].execute.assert_not_called()
