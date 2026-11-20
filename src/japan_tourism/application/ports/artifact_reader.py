from contextlib import AbstractContextManager
from typing import BinaryIO, Protocol

from japan_tourism.application.models.stored_artifact import StoredArtifact


class ArtifactReader(Protocol):
    """Port for reading previously preserved source artifacts."""

    def open(
        self,
        artifact: StoredArtifact,
    ) -> AbstractContextManager[BinaryIO]:
        """Open a preserved artifact for reading.

        The returned context manager is responsible for managing
        the lifetime of the underlying binary stream.
        """
        ...
