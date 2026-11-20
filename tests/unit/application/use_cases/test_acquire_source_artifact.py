from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC
from io import BytesIO
from typing import BinaryIO
from uuid import UUID

import pytest

from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.downloaded_source import DownloadedSource
from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.application.use_cases.acquire_source_artifact import (
    AcquireSourceArtifact,
)
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class FakeSourceClient:
    def __init__(
        self,
        source_url: str = "https://example.com/002028776.xlsx",
        effective_url: str = "https://cdn.example.com/002028776.xlsx",
        content: bytes = b"excel-workbook-content",
        original_filename: str = "002028776.xlsx",
    ) -> None:
        self.source_url = source_url
        self.effective_url = effective_url
        self.content = content
        self.original_filename = original_filename
        self.opened_url: str | None = None

    @contextmanager
    def open(self, source_url: str) -> Generator[DownloadedSource, None, None]:
        self.opened_url = source_url

        yield DownloadedSource(
            stream=BytesIO(self.content),
            original_filename=self.original_filename,
            source_url=self.effective_url,
        )


class FakeArtifactStore:
    def __init__(self) -> None:
        self.stored_artifacts: list[StoredArtifact] = []
        self.stored_content: list[bytes] = []
        self.should_fail = False

    def store(
        self,
        dataset_id: DatasetId,
        source: BinaryIO,
        original_filename: str,
    ) -> StoredArtifact:
        if self.should_fail:
            raise RuntimeError("Artifact storage failed.")

        content = source.read()
        self.stored_content.append(content)

        artifact = StoredArtifact(
            dataset_id=dataset_id,
            original_filename=original_filename,
            sha256="a" * 64,
            uri="file:///artifacts/test-artifact",
        )

        self.stored_artifacts.append(artifact)
        return artifact


class FakeArtifactAcquisitionRepository:
    def __init__(self) -> None:
        self.acquisitions: dict[UUID, ArtifactAcquisition] = {}
        self.should_fail = False

    def save(self, acquisition: ArtifactAcquisition) -> None:
        if self.should_fail:
            raise RuntimeError("Acquisition persistence failed.")

        if acquisition.acquisition_id in self.acquisitions:
            raise ValueError("Duplicate acquisition ID.")

        self.acquisitions[acquisition.acquisition_id] = acquisition

    def get_by_id(
        self,
        acquisition_id: UUID,
    ) -> ArtifactAcquisition | None:
        return self.acquisitions.get(acquisition_id)


@pytest.fixture
def source_client() -> FakeSourceClient:
    return FakeSourceClient()


@pytest.fixture
def artifact_store() -> FakeArtifactStore:
    return FakeArtifactStore()


@pytest.fixture
def acquisition_repository() -> FakeArtifactAcquisitionRepository:
    return FakeArtifactAcquisitionRepository()


@pytest.fixture
def use_case(
    source_client: FakeSourceClient,
    artifact_store: FakeArtifactStore,
    acquisition_repository: FakeArtifactAcquisitionRepository,
) -> AcquireSourceArtifact:
    return AcquireSourceArtifact(
        source_client=source_client,
        artifact_store=artifact_store,
        acquisition_repository=acquisition_repository,
    )


@pytest.fixture
def dataset_id() -> DatasetId:
    return DatasetId("accommodation_foreign_guest_nights")


def test_successful_acquisition(
    use_case: AcquireSourceArtifact,
    source_client: FakeSourceClient,
    artifact_store: FakeArtifactStore,
    acquisition_repository: FakeArtifactAcquisitionRepository,
    dataset_id: DatasetId,
) -> None:
    result = use_case.execute(
        source_url="https://example.com/002028776.xlsx",
        dataset_id=dataset_id,
        publication_stage="preliminary",
    )

    assert isinstance(result, ArtifactAcquisition)
    assert result.artifact == artifact_store.stored_artifacts[0]
    assert result.source_url == source_client.effective_url
    assert result.publication_stage == "preliminary"
    assert result.retrieved_at.tzinfo == UTC

    assert source_client.opened_url == source_client.source_url
    assert len(artifact_store.stored_artifacts) == 1
    assert len(acquisition_repository.acquisitions) == 1
    assert acquisition_repository.get_by_id(result.acquisition_id) == result


def test_records_effective_url_after_redirect(
    use_case: AcquireSourceArtifact,
    source_client: FakeSourceClient,
    dataset_id: DatasetId,
) -> None:
    result = use_case.execute(
        source_url="https://example.com/002028776.xlsx",
        dataset_id=dataset_id,
    )

    assert result.source_url == source_client.effective_url
    assert result.source_url != source_client.source_url


def test_does_not_save_acquisition_when_artifact_storage_fails(
    use_case: AcquireSourceArtifact,
    artifact_store: FakeArtifactStore,
    acquisition_repository: FakeArtifactAcquisitionRepository,
    dataset_id: DatasetId,
) -> None:
    artifact_store.should_fail = True

    with pytest.raises(RuntimeError, match="Artifact storage failed"):
        use_case.execute(
            source_url="https://example.com/002028776.xlsx",
            dataset_id=dataset_id,
        )

    assert len(acquisition_repository.acquisitions) == 0


def test_propagates_repository_failure_after_artifact_storage(
    use_case: AcquireSourceArtifact,
    artifact_store: FakeArtifactStore,
    acquisition_repository: FakeArtifactAcquisitionRepository,
    dataset_id: DatasetId,
) -> None:
    acquisition_repository.should_fail = True

    with pytest.raises(RuntimeError, match="Acquisition persistence failed"):
        use_case.execute(
            source_url="https://example.com/002028776.xlsx",
            dataset_id=dataset_id,
        )

    assert len(artifact_store.stored_artifacts) == 1
    assert len(acquisition_repository.acquisitions) == 0


def test_repeated_acquisition_creates_distinct_acquisition_ids(
    use_case: AcquireSourceArtifact,
    artifact_store: FakeArtifactStore,
    acquisition_repository: FakeArtifactAcquisitionRepository,
    dataset_id: DatasetId,
) -> None:
    first = use_case.execute(
        source_url="https://example.com/002028776.xlsx",
        dataset_id=dataset_id,
    )

    second = use_case.execute(
        source_url="https://example.com/002028776.xlsx",
        dataset_id=dataset_id,
    )

    assert first.acquisition_id != second.acquisition_id
    assert first.artifact == second.artifact
    assert len(artifact_store.stored_artifacts) == 2
    assert len(acquisition_repository.acquisitions) == 2


def test_preserves_original_downloaded_content(
    use_case: AcquireSourceArtifact,
    artifact_store: FakeArtifactStore,
    dataset_id: DatasetId,
) -> None:
    use_case.execute(
        source_url="https://example.com/002028776.xlsx",
        dataset_id=dataset_id,
    )

    assert artifact_store.stored_content == [b"excel-workbook-content"]


def test_allows_missing_publication_stage(
    use_case: AcquireSourceArtifact,
    dataset_id: DatasetId,
) -> None:
    result = use_case.execute(
        source_url="https://example.com/002028776.xlsx",
        dataset_id=dataset_id,
    )

    assert result.publication_stage is None
