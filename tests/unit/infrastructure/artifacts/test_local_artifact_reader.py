import hashlib
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.artifacts.local_artifact_reader import (
    InvalidArtifactUriError,
    LocalArtifactReader,
)
from japan_tourism.infrastructure.artifacts.local_artifact_store import (
    ArtifactIntegrityError,
    LocalArtifactStore,
)

DATASET_ID = DatasetId("accommodation_foreign_guest_nights")
ARTIFACT_CONTENT = b"Japan Tourism Agency source workbook"


@pytest.fixture
def artifact_store(tmp_path: Path) -> LocalArtifactStore:
    return LocalArtifactStore(tmp_path)


@pytest.fixture
def stored_artifact(artifact_store: LocalArtifactStore) -> StoredArtifact:
    return artifact_store.store(
        dataset_id=DATASET_ID,
        source=BytesIO(ARTIFACT_CONTENT),
        original_filename="source.xlsx",
    )


@pytest.fixture
def artifact_reader(tmp_path: Path) -> LocalArtifactReader:
    return LocalArtifactReader(tmp_path)


def test_reads_preserved_artifact(
    artifact_reader: LocalArtifactReader,
    stored_artifact: StoredArtifact,
) -> None:
    with artifact_reader.open(stored_artifact) as stream:
        assert stream.read() == ARTIFACT_CONTENT


def test_returns_stream_positioned_at_start(
    artifact_reader: LocalArtifactReader,
    stored_artifact: StoredArtifact,
) -> None:
    with artifact_reader.open(stored_artifact) as stream:
        assert stream.tell() == 0


def test_closes_stream_after_context_exits(
    artifact_reader: LocalArtifactReader,
    stored_artifact: StoredArtifact,
) -> None:
    with artifact_reader.open(stored_artifact) as stream:
        assert not stream.closed

    assert stream.closed


def test_rejects_artifact_with_checksum_mismatch(
    artifact_reader: LocalArtifactReader,
    stored_artifact: StoredArtifact,
) -> None:
    artifact_path = Path(unquote(urlsplit(stored_artifact.uri).path))
    artifact_path.write_bytes(b"Modified artifact content")

    with pytest.raises(ArtifactIntegrityError, match="checksum mismatch"):
        with artifact_reader.open(stored_artifact):
            pass


def test_rejects_non_file_uri(
    artifact_reader: LocalArtifactReader,
    stored_artifact: StoredArtifact,
) -> None:
    invalid_artifact = StoredArtifact(
        dataset_id=stored_artifact.dataset_id,
        original_filename=stored_artifact.original_filename,
        sha256=stored_artifact.sha256,
        uri="https://example.com/artifact",
    )

    with pytest.raises(InvalidArtifactUriError, match="local file URI"):
        with artifact_reader.open(invalid_artifact):
            pass


def test_rejects_artifact_outside_expected_dataset_directory(
    artifact_reader: LocalArtifactReader,
    artifact_store: LocalArtifactStore,
) -> None:
    other_artifact = artifact_store.store(
        dataset_id=DatasetId("another_dataset"),
        source=BytesIO(ARTIFACT_CONTENT),
        original_filename="source.xlsx",
    )

    mismatched_artifact = StoredArtifact(
        dataset_id=DATASET_ID,
        original_filename=other_artifact.original_filename,
        sha256=other_artifact.sha256,
        uri=other_artifact.uri,
    )

    with pytest.raises(InvalidArtifactUriError, match="does not match"):
        with artifact_reader.open(mismatched_artifact):
            pass


def test_raises_when_artifact_does_not_exist(
    artifact_reader: LocalArtifactReader,
    stored_artifact: StoredArtifact,
) -> None:
    artifact_path = Path(unquote(urlsplit(stored_artifact.uri).path))
    artifact_path.unlink()

    with pytest.raises(FileNotFoundError):
        with artifact_reader.open(stored_artifact):
            pass


def test_rejects_artifact_symlink_pointing_outside_store(tmp_path: Path) -> None:
    # Arrange
    root_directory = tmp_path / "artifacts"
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    artifact_content = b"valid artifact content"
    external_file = tmp_path / "external.xlsx"
    external_file.write_bytes(artifact_content)

    sha256 = hashlib.sha256(artifact_content).hexdigest()

    expected_directory = root_directory / dataset_id.value / sha256
    expected_directory.mkdir(parents=True)

    artifact_path = expected_directory / "artifact"
    artifact_path.symlink_to(external_file)

    artifact = StoredArtifact(
        dataset_id=dataset_id,
        original_filename="source.xlsx",
        sha256=sha256,
        uri=artifact_path.as_uri(),
    )

    reader = LocalArtifactReader(root_directory)

    # Act & Assert
    with pytest.raises(InvalidArtifactUriError, match="does not match"):
        with reader.open(artifact):
            pytest.fail("The reader must reject the external symlink.")
