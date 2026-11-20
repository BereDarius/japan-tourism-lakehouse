import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from uuid import UUID

from japan_tourism.application.exceptions import (
    DuplicateArtifactAcquisitionError,
)
from japan_tourism.application.models.artifact_acquisition import (
    ArtifactAcquisition,
)
from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.application.ports.artifact_acquisition_repository import (
    ArtifactAcquisitionRepository,
)
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class SQLiteArtifactAcquisitionRepository(ArtifactAcquisitionRepository):
    """SQLite implementation of the artifact acquisition repository."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize_database()

    def save(self, acquisition: ArtifactAcquisition) -> None:
        """Persist a new acquisition record.

        Raises:
            DuplicateArtifactAcquisitionError:
                If the acquisition ID already exists.
        """
        try:
            with self._connection() as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO artifact_acquisitions (
                            acquisition_id,
                            dataset_id,
                            original_filename,
                            sha256,
                            artifact_uri,
                            source_url,
                            retrieved_at,
                            publication_stage
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(acquisition.acquisition_id),
                            str(acquisition.artifact.dataset_id),
                            acquisition.artifact.original_filename,
                            acquisition.artifact.sha256,
                            acquisition.artifact.uri,
                            acquisition.source_url,
                            acquisition.retrieved_at.isoformat(),
                            acquisition.publication_stage,
                        ),
                    )

        except sqlite3.IntegrityError as error:
            if error.sqlite_errorname == "SQLITE_CONSTRAINT_PRIMARYKEY":
                raise DuplicateArtifactAcquisitionError(
                    f"Acquisition '{acquisition.acquisition_id}' already exists."
                ) from error

            raise

    def get_by_id(
        self,
        acquisition_id: UUID,
    ) -> ArtifactAcquisition | None:
        """Retrieve an acquisition record by its ID."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    acquisition_id,
                    dataset_id,
                    original_filename,
                    sha256,
                    artifact_uri,
                    source_url,
                    retrieved_at,
                    publication_stage
                FROM artifact_acquisitions
                WHERE acquisition_id = ?
                """,
                (str(acquisition_id),),
            ).fetchone()

        if row is None:
            return None

        return self._map_to_acquisition(row)

    def _initialize_database(self) -> None:
        """Create the acquisition table if it does not exist."""
        with self._connection() as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS artifact_acquisitions (
                        acquisition_id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        original_filename TEXT NOT NULL,
                        sha256 TEXT NOT NULL,
                        artifact_uri TEXT NOT NULL,
                        source_url TEXT NOT NULL,
                        retrieved_at TEXT NOT NULL,
                        publication_stage TEXT
                    )
                    """
                )

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a SQLite connection that is always closed."""
        connection = sqlite3.connect(self._database_path)

        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _map_to_acquisition(
        row: tuple[object, ...],
    ) -> ArtifactAcquisition:
        """Reconstruct an acquisition model from a database row."""
        (
            acquisition_id,
            dataset_id,
            original_filename,
            sha256,
            artifact_uri,
            source_url,
            retrieved_at,
            publication_stage,
        ) = row

        if not isinstance(acquisition_id, str):
            raise ValueError("Invalid acquisition ID in database.")

        if not isinstance(dataset_id, str):
            raise ValueError("Invalid dataset ID in database.")

        if not isinstance(original_filename, str):
            raise ValueError("Invalid original filename in database.")

        if not isinstance(sha256, str):
            raise ValueError("Invalid artifact checksum in database.")

        if not isinstance(artifact_uri, str):
            raise ValueError("Invalid artifact URI in database.")

        if not isinstance(source_url, str):
            raise ValueError("Invalid source URL in database.")

        if not isinstance(retrieved_at, str):
            raise ValueError("Invalid retrieval timestamp in database.")

        if publication_stage is not None and not isinstance(
            publication_stage,
            str,
        ):
            raise ValueError("Invalid publication stage in database.")

        artifact = StoredArtifact(
            dataset_id=DatasetId(dataset_id),
            original_filename=original_filename,
            sha256=sha256,
            uri=artifact_uri,
        )

        return ArtifactAcquisition(
            acquisition_id=UUID(acquisition_id),
            artifact=artifact,
            source_url=source_url,
            retrieved_at=datetime.fromisoformat(retrieved_at),
            publication_stage=publication_stage,
        )
