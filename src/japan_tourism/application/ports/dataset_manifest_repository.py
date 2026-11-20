from typing import Protocol

from japan_tourism.application.models.dataset_manifest import DatasetManifest
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class DatasetManifestRepository(Protocol):
    """Port for retrieving dataset ingestion manifests."""

    def get(self, dataset_id: DatasetId) -> DatasetManifest:
        """Retrieve a manifest by its dataset identifier."""
        ...
