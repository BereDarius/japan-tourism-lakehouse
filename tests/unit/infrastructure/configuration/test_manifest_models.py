from typing import Any

import pytest
from pydantic import ValidationError

from japan_tourism.infrastructure.configuration.manifest_models import (
    IngestionManifest,
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


def test_valid_manifest_is_accepted(valid_manifest_data: ManifestData) -> None:
    manifest = IngestionManifest.model_validate(valid_manifest_data)

    assert manifest.dataset.id == "accommodation_foreign_guest_nights"
    assert manifest.reader.layout.expected_data_rows == 48


def test_unknown_field_is_rejected(valid_manifest_data: ManifestData) -> None:
    valid_manifest_data["unexpected_field"] = "value"

    with pytest.raises(ValidationError):
        IngestionManifest.model_validate(valid_manifest_data)


def test_string_row_count_is_rejected(valid_manifest_data: ManifestData) -> None:
    valid_manifest_data["reader"]["layout"]["expected_data_rows"] = "48"

    with pytest.raises(ValidationError):
        IngestionManifest.model_validate(valid_manifest_data)


def test_invalid_dataset_id_is_rejected(valid_manifest_data: ManifestData) -> None:
    valid_manifest_data["dataset"]["id"] = "Invalid Dataset ID"

    with pytest.raises(ValidationError):
        IngestionManifest.model_validate(valid_manifest_data)


def test_invalid_row_order_is_rejected(valid_manifest_data: ManifestData) -> None:
    valid_manifest_data["reader"]["layout"]["data_start_row"] = 3

    with pytest.raises(ValidationError):
        IngestionManifest.model_validate(valid_manifest_data)


def test_unsupported_ingestion_mode_is_rejected(
    valid_manifest_data: ManifestData,
) -> None:
    valid_manifest_data["ingestion"]["mode"] = "incremental"

    with pytest.raises(ValidationError):
        IngestionManifest.model_validate(valid_manifest_data)
