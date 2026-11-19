class IngestionRunNotFoundError(Exception):
    """Raised when an ingestion run cannot be found."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Ingestion run '{run_id}' was not found.")
