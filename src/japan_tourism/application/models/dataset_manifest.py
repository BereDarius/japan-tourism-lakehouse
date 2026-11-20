from dataclasses import dataclass

from japan_tourism.domain.value_objects.dataset_id import DatasetId


@dataclass(frozen=True)
class ExcelLayout:
    """Worksheet layout required for Excel extraction."""

    title_row: int
    unit_row: int
    reporting_year_row: int
    month_header_row: int
    data_start_row: int
    expected_data_rows: int


@dataclass(frozen=True)
class ExcelReaderConfig:
    """Configuration for reading an Excel worksheet."""

    worksheet: str
    layout: ExcelLayout


@dataclass(frozen=True)
class DatasetManifest:
    """Application representation of a dataset ingestion manifest."""

    dataset_id: DatasetId
    reader: ExcelReaderConfig
