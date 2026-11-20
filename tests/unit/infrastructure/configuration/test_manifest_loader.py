from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from japan_tourism.infrastructure.configuration.manifest_loader import (
    ManifestFileNotFoundError,
    ManifestYamlParseError,
    YamlManifestLoader,
)

ManifestData = dict[str, Any]


@pytest.fixture
def valid_manifest_data() -> ManifestData:
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


def test_load_valid_manifest(
    tmp_path: Path,
    valid_manifest_data: ManifestData,
) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(valid_manifest_data),
        encoding="utf-8",
    )

    manifest = YamlManifestLoader().load(manifest_path)

    assert manifest.dataset.id == "accommodation_foreign_guest_nights"
    assert manifest.ingestion.mode == "full_snapshot"


def test_missing_manifest_raises_file_not_found_error(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "missing.yaml"

    with pytest.raises(ManifestFileNotFoundError):
        YamlManifestLoader().load(manifest_path)


def test_malformed_yaml_raises_parse_error(tmp_path: Path) -> None:
    manifest_path = tmp_path / "malformed.yaml"
    manifest_path.write_text("dataset: [\n", encoding="utf-8")

    with pytest.raises(ManifestYamlParseError):
        YamlManifestLoader().load(manifest_path)


def test_invalid_manifest_raises_validation_error(
    tmp_path: Path,
    valid_manifest_data: ManifestData,
) -> None:
    valid_manifest_data["reader"]["layout"]["expected_data_rows"] = "48"

    manifest_path = tmp_path / "invalid.yaml"
    manifest_path.write_text(
        yaml.safe_dump(valid_manifest_data),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        YamlManifestLoader().load(manifest_path)
