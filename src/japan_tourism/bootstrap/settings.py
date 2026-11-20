import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IngestionSettings:
    manifest_directory: Path = Path("conf/ingestion")
    artifact_directory: Path = Path(".local/artifacts")
    metadata_database: Path = Path(".local/metadata.sqlite")
    bronze_table: str = "workspace.bronze.accommodation_foreign_guest_nights"
    databricks_profile: str = "JAPAN_TOURISM"

    def __post_init__(self) -> None:
        if not self.bronze_table.strip():
            raise ValueError("bronze_table cannot be empty.")

        if not self.databricks_profile.strip():
            raise ValueError("databricks_profile cannot be empty.")

    @classmethod
    def from_environment(cls) -> "IngestionSettings":
        def get_value(name: str, default: str) -> str:
            value = os.getenv(name, default)
            if not value.strip():
                raise ValueError(f"Environment variable {name} cannot be empty.")
            return value.strip()

        return cls(
            manifest_directory=Path(get_value("JTL_MANIFEST_DIRECTORY", "conf/ingestion")),
            artifact_directory=Path(get_value("JTL_ARTIFACT_DIRECTORY", ".local/artifacts")),
            metadata_database=Path(get_value("JTL_METADATA_DATABASE", ".local/metadata.sqlite")),
            bronze_table=get_value(
                "JTL_BRONZE_TABLE",
                "workspace.bronze.accommodation_foreign_guest_nights",
            ),
            databricks_profile=get_value(
                "JTL_DATABRICKS_PROFILE",
                "JAPAN_TOURISM",
            ),
        )
