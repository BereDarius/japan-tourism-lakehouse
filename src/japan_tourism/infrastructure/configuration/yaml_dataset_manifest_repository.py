from pathlib import Path

from japan_tourism.application.exceptions import (
    DatasetManifestNotFoundError,
)
from japan_tourism.application.models.dataset_manifest import (
    DatasetManifest,
    ExcelLayout,
    ExcelReaderConfig,
)
from japan_tourism.application.ports.dataset_manifest_repository import (
    DatasetManifestRepository,
)
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.configuration.manifest_loader import (
    ManifestFileNotFoundError,
    YamlManifestLoader,
)


class YamlDatasetManifestRepository(DatasetManifestRepository):
    """Filesystem-backed dataset manifest repository."""

    def __init__(
        self,
        manifest_directory: Path,
        loader: YamlManifestLoader,
    ) -> None:
        self._manifest_directory = manifest_directory
        self._loader = loader

    def get(self, dataset_id: DatasetId) -> DatasetManifest:
        """Retrieve a validated dataset manifest by its identifier."""
        manifest_path = self._manifest_directory / f"{dataset_id.value}.yaml"

        try:
            manifest = self._loader.load(manifest_path)
        except ManifestFileNotFoundError as error:
            raise DatasetManifestNotFoundError(dataset_id) from error

        if manifest.dataset.id != dataset_id.value:
            raise ValueError(
                f"Manifest ID '{manifest.dataset.id}' does not match "
                f"requested dataset ID '{dataset_id.value}'."
            )

        layout = manifest.reader.layout

        return DatasetManifest(
            dataset_id=dataset_id,
            reader=ExcelReaderConfig(
                worksheet=manifest.reader.worksheet,
                layout=ExcelLayout(
                    title_row=layout.title_row,
                    unit_row=layout.unit_row,
                    reporting_year_row=layout.reporting_year_row,
                    month_header_row=layout.month_header_row,
                    data_start_row=layout.data_start_row,
                    expected_data_rows=layout.expected_data_rows,
                ),
            ),
        )
