from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from japan_tourism.application.models.stored_artifact import StoredArtifact


@dataclass(frozen=True)
class ArtifactAcquisition:
    """Records the acquisition and provenance of a source artifact."""

    acquisition_id: UUID
    artifact: StoredArtifact
    source_url: str
    retrieved_at: datetime
    publication_stage: str | None = None

    def __post_init__(self) -> None:
        if not self.source_url.strip():
            raise ValueError("Source URL cannot be empty.")

        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("Retrieval timestamp must be timezone-aware.")

        if self.retrieved_at.utcoffset() != UTC.utcoffset(self.retrieved_at):
            raise ValueError("Retrieval timestamp must be in UTC.")

        if self.publication_stage is not None and not self.publication_stage.strip():
            raise ValueError("Publication stage cannot be empty.")
