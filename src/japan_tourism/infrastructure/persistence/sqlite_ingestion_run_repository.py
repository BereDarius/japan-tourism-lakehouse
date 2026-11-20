import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from uuid import UUID

from japan_tourism.application.ports.ingestion_run_repository import (
    IngestionRunRepository,
)
from japan_tourism.domain.models.ingestion_run import IngestionRun
from japan_tourism.domain.models.ingestion_status import IngestionStatus
from japan_tourism.domain.value_objects.dataset_id import DatasetId


class SQLiteIngestionRunRepository(IngestionRunRepository):
    """SQLite implementation of the ingestion run repository."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize_database()

    def save(self, run: IngestionRun) -> None:
        """Insert or update an ingestion run."""
        with self._connection() as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO ingestion_runs (
                        run_id,
                        dataset_id,
                        status,
                        started_at,
                        completed_at,
                        error_message
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(run_id) DO UPDATE SET
                        dataset_id = excluded.dataset_id,
                        status = excluded.status,
                        started_at = excluded.started_at,
                        completed_at = excluded.completed_at,
                        error_message = excluded.error_message
                    """,
                    (
                        str(run.run_id),
                        run.dataset_id.value,
                        run.status.value,
                        (run.started_at.isoformat() if run.started_at is not None else None),
                        (run.completed_at.isoformat() if run.completed_at is not None else None),
                        run.error_message,
                    ),
                )

    def get_by_id(self, run_id: UUID) -> IngestionRun | None:
        """Retrieve an ingestion run by its unique identifier."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    run_id,
                    dataset_id,
                    status,
                    started_at,
                    completed_at,
                    error_message
                FROM ingestion_runs
                WHERE run_id = ?
                """,
                (str(run_id),),
            ).fetchone()

        if row is None:
            return None

        return self._map_to_run(row)

    def get_by_dataset_id(
        self,
        dataset_id: DatasetId,
    ) -> list[IngestionRun]:
        """Retrieve all ingestion runs belonging to a dataset."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    run_id,
                    dataset_id,
                    status,
                    started_at,
                    completed_at,
                    error_message
                FROM ingestion_runs
                WHERE dataset_id = ?
                ORDER BY started_at ASC, run_id ASC
                """,
                (dataset_id.value,),
            ).fetchall()

        return [self._map_to_run(row) for row in rows]

    def get_by_status(
        self,
        status: IngestionStatus,
    ) -> list[IngestionRun]:
        """Retrieve all ingestion runs with a given status."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    run_id,
                    dataset_id,
                    status,
                    started_at,
                    completed_at,
                    error_message
                FROM ingestion_runs
                WHERE status = ?
                ORDER BY started_at ASC, run_id ASC
                """,
                (status.value,),
            ).fetchall()

        return [self._map_to_run(row) for row in rows]

    def _initialize_database(self) -> None:
        """Create the ingestion runs table and indexes if necessary."""
        with self._connection() as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ingestion_runs (
                        run_id TEXT PRIMARY KEY,
                        dataset_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT,
                        error_message TEXT
                    )
                    """
                )

                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_ingestion_runs_dataset_id
                    ON ingestion_runs(dataset_id)
                    """
                )

                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status
                    ON ingestion_runs(status)
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
    def _map_to_run(row: tuple[object, ...]) -> IngestionRun:
        """Reconstruct an ingestion run from a database row."""
        (
            run_id,
            dataset_id,
            status,
            started_at,
            completed_at,
            error_message,
        ) = row

        if not isinstance(run_id, str):
            raise ValueError("Invalid ingestion run ID in database.")

        if not isinstance(dataset_id, str):
            raise ValueError("Invalid dataset ID in database.")

        if not isinstance(status, str):
            raise ValueError("Invalid ingestion status in database.")

        if started_at is not None and not isinstance(started_at, str):
            raise ValueError("Invalid start timestamp in database.")

        if completed_at is not None and not isinstance(completed_at, str):
            raise ValueError("Invalid completion timestamp in database.")

        if error_message is not None and not isinstance(error_message, str):
            raise ValueError("Invalid error message in database.")

        return IngestionRun.reconstitute(
            dataset_id=DatasetId(dataset_id),
            run_id=UUID(run_id),
            status=IngestionStatus(status),
            started_at=(datetime.fromisoformat(started_at) if started_at is not None else None),
            completed_at=(
                datetime.fromisoformat(completed_at) if completed_at is not None else None
            ),
            error_message=error_message,
        )
