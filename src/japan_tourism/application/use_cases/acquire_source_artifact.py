from datetime import UTC, datetime
from uuid import uuid4

from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.ports.artifact_acquisition_repository import (
    ArtifactAcquisitionRepository,
)
from japan_tourism.application.ports.artifact_store import ArtifactStore
from japan_tourism.application.ports.source_client import SourceClient
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class AcquireSourceArtifact:
    """Acquire, preserve, and record a source artifact."""

    def __init__(
        self,
        source_client: SourceClient,
        artifact_store: ArtifactStore,
        acquisition_repository: ArtifactAcquisitionRepository,
    ) -> None:
        self._source_client = source_client
        self._artifact_store = artifact_store
        self._acquisition_repository = acquisition_repository

    def execute(
        self,
        source_url: str,
        dataset_id: DatasetId,
        publication_stage: str | None = None,
    ) -> ArtifactAcquisition:
        """Download a source artifact, preserve it, and record provenance."""

        with self._source_client.open(source_url) as downloaded_source:
            retrieved_at = datetime.now(UTC)

            stored_artifact = self._artifact_store.store(
                dataset_id=dataset_id,
                source=downloaded_source.stream,
                original_filename=downloaded_source.original_filename,
            )

            acquisition = ArtifactAcquisition(
                acquisition_id=uuid4(),
                artifact=stored_artifact,
                source_url=downloaded_source.source_url,
                retrieved_at=retrieved_at,
                publication_stage=publication_stage,
            )

            self._acquisition_repository.save(acquisition)

        return acquisition
