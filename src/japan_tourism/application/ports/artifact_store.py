from typing import BinaryIO, Protocol

from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class ArtifactStore(Protocol):
    """Port for immutable storage of source artifacts."""

    def store(
        self,
        dataset_id: DatasetId,
        source: BinaryIO,
        original_filename: str,
    ) -> StoredArtifact:
        """Preserve an artifact and return its storage reference."""
        ...
