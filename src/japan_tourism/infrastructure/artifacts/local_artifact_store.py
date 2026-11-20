import hashlib
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.application.ports.artifact_store import ArtifactStore
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class ArtifactIntegrityError(RuntimeError):
    """Raised when an existing stored artifact fails integrity verification."""


class LocalArtifactStore(ArtifactStore):
    """Filesystem-backed immutable storage for source artifacts."""

    CHUNK_SIZE = 1024 * 1024

    def __init__(self, root_directory: Path) -> None:
        self._root_directory = root_directory

    def store(
        self,
        dataset_id: DatasetId,
        source: BinaryIO,
        original_filename: str,
    ) -> StoredArtifact:
        """Preserve an artifact using its SHA-256 checksum as its identity."""
        self._validate_filename(original_filename)

        dataset_directory = self._root_directory / dataset_id.value
        dataset_directory.mkdir(parents=True, exist_ok=True)

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=".artifact-",
                suffix=".tmp",
                dir=dataset_directory,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                checksum = hashlib.sha256()
                bytes_written = 0

                while chunk := source.read(self.CHUNK_SIZE):
                    temporary_file.write(chunk)
                    checksum.update(chunk)
                    bytes_written += len(chunk)

                if bytes_written == 0:
                    raise ValueError("Cannot store an empty artifact.")

                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            sha256 = checksum.hexdigest()
            artifact_directory = dataset_directory / sha256
            artifact_directory.mkdir(exist_ok=True)

            artifact_path = artifact_directory / "artifact"

            try:
                # Atomically publish without replacing an existing artifact.
                os.link(temporary_path, artifact_path)
            except FileExistsError:
                existing_checksum = self._calculate_sha256(artifact_path)

                if existing_checksum != sha256:
                    raise ArtifactIntegrityError(
                        f"Existing artifact failed integrity verification: {artifact_path}"
                    ) from None

            return StoredArtifact(
                dataset_id=dataset_id,
                original_filename=original_filename,
                sha256=sha256,
                uri=artifact_path.resolve().as_uri(),
            )

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _calculate_sha256(path: Path) -> str:
        checksum = hashlib.sha256()

        with path.open("rb") as artifact:
            while chunk := artifact.read(LocalArtifactStore.CHUNK_SIZE):
                checksum.update(chunk)

        return checksum.hexdigest()

    @staticmethod
    def _validate_filename(filename: str) -> None:
        if (
            not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
            or "\x00" in filename
        ):
            raise ValueError("Invalid original artifact filename.")
