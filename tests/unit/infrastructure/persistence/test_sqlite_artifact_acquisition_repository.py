import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from japan_tourism.application.exceptions import (
    DuplicateArtifactAcquisitionError,
)
from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.domain.value_objects.dataset_id import DatasetId
from japan_tourism.infrastructure.persistence.sqlite_artifact_acquisition_repository import (
    SQLiteArtifactAcquisitionRepository,
)


def make_acquisition(
    publication_stage: str | None = "preliminary",
) -> ArtifactAcquisition:
    return ArtifactAcquisition(
        acquisition_id=uuid4(),
        artifact=StoredArtifact(
            dataset_id=DatasetId("accommodation_foreign_guest_nights"),
            original_filename="002028776.xlsx",
            sha256="a" * 64,
            uri="file:///artifacts/002028776.xlsx",
        ),
        source_url="https://example.com/002028776.xlsx",
        retrieved_at=datetime(2026, 11, 20, 10, 0, tzinfo=UTC),
        publication_stage=publication_stage,
    )


def test_initializes_database(tmp_path: Path) -> None:
    database_path = tmp_path / "metadata" / "acquisitions.db"

    SQLiteArtifactAcquisitionRepository(database_path)

    assert database_path.exists()

    with sqlite3.connect(database_path) as connection:
        result = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'artifact_acquisitions'
            """
        ).fetchone()

    assert result is not None


def test_saves_and_retrieves_acquisition(tmp_path: Path):
    repository = SQLiteArtifactAcquisitionRepository(tmp_path / "acquisitions.db")
    acquisition = make_acquisition()

    repository.save(acquisition)

    result = repository.get_by_id(acquisition.acquisition_id)

    assert result == acquisition


def test_returns_none_for_missing_acquisition(tmp_path: Path):
    repository = SQLiteArtifactAcquisitionRepository(tmp_path / "acquisitions.db")

    assert repository.get_by_id(uuid4()) is None


def test_rejects_duplicate_acquisition_id(tmp_path: Path):
    repository = SQLiteArtifactAcquisitionRepository(tmp_path / "acquisitions.db")
    acquisition = make_acquisition()

    repository.save(acquisition)

    with pytest.raises(DuplicateArtifactAcquisitionError):
        repository.save(acquisition)

    assert repository.get_by_id(acquisition.acquisition_id) == acquisition


def test_preserves_multiple_acquisitions(tmp_path: Path):
    repository = SQLiteArtifactAcquisitionRepository(tmp_path / "acquisitions.db")
    first = make_acquisition()
    second = make_acquisition()

    repository.save(first)
    repository.save(second)

    assert repository.get_by_id(first.acquisition_id) == first
    assert repository.get_by_id(second.acquisition_id) == second


def test_persists_acquisitions_across_repository_instances(tmp_path: Path):
    database_path = tmp_path / "acquisitions.db"

    first_repository = SQLiteArtifactAcquisitionRepository(database_path)
    acquisition = make_acquisition()

    first_repository.save(acquisition)

    second_repository = SQLiteArtifactAcquisitionRepository(database_path)

    assert second_repository.get_by_id(acquisition.acquisition_id) == acquisition


def test_preserves_null_publication_stage(tmp_path: Path):
    repository = SQLiteArtifactAcquisitionRepository(tmp_path / "acquisitions.db")
    acquisition = make_acquisition(publication_stage=None)

    repository.save(acquisition)

    result = repository.get_by_id(acquisition.acquisition_id)

    assert result is not None
    assert result.publication_stage is None
