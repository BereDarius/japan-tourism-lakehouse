from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from japan_tourism.domain.value_objects.dataset_id import DatasetId

NonEmptyString = Annotated[str, Field(min_length=1)]
PositiveInt = Annotated[int, Field(gt=0)]


class StrictConfigModel(BaseModel):
    """Base class for immutable, strictly validated configuration models."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )


class DatasetConfig(StrictConfigModel):
    id: NonEmptyString

    @field_validator("id")
    @classmethod
    def validate_dataset_id(cls, value: str) -> str:
        DatasetId(value)
        return value


class SourceConfig(StrictConfigModel):
    provider: NonEmptyString
    survey: NonEmptyString
    format: Literal["xlsx"]
    landing_page_url: NonEmptyString

    @field_validator("landing_page_url")
    @classmethod
    def validate_landing_page_url(cls, value: str) -> str:
        parsed_url = urlsplit(value)

        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError("landing_page_url must be a valid HTTPS URL")

        return value


class ExcelLayoutConfig(StrictConfigModel):
    title_row: PositiveInt
    unit_row: PositiveInt
    reporting_year_row: PositiveInt
    month_header_row: PositiveInt
    data_start_row: PositiveInt
    expected_data_rows: PositiveInt

    @model_validator(mode="after")
    def validate_row_order(self) -> "ExcelLayoutConfig":
        rows = (
            self.title_row,
            self.unit_row,
            self.reporting_year_row,
            self.month_header_row,
            self.data_start_row,
        )

        if tuple(sorted(rows)) != rows:
            raise ValueError(
                "Worksheet rows must be in ascending order: "
                "title, unit, reporting year, month header, data"
            )

        return self


class ReaderConfig(StrictConfigModel):
    type: Literal["excel"]
    worksheet: NonEmptyString
    layout: ExcelLayoutConfig


class IngestionConfig(StrictConfigModel):
    mode: Literal["full_snapshot"]


class IngestionManifest(StrictConfigModel):
    manifest_version: Literal[1]
    dataset: DatasetConfig
    source: SourceConfig
    reader: ReaderConfig
    ingestion: IngestionConfig
