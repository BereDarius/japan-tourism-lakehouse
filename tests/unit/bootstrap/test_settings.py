from pathlib import Path

import pytest

from japan_tourism.bootstrap.settings import IngestionSettings

ENVIRONMENT_VARIABLES = (
    "JTL_MANIFEST_DIRECTORY",
    "JTL_ARTIFACT_DIRECTORY",
    "JTL_METADATA_DATABASE",
    "JTL_BRONZE_TABLE",
    "JTL_DATABRICKS_PROFILE",
)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_default_settings() -> None:
    settings = IngestionSettings.from_environment()

    assert settings.manifest_directory == Path("conf/ingestion")
    assert settings.artifact_directory == Path(".local/artifacts")
    assert settings.metadata_database == Path(".local/metadata.sqlite")
    assert settings.bronze_table == "workspace.bronze.accommodation_foreign_guest_nights"
    assert settings.databricks_profile == "JAPAN_TOURISM"


def test_environment_variables_override_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JTL_MANIFEST_DIRECTORY", "custom/manifests")
    monkeypatch.setenv("JTL_ARTIFACT_DIRECTORY", "custom/artifacts")
    monkeypatch.setenv("JTL_METADATA_DATABASE", "custom/metadata.sqlite")
    monkeypatch.setenv("JTL_BRONZE_TABLE", "catalog.schema.my_table")
    monkeypatch.setenv("JTL_DATABRICKS_PROFILE", "CUSTOM_PROFILE")

    settings = IngestionSettings.from_environment()

    assert settings.manifest_directory == Path("custom/manifests")
    assert settings.artifact_directory == Path("custom/artifacts")
    assert settings.metadata_database == Path("custom/metadata.sqlite")
    assert settings.bronze_table == "catalog.schema.my_table"
    assert settings.databricks_profile == "CUSTOM_PROFILE"


@pytest.mark.parametrize("name", ENVIRONMENT_VARIABLES)
def test_empty_environment_variable_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    monkeypatch.setenv(name, "   ")

    with pytest.raises(ValueError, match=name):
        IngestionSettings.from_environment()


def test_environment_values_are_stripped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JTL_BRONZE_TABLE", "  catalog.schema.table  ")
    monkeypatch.setenv("JTL_DATABRICKS_PROFILE", "  PROFILE  ")

    settings = IngestionSettings.from_environment()

    assert settings.bronze_table == "catalog.schema.table"
    assert settings.databricks_profile == "PROFILE"


def test_direct_settings_reject_empty_bronze_table() -> None:
    with pytest.raises(ValueError):
        IngestionSettings(bronze_table=" ")


def test_direct_settings_reject_empty_databricks_profile() -> None:
    with pytest.raises(ValueError):
        IngestionSettings(databricks_profile=" ")
