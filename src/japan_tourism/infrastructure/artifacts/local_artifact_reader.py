import hashlib
import os
import stat
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO
from urllib.parse import unquote, urlsplit

from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.application.ports.artifact_reader import ArtifactReader
from japan_tourism.infrastructure.artifacts.local_artifact_store import (
    ArtifactIntegrityError,
)


class InvalidArtifactUriError(ValueError):
    """Raised when an artifact URI is invalid or outside the configured store."""


class LocalArtifactReader(ArtifactReader):
    """Filesystem-backed reader for previously preserved source artifacts."""

    CHUNK_SIZE = 1024 * 1024

    def __init__(self, root_directory: Path) -> None:
        self._root_directory = root_directory.resolve()

    @contextmanager
    def open(self, artifact: StoredArtifact) -> Generator[BinaryIO, None, None]:
        """Open and verify a preserved artifact.

        The checksum is verified before the stream is yielded.
        The underlying file remains open until the context exits.
        """
        artifact_path = self._resolve_artifact_path(artifact)

        with artifact_path.open("rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise InvalidArtifactUriError("Artifact URI must reference a regular file.")

            checksum = hashlib.sha256()

            while chunk := stream.read(self.CHUNK_SIZE):
                checksum.update(chunk)

            actual_sha256 = checksum.hexdigest()

            if actual_sha256 != artifact.sha256:
                raise ArtifactIntegrityError(
                    f"Artifact checksum mismatch: expected {artifact.sha256}, got {actual_sha256}."
                )

            stream.seek(0)
            yield stream

    def _resolve_artifact_path(self, artifact: StoredArtifact) -> Path:
        """Resolve and validate the artifact's filesystem location."""
        if len(artifact.sha256) != 64 or any(
            character not in "0123456789abcdef" for character in artifact.sha256
        ):
            raise InvalidArtifactUriError("Invalid artifact SHA-256 value.")

        try:
            parsed_uri = urlsplit(artifact.uri)
        except ValueError as exc:
            raise InvalidArtifactUriError("Invalid artifact URI.") from exc

        if (
            parsed_uri.scheme != "file"
            or parsed_uri.netloc
            or parsed_uri.query
            or parsed_uri.fragment
        ):
            raise InvalidArtifactUriError(
                "Artifact URI must be a local file URI without query or fragment."
            )

        if not parsed_uri.path:
            raise InvalidArtifactUriError("Artifact URI must contain a file path.")

        candidate_path = Path(unquote(parsed_uri.path))

        resolved_path = candidate_path.resolve(strict=True)

        expected_path = (
            self._root_directory / artifact.dataset_id.value / artifact.sha256 / "artifact"
        )

        if resolved_path != expected_path:
            raise InvalidArtifactUriError(
                "Artifact URI does not match the expected dataset and checksum path."
            )

        return resolved_path
