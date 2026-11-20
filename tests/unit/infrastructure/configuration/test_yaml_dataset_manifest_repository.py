from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from japan_tourism.application.exceptions import (
    DatasetManifestNotFoundError,
)
from japan_tourism.application.models.dataset_manifest import (
    DatasetManifest,
    ExcelLayout,
    ExcelReaderConfig,
)
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.configuration.manifest_loader import (
    YamlManifestLoader,
)
from japan_tourism.infrastructure.configuration.yaml_dataset_manifest_repository import (
    YamlDatasetManifestRepository,
)

ManifestData = dict[str, Any]


@pytest.fixture
def manifest_data() -> ManifestData:
    return {
        "manifest_version": 1,
        "dataset": {"id": "accommodation_foreign_guest_nights"},
        "source": {
            "provider": "japan_tourism_agency",
            "survey": "accommodation_survey",
            "format": "xlsx",
            "landing_page_url": (
                "https://www.mlit.go.jp/kankocho/tokei_hakusyo/shukuhakutokei.html"
            ),
        },
        "reader": {
            "type": "excel",
            "worksheet": "3-1",
            "layout": {
                "title_row": 1,
                "unit_row": 2,
                "reporting_year_row": 3,
                "month_header_row": 4,
                "data_start_row": 5,
                "expected_data_rows": 48,
            },
        },
        "ingestion": {"mode": "full_snapshot"},
    }


@pytest.fixture
def repository(tmp_path: Path) -> YamlDatasetManifestRepository:
    return YamlDatasetManifestRepository(
        manifest_directory=tmp_path,
        loader=YamlManifestLoader(),
    )


def write_manifest(
    directory: Path,
    dataset_id: str,
    data: ManifestData,
) -> None:
    data["dataset"]["id"] = dataset_id
    path = directory / f"{dataset_id}.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_get_returns_dataset_manifest(
    repository: YamlDatasetManifestRepository,
    tmp_path: Path,
    manifest_data: ManifestData,
) -> None:
    dataset_id = DatasetId("accommodation_foreign_guest_nights")
    write_manifest(tmp_path, dataset_id.value, manifest_data)

    result = repository.get(dataset_id)

    assert result == DatasetManifest(
        dataset_id=dataset_id,
        reader=ExcelReaderConfig(
            worksheet="3-1",
            layout=ExcelLayout(
                title_row=1,
                unit_row=2,
                reporting_year_row=3,
                month_header_row=4,
                data_start_row=5,
                expected_data_rows=48,
            ),
        ),
    )


def test_get_raises_when_manifest_is_missing(
    repository: YamlDatasetManifestRepository,
) -> None:
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    with pytest.raises(DatasetManifestNotFoundError):
        repository.get(dataset_id)


def test_get_rejects_manifest_id_mismatch(
    repository: YamlDatasetManifestRepository,
    tmp_path: Path,
    manifest_data: ManifestData,
) -> None:
    requested_id = DatasetId("accommodation_foreign_guest_nights")
    write_manifest(tmp_path, requested_id.value, manifest_data)
    manifest_data["dataset"]["id"] = "another_dataset"
    (tmp_path / f"{requested_id.value}.yaml").write_text(
        yaml.safe_dump(manifest_data),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match"):
        repository.get(requested_id)


def test_get_propagates_manifest_validation_error(
    repository: YamlDatasetManifestRepository,
    tmp_path: Path,
    manifest_data: ManifestData,
) -> None:
    dataset_id = DatasetId("accommodation_foreign_guest_nights")
    manifest_data["reader"]["layout"]["expected_data_rows"] = "48"
    write_manifest(tmp_path, dataset_id.value, manifest_data)

    with pytest.raises(ValidationError):
        repository.get(dataset_id)
