from japan_tourism.domain.value_objects.dataset_id import DatasetId


class IngestionRunNotFoundError(Exception):
    """Raised when an ingestion run cannot be found."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Ingestion run '{run_id}' was not found.")


class DatasetManifestNotFoundError(Exception):
    """Raised when a dataset manifest cannot be found."""

    def __init__(self, dataset_id: DatasetId) -> None:
        self.dataset_id = dataset_id
        super().__init__(f"Manifest for dataset '{dataset_id}' was not found.")


class DuplicateArtifactAcquisitionError(Exception):
    """Raised when an acquisition ID already exists."""


class BronzeWriteOutcomeUnknownError(RuntimeError):
    """Raised when a Bronze write may have committed but its outcome is unknown."""
