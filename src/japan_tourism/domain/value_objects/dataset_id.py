import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetId:
    """Identifies a dataset using a stable snake_case identifier."""

    value: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.value):
            raise ValueError(
                "Dataset ID must start with a lowercase letter "
                "and contain only lowercase letters, digits, and underscores."
            )

    def __str__(self) -> str:
        return self.value
