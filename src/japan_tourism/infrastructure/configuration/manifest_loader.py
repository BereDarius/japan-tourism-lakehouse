from pathlib import Path

import yaml

from japan_tourism.infrastructure.configuration.manifest_models import (
    IngestionManifest,
)


class ManifestFileNotFoundError(FileNotFoundError):
    """Raised when an ingestion manifest file cannot be found."""


class ManifestYamlParseError(ValueError):
    """Raised when an ingestion manifest contains invalid YAML."""


class YamlManifestLoader:
    """Loads YAML ingestion manifests and validates their structure."""

    def load(self, path: Path) -> IngestionManifest:
        """Load and validate an ingestion manifest from a YAML file."""
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise ManifestFileNotFoundError(f"Manifest file not found: {path}") from error

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as error:
            raise ManifestYamlParseError(f"Invalid YAML in manifest file: {path}") from error

        return IngestionManifest.model_validate(data)
