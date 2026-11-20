from uuid import UUID

from japan_tourism.application.exceptions import BronzeWriteOutcomeUnknownError
from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.ingestion_result import IngestionResult
from japan_tourism.application.ports.artifact_reader import ArtifactReader
from japan_tourism.application.ports.dataset_manifest_repository import (
    DatasetManifestRepository,
)
from japan_tourism.application.ports.source_reader import SourceReader
from japan_tourism.application.use_cases.acquire_source_artifact import (
    AcquireSourceArtifact,
)
from japan_tourism.application.use_cases.complete_ingestion_run import (
    CompleteIngestionRun,
)
from japan_tourism.application.use_cases.fail_ingestion_run import (
    FailIngestionRun,
)
from japan_tourism.application.use_cases.require_reconciliation import (
    RequireReconciliation,
)
from japan_tourism.application.use_cases.start_ingestion_run import (
    StartIngestionRun,
)
from japan_tourism.application.use_cases.write_bronze_data import (
    WriteBronzeData,
)
from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class IngestionEngine:
    """Orchestrates the ingestion lifecycle for a single dataset."""

    def __init__(
        self,
        manifest_repository: DatasetManifestRepository,
        start_ingestion_run: StartIngestionRun,
        acquire_source_artifact: AcquireSourceArtifact,
        artifact_reader: ArtifactReader,
        source_reader: SourceReader,
        write_bronze_data: WriteBronzeData,
        complete_ingestion_run: CompleteIngestionRun,
        fail_ingestion_run: FailIngestionRun,
        require_reconciliation: RequireReconciliation,
    ) -> None:
        self._manifest_repository = manifest_repository
        self._start_ingestion_run = start_ingestion_run
        self._acquire_source_artifact = acquire_source_artifact
        self._artifact_reader = artifact_reader
        self._source_reader = source_reader
        self._write_bronze_data = write_bronze_data
        self._complete_ingestion_run = complete_ingestion_run
        self._fail_ingestion_run = fail_ingestion_run
        self._require_reconciliation = require_reconciliation

    def execute(
        self,
        dataset_id: DatasetId,
        source_url: str,
        publication_stage: str | None = None,
    ) -> IngestionResult:
        """Execute ingestion for a single dataset."""

        # 1. Load the dataset manifest before creating a run.
        manifest = self._manifest_repository.get(dataset_id)

        # 2. Start the ingestion run.
        run = self._start_ingestion_run.execute(dataset_id)

        acquisition: ArtifactAcquisition | None = None

        try:
            # 3. Acquire and preserve the source artifact.
            acquisition = self._acquire_source_artifact.execute(
                source_url=source_url,
                dataset_id=dataset_id,
                publication_stage=publication_stage,
            )

            # 4. Reopen the preserved artifact and extract the worksheet.
            with self._artifact_reader.open(acquisition.artifact) as source:
                extracted_worksheet = self._source_reader.read(
                    source=source,
                    config=manifest.reader,
                )

            # 5. Convert extracted data into Bronze records and persist them.
            records_written = self._write_bronze_data.execute(
                extracted_worksheet=extracted_worksheet,
                artifact_acquisition=acquisition,
                ingestion_run_id=run.run_id,
                data_start_row=manifest.reader.layout.data_start_row,
            )

        except BronzeWriteOutcomeUnknownError as exc:
            return self._handle_failure(
                run_id=run.run_id,
                error=exc,
                acquisition=acquisition,
                reconciliation_required=True,
            )

        except Exception as exc:
            return self._handle_failure(
                run_id=run.run_id,
                error=exc,
                acquisition=acquisition,
                reconciliation_required=False,
            )

        # 6. Mark the ingestion run as successfully completed.
        # Deliberately outside the try block: Bronze has already been written.
        completed_run = self._complete_ingestion_run.execute(run.run_id)

        # 7. Build the successful execution result.
        return self._build_result(
            run=completed_run,
            acquisition=acquisition,
            records_written=records_written,
            error_message=None,
        )

    def _handle_failure(
        self,
        run_id: UUID,
        error: Exception,
        acquisition: ArtifactAcquisition | None,
        reconciliation_required: bool,
    ) -> IngestionResult:
        """Record a failure while preserving the original exception."""

        try:
            if reconciliation_required:
                run = self._require_reconciliation.execute(
                    run_id,
                    str(error) or type(error).__name__,
                )
                records_written = None
            else:
                run = self._fail_ingestion_run.execute(
                    run_id,
                    str(error) or type(error).__name__,
                )
                records_written = 0

        except Exception as tracking_error:
            error.add_note(f"Additionally, ingestion failure tracking failed: {tracking_error}")
            raise error from tracking_error

        return self._build_result(
            run=run,
            acquisition=acquisition,
            records_written=records_written,
            error_message=str(error) or type(error).__name__,
        )

    @staticmethod
    def _build_result(
        run: IngestionRun,
        acquisition: ArtifactAcquisition | None,
        records_written: int | None,
        error_message: str | None,
    ) -> IngestionResult:
        """Construct a result from a terminal ingestion run."""

        if run.started_at is None:
            raise RuntimeError("Terminal ingestion run has no start timestamp.")

        if run.completed_at is None:
            raise RuntimeError("Terminal ingestion run has no completion timestamp.")

        return IngestionResult(
            dataset_id=run.dataset_id,
            run_id=run.run_id,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            artifact_acquisition=acquisition,
            bronze_records_written=records_written,
            error_message=error_message,
        )
