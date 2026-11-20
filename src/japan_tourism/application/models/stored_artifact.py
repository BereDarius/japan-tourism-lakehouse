from dataclasses import dataclass

from japan_tourism.domain.value_objects.dataset_id import DatasetId


@dataclass(frozen=True)
class StoredArtifact:
    """Reference to an immutable, preserved source artifact."""

    dataset_id: DatasetId
    original_filename: str
    sha256: str
    uri: str
