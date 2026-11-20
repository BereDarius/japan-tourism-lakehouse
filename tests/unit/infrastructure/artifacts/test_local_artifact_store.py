import hashlib
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import pytest

from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.artifacts.local_artifact_store import (
    ArtifactIntegrityError,
    LocalArtifactStore,
)


@pytest.fixture
def artifact_store(tmp_path: Path) -> LocalArtifactStore:
    return LocalArtifactStore(tmp_path)


@pytest.fixture
def dataset_id() -> DatasetId:
    return DatasetId("accommodation_foreign_guest_nights")


def test_store_preserves_original_bytes(
    artifact_store: LocalArtifactStore,
    dataset_id: DatasetId,
    tmp_path: Path,
) -> None:
    content = b"original workbook content"

    result = artifact_store.store(
        dataset_id,
        BytesIO(content),
        "source.xlsx",
    )

    artifact_path = tmp_path / dataset_id.value / result.sha256 / "artifact"

    assert artifact_path.read_bytes() == content
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert result.original_filename == "source.xlsx"
    assert result.uri == artifact_path.resolve().as_uri()


def test_identical_content_is_idempotent(
    artifact_store: LocalArtifactStore,
    dataset_id: DatasetId,
) -> None:
    content = b"same workbook content"

    first = artifact_store.store(dataset_id, BytesIO(content), "first.xlsx")
    second = artifact_store.store(dataset_id, BytesIO(content), "second.xlsx")

    assert first.sha256 == second.sha256
    assert first.uri == second.uri
    assert first.original_filename != second.original_filename


def test_different_content_creates_separate_artifacts(
    artifact_store: LocalArtifactStore,
    dataset_id: DatasetId,
) -> None:
    first = artifact_store.store(dataset_id, BytesIO(b"version one"), "source.xlsx")
    second = artifact_store.store(dataset_id, BytesIO(b"version two"), "source.xlsx")

    assert first.sha256 != second.sha256
    assert first.uri != second.uri


def test_existing_artifact_is_never_overwritten(
    artifact_store: LocalArtifactStore,
    dataset_id: DatasetId,
    tmp_path: Path,
) -> None:
    content = b"original content"
    checksum = hashlib.sha256(content).hexdigest()

    artifact_path = tmp_path / dataset_id.value / checksum / "artifact"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"corrupted existing content")

    with pytest.raises(ArtifactIntegrityError):
        artifact_store.store(
            dataset_id,
            BytesIO(content),
            "source.xlsx",
        )

    assert artifact_path.read_bytes() == b"corrupted existing content"


def test_empty_artifact_is_rejected(
    artifact_store: LocalArtifactStore,
    dataset_id: DatasetId,
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="empty artifact"):
        artifact_store.store(
            dataset_id,
            BytesIO(b""),
            "empty.xlsx",
        )

    temporary_files = list(tmp_path.rglob(".artifact-*.tmp"))
    assert temporary_files == []


def test_invalid_filename_is_rejected(
    artifact_store: LocalArtifactStore,
    dataset_id: DatasetId,
) -> None:
    with pytest.raises(ValueError, match="Invalid"):
        artifact_store.store(
            dataset_id,
            BytesIO(b"content"),
            "../source.xlsx",
        )


def test_temporary_file_is_removed_after_read_failure(
    artifact_store: LocalArtifactStore,
    dataset_id: DatasetId,
    tmp_path: Path,
) -> None:
    class FailingStream(BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            if self.tell() > 0:
                raise OSError("Simulated source read failure")

            return super().read(size)

    with pytest.raises(OSError, match="Simulated source read failure"):
        artifact_store.store(
            dataset_id,
            FailingStream(b"partial content"),
            "source.xlsx",
        )

    temporary_files = list(tmp_path.rglob(".artifact-*.tmp"))
    published_artifacts = list(tmp_path.rglob("artifact"))

    assert temporary_files == []
    assert published_artifacts == []


def test_concurrent_identical_writes_are_idempotent(
    artifact_store: LocalArtifactStore,
    dataset_id: DatasetId,
    tmp_path: Path,
) -> None:
    content = b"concurrent workbook content"

    def store_content() -> str:
        result = artifact_store.store(
            dataset_id,
            BytesIO(content),
            "source.xlsx",
        )
        return result.uri

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(store_content) for _ in range(8)]
        uris = [future.result() for future in futures]

    assert len(set(uris)) == 1

    published_artifacts = list(tmp_path.rglob("artifact"))
    assert len(published_artifacts) == 1
    assert published_artifacts[0].read_bytes() == content
