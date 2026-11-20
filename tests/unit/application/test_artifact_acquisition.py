from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.domain.value_objects.dataset_id import DatasetId


@pytest.fixture
def stored_artifact() -> StoredArtifact:
    return StoredArtifact(
        dataset_id=DatasetId("accommodation_foreign_guest_nights"),
        original_filename="002028776.xlsx",
        sha256="a" * 64,
        uri="file:///artifacts/a" * 1,
    )


def test_valid_acquisition_is_created(
    stored_artifact: StoredArtifact,
) -> None:
    retrieved_at = datetime.now(UTC)

    acquisition = ArtifactAcquisition(
        acquisition_id=uuid4(),
        artifact=stored_artifact,
        source_url="https://example.com/source.xlsx",
        retrieved_at=retrieved_at,
        publication_stage="preliminary",
    )

    assert acquisition.artifact == stored_artifact
    assert acquisition.retrieved_at == retrieved_at
    assert acquisition.publication_stage == "preliminary"


def test_naive_timestamp_is_rejected(
    stored_artifact: StoredArtifact,
) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ArtifactAcquisition(
            acquisition_id=uuid4(),
            artifact=stored_artifact,
            source_url="https://example.com/source.xlsx",
            retrieved_at=datetime(2026, 11, 20),
        )


def test_non_utc_timestamp_is_rejected(
    stored_artifact: StoredArtifact,
) -> None:
    non_utc_timestamp = datetime(2026, 11, 20, tzinfo=timezone(timedelta(hours=2)))

    with pytest.raises(ValueError, match="UTC"):
        ArtifactAcquisition(
            acquisition_id=uuid4(),
            artifact=stored_artifact,
            source_url="https://example.com/source.xlsx",
            retrieved_at=non_utc_timestamp,
        )


def test_empty_source_url_is_rejected(
    stored_artifact: StoredArtifact,
) -> None:
    with pytest.raises(ValueError, match="Source URL"):
        ArtifactAcquisition(
            acquisition_id=uuid4(),
            artifact=stored_artifact,
            source_url=" ",
            retrieved_at=datetime.now(UTC),
        )


def test_empty_publication_stage_is_rejected(
    stored_artifact: StoredArtifact,
) -> None:
    with pytest.raises(ValueError, match="Publication stage"):
        ArtifactAcquisition(
            acquisition_id=uuid4(),
            artifact=stored_artifact,
            source_url="https://example.com/source.xlsx",
            retrieved_at=datetime.now(UTC),
            publication_stage=" ",
        )


def test_publication_stage_can_be_omitted(
    stored_artifact: StoredArtifact,
) -> None:
    acquisition = ArtifactAcquisition(
        acquisition_id=uuid4(),
        artifact=stored_artifact,
        source_url="https://example.com/source.xlsx",
        retrieved_at=datetime.now(UTC),
    )

    assert acquisition.publication_stage is None
