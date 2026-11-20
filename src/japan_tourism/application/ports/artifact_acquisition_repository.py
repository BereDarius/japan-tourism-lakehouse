from typing import Protocol
from uuid import UUID

from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)


class ArtifactAcquisitionRepository(Protocol):
    def save(self, acquisition: ArtifactAcquisition) -> None:
        """Persist a new acquisition record.

        Raises:
            DuplicateArtifactAcquisitionError: If the ID already exists.
        """

    def get_by_id(
        self,
        acquisition_id: UUID,
    ) -> ArtifactAcquisition | None:
        """Retrieve an acquisition record by its ID."""
