from io import BytesIO
from typing import BinaryIO

import pytest
from openpyxl import Workbook

from japan_tourism.application.models.dataset_manifest import (
    ExcelLayout,
    ExcelReaderConfig,
)
from japan_tourism.infrastructure.sources.excel_source_reader import (
    ExcelReaderError,
    ExcelSourceReader,
)

ExcelCellValue = bool | float | int | str | None


@pytest.fixture
def reader() -> ExcelSourceReader:
    return ExcelSourceReader()


@pytest.fixture
def config() -> ExcelReaderConfig:
    return ExcelReaderConfig(
        worksheet="3-1",
        layout=ExcelLayout(
            title_row=1,
            unit_row=2,
            reporting_year_row=3,
            month_header_row=4,
            data_start_row=5,
            expected_data_rows=48,
        ),
    )


def create_workbook(
    *,
    reporting_year: str = "令和8年",
    data_rows: int = 48,
    title: str = "都道府県別 外国人延べ宿泊者数",
    unit: str = "（単位：人泊）",
    month_headers: list[str] | None = None,
    observations: list[ExcelCellValue] | None = None,
) -> BinaryIO:
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = "3-1"

    worksheet["A1"] = title
    worksheet["M2"] = unit
    worksheet["B3"] = reporting_year

    worksheet.merge_cells("A3:A4")
    worksheet.merge_cells("B3:M3")

    headers = month_headers or [f"{month}月" for month in range(1, 13)]

    for column, header in enumerate(headers, start=2):
        worksheet.cell(row=4, column=column, value=header)

    for index in range(data_rows):
        row_number = 5 + index
        geography = "全　国" if index == 0 else f"{index:02d}都道府県"

        worksheet.cell(row=row_number, column=1, value=geography)

        for month in range(12):
            value = 1000 + index + month

            if observations is not None and index == 0 and month == 0:
                value = observations[0]

            if month >= 8:
                value = None

            worksheet.cell(
                row=row_number,
                column=month + 2,
                value=value,
            )

    worksheet["A53"] = "※令和8年の数値は速報値"

    stream = BytesIO()
    workbook.save(stream)
    workbook.close()
    stream.seek(0)

    return stream


def test_reads_worksheet_successfully(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
) -> None:
    result = reader.read(create_workbook(), config)

    assert result.worksheet_name == "3-1"
    assert result.title == "都道府県別 外国人延べ宿泊者数"
    assert result.unit == "（単位：人泊）"
    assert result.reporting_year == 2026

    assert result.column_headers == (
        None,
        "1月",
        "2月",
        "3月",
        "4月",
        "5月",
        "6月",
        "7月",
        "8月",
        "9月",
        "10月",
        "11月",
        "12月",
    )

    assert len(result.rows) == 48
    assert len(result.rows[0]) == 13
    assert result.rows[0][0] == "全　国"
    assert result.rows[0][1] == 1000
    assert result.rows[0][9] is None


@pytest.mark.parametrize(
    ("year_text", "expected_year"),
    [
        ("令和元年", 2019),
        ("令和2年", 2020),
        ("令和8年", 2026),
    ],
)
def test_converts_reiwa_year(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
    year_text: str,
    expected_year: int,
) -> None:
    result = reader.read(
        create_workbook(reporting_year=year_text),
        config,
    )

    assert result.reporting_year == expected_year


def test_rejects_missing_worksheet(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
) -> None:
    config = ExcelReaderConfig(
        worksheet="missing",
        layout=config.layout,
    )

    with pytest.raises(ExcelReaderError, match="was not found"):
        reader.read(create_workbook(), config)


@pytest.mark.parametrize(
    "year_text",
    ["2026", "平成30年", "令和0年", "invalid"],
)
def test_rejects_unsupported_reporting_year(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
    year_text: str,
) -> None:
    with pytest.raises(ExcelReaderError, match="reporting year"):
        reader.read(
            create_workbook(reporting_year=year_text),
            config,
        )


def test_rejects_unexpected_data_row_count(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
) -> None:
    stream = create_workbook(data_rows=47)

    with pytest.raises(ExcelReaderError):
        reader.read(stream, config)


def test_rejects_invalid_month_headers(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
) -> None:
    headers = [f"{month}月" for month in range(1, 13)]
    headers[0] = "January"

    with pytest.raises(ExcelReaderError, match="Invalid month headers"):
        reader.read(
            create_workbook(month_headers=headers),
            config,
        )


def test_preserves_blank_observations(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
) -> None:
    result = reader.read(create_workbook(), config)

    assert result.rows[0][9] is None
    assert result.rows[0][10] is None
    assert result.rows[0][11] is None
    assert result.rows[0][12] is None


@pytest.mark.parametrize("value", [-1, "invalid", True])
def test_rejects_invalid_observations(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
    value: ExcelCellValue,
) -> None:
    with pytest.raises(ExcelReaderError, match="Invalid observation|Negative"):
        reader.read(
            create_workbook(observations=[value]),
            config,
        )


@pytest.mark.parametrize(
    ("title", "unit"),
    [
        ("", "（単位：人泊）"),
        ("Valid title", ""),
    ],
)
def test_rejects_missing_title_or_unit(
    reader: ExcelSourceReader,
    config: ExcelReaderConfig,
    title: str,
    unit: str,
) -> None:
    with pytest.raises(ExcelReaderError):
        reader.read(
            create_workbook(title=title, unit=unit),
            config,
        )
