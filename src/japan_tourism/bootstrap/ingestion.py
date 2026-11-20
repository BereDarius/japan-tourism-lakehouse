from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession

from japan_tourism.application.services.ingestion_engine import IngestionEngine
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
from japan_tourism.bootstrap.settings import IngestionSettings
from japan_tourism.infrastructure.artifacts.local_artifact_reader import (
    LocalArtifactReader,
)
from japan_tourism.infrastructure.artifacts.local_artifact_store import (
    LocalArtifactStore,
)
from japan_tourism.infrastructure.configuration.manifest_loader import (
    YamlManifestLoader,
)
from japan_tourism.infrastructure.configuration.yaml_dataset_manifest_repository import (
    YamlDatasetManifestRepository,
)
from japan_tourism.infrastructure.persistence.databricks_bronze_writer import (
    DatabricksBronzeWriter,
)
from japan_tourism.infrastructure.persistence.sqlite_artifact_acquisition_repository import (
    SQLiteArtifactAcquisitionRepository,
)
from japan_tourism.infrastructure.persistence.sqlite_ingestion_run_repository import (
    SQLiteIngestionRunRepository,
)
from japan_tourism.infrastructure.sources.excel_source_reader import (
    ExcelSourceReader,
)
from japan_tourism.infrastructure.sources.http_source_client import (
    HttpSourceClient,
)


def create_databricks_session(profile: str) -> SparkSession:
    """Create a Databricks Connect session using serverless compute."""
    return DatabricksSession.builder.serverless().profile(profile).getOrCreate()


def create_ingestion_engine(
    settings: IngestionSettings,
    spark: SparkSession | None = None,
) -> IngestionEngine:
    """Construct the ingestion engine and all its dependencies."""

    # Persistence adapters share one SQLite database, using separate tables.
    ingestion_run_repository = SQLiteIngestionRunRepository(settings.metadata_database)
    acquisition_repository = SQLiteArtifactAcquisitionRepository(settings.metadata_database)

    # Configuration.
    manifest_repository = YamlDatasetManifestRepository(
        manifest_directory=settings.manifest_directory,
        loader=YamlManifestLoader(),
    )

    # Source acquisition and immutable artifact storage.
    source_client = HttpSourceClient()
    artifact_store = LocalArtifactStore(settings.artifact_directory)
    artifact_reader = LocalArtifactReader(settings.artifact_directory)

    acquire_source_artifact = AcquireSourceArtifact(
        source_client=source_client,
        artifact_store=artifact_store,
        acquisition_repository=acquisition_repository,
    )

    # Source extraction.
    source_reader = ExcelSourceReader()

    # Databricks persistence.
    spark_session = (
        spark if spark is not None else create_databricks_session(settings.databricks_profile)
    )
    bronze_writer = DatabricksBronzeWriter(
        spark=spark_session,
        table_name=settings.bronze_table,
    )
    write_bronze_data = WriteBronzeData(bronze_writer)

    # Run lifecycle use cases.
    start_ingestion_run = StartIngestionRun(ingestion_run_repository)
    complete_ingestion_run = CompleteIngestionRun(ingestion_run_repository)
    fail_ingestion_run = FailIngestionRun(ingestion_run_repository)
    require_reconciliation = RequireReconciliation(ingestion_run_repository)

    return IngestionEngine(
        manifest_repository=manifest_repository,
        start_ingestion_run=start_ingestion_run,
        acquire_source_artifact=acquire_source_artifact,
        artifact_reader=artifact_reader,
        source_reader=source_reader,
        write_bronze_data=write_bronze_data,
        complete_ingestion_run=complete_ingestion_run,
        fail_ingestion_run=fail_ingestion_run,
        require_reconciliation=require_reconciliation,
    )
