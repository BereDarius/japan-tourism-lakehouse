from dataclasses import dataclass

from japan_tourism.domain.value_objects.dataset_id import DatasetId


@dataclass(frozen=True)
class DatasetManifest:
    """Application representation of a dataset ingestion manifest."""

    dataset_id: DatasetId
