import sqlite3
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest
from pyspark.sql import SparkSession

from japan_tourism.application.services.ingestion_engine import IngestionEngine
from japan_tourism.bootstrap.ingestion import create_ingestion_engine
from japan_tourism.bootstrap.settings import IngestionSettings


def fail_if_databricks_session_created(profile: str) -> SparkSession:
    pytest.fail("Databricks session should not be created.")


def test_create_ingestion_engine_wires_shared_metadata_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = IngestionSettings(
        manifest_directory=tmp_path / "manifests",
        artifact_directory=tmp_path / "artifacts",
        metadata_database=tmp_path / "metadata.sqlite",
        bronze_table="workspace.bronze.test_dataset",
        databricks_profile="TEST_PROFILE",
    )
    spark = cast(SparkSession, MagicMock())

    monkeypatch.setattr(
        "japan_tourism.bootstrap.ingestion.create_databricks_session",
        fail_if_databricks_session_created,
    )

    engine = create_ingestion_engine(settings, spark=spark)

    assert isinstance(engine, IngestionEngine)

    with sqlite3.connect(settings.metadata_database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "ingestion_runs" in tables
    assert "artifact_acquisitions" in tables
