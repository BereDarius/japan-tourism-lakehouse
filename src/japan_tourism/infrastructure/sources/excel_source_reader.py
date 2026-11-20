from __future__ import annotations

import re
from typing import BinaryIO, cast

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.worksheet._read_only import ReadOnlyWorksheet

from japan_tourism.application.models.dataset_manifest import (
    ExcelReaderConfig,
)
from japan_tourism.application.models.extracted_worksheet import (
    ExtractedWorksheet,
)


class ExcelReaderError(ValueError):
    """Raised when an Excel source cannot be extracted."""


class ExcelSourceReader:
    """Extracts source-shaped data from Excel worksheets."""

    _MONTH_PATTERN = re.compile(r"^(?:[1-9]|1[0-2])月$")
    _REIWA_YEAR_PATTERN = re.compile(r"^令和(?P<year>\d+|元)年$")

    def read(
        self,
        source: BinaryIO,
        config: ExcelReaderConfig,
    ) -> ExtractedWorksheet:
        """Extract a configured worksheet while preserving its source layout."""
        try:
            workbook = load_workbook(
                source,
                read_only=True,
                data_only=True,
            )
        except (InvalidFileException, OSError, ValueError) as error:
            raise ExcelReaderError("Unable to open Excel workbook.") from error

        try:
            if config.worksheet not in workbook.sheetnames:
                raise ExcelReaderError(
                    f"Worksheet '{config.worksheet}' was not found. "
                    f"Available worksheets: {workbook.sheetnames}"
                )

            worksheet = cast(
                ReadOnlyWorksheet,
                workbook[config.worksheet],
            )
            layout = config.layout

            title = self._read_single_value(
                worksheet,
                layout.title_row,
                "title",
            )
            unit = self._read_single_value(
                worksheet,
                layout.unit_row,
                "unit",
            )
            reporting_year = self._read_reporting_year(
                worksheet,
                layout.reporting_year_row,
            )

            column_headers = self._read_month_headers(
                worksheet,
                layout.month_header_row,
            )

            rows = self._read_data_rows(
                worksheet,
                layout.data_start_row,
                layout.expected_data_rows,
                len(column_headers),
            )

            return ExtractedWorksheet(
                worksheet_name=worksheet.title,
                title=title,
                unit=unit,
                reporting_year=reporting_year,
                column_headers=column_headers,
                rows=rows,
            )
        finally:
            workbook.close()

    @staticmethod
    def _read_single_value(
        worksheet: ReadOnlyWorksheet,
        row_number: int,
        field_name: str,
    ) -> str:
        """Read a row containing exactly one non-empty textual value."""
        values = cast(
            tuple[object, ...],
            next(
                worksheet.iter_rows(
                    min_row=row_number,
                    max_row=row_number,
                    values_only=True,
                )
            ),
        )

        populated_values = [value for value in values if value is not None]

        if len(populated_values) != 1:
            raise ExcelReaderError(
                f"Expected exactly one populated cell for {field_name} "
                f"in row {row_number}; found {len(populated_values)}."
            )

        value = populated_values[0]

        if not isinstance(value, str) or not value.strip():
            raise ExcelReaderError(
                f"Expected a non-empty text value for {field_name} in row {row_number}."
            )

        return value.strip()

    def _read_reporting_year(
        self,
        worksheet: ReadOnlyWorksheet,
        row_number: int,
    ) -> int:
        """Convert a Japanese Reiwa year into a Gregorian calendar year."""
        value = self._read_single_value(
            worksheet,
            row_number,
            "reporting year",
        )

        match = self._REIWA_YEAR_PATTERN.fullmatch(value)

        if match is None:
            raise ExcelReaderError(
                f"Unsupported reporting year format: {value!r}. "
                "Expected a Reiwa year such as '令和8年'."
            )

        year_text = match.group("year")
        reiwa_year = 1 if year_text == "元" else int(year_text)

        if reiwa_year < 1:
            raise ExcelReaderError(f"Invalid reporting year: {value!r}.")

        return 2018 + reiwa_year

    def _read_month_headers(
        self,
        worksheet: ReadOnlyWorksheet,
        row_number: int,
    ) -> tuple[str | None, ...]:
        """Read and validate twelve Japanese month headers."""
        values = next(
            worksheet.iter_rows(
                min_row=row_number,
                max_row=row_number,
                values_only=True,
            )
        )

        if len(values) != 13:
            raise ExcelReaderError(
                f"Expected 13 worksheet columns in month header row "
                f"{row_number}; found {len(values)}."
            )

        if values[0] is not None:
            raise ExcelReaderError("Expected the first month-header cell (column A) to be blank.")

        validated_headers: list[str] = []

        for header in values[1:]:
            if not isinstance(header, str):
                raise ExcelReaderError(
                    f"Expected all month headers to be strings; found {values[1:]}."
                )

            validated_headers.append(header)

        expected_headers = tuple(f"{month}月" for month in range(1, 13))

        month_headers = tuple(validated_headers)

        if month_headers != expected_headers:
            raise ExcelReaderError(
                f"Invalid month headers in row {row_number}. "
                f"Expected {expected_headers}; found {month_headers}."
            )

        return (None, *month_headers)

    @staticmethod
    def _read_data_rows(
        worksheet: ReadOnlyWorksheet,
        start_row: int,
        expected_data_rows: int,
        expected_columns: int,
    ) -> tuple[tuple[object, ...], ...]:
        """Read source-shaped data rows and validate their values."""
        end_row = start_row + expected_data_rows - 1

        rows = tuple(
            cast(tuple[object, ...], row)
            for row in worksheet.iter_rows(
                min_row=start_row,
                max_row=end_row,
                min_col=1,
                max_col=expected_columns,
                values_only=True,
            )
        )

        if len(rows) != expected_data_rows:
            raise ExcelReaderError(f"Expected {expected_data_rows} data rows; found {len(rows)}.")

        for row_index, row in enumerate(rows, start=start_row):
            if len(row) != expected_columns:
                raise ExcelReaderError(f"Unexpected number of columns in row {row_index}.")

            geography = row[0]

            if not isinstance(geography, str) or not geography.strip():
                raise ExcelReaderError(f"Missing or invalid geography label in row {row_index}.")

            for column_index, value in enumerate(row[1:], start=2):
                if value is None:
                    continue

                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ExcelReaderError(
                        f"Invalid observation at row {row_index}, column {column_index}: {value!r}."
                    )

                if value < 0:
                    raise ExcelReaderError(
                        f"Negative observation at row {row_index}, "
                        f"column {column_index}: {value!r}."
                    )

        return rows
