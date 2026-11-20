from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedWorksheet:
    """Represents source-shaped data extracted from a worksheet."""

    worksheet_name: str
    title: str
    unit: str
    reporting_year: int
    column_headers: tuple[str | None, ...]
    rows: tuple[tuple[object, ...], ...]
