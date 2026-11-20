from contextlib import AbstractContextManager
from typing import BinaryIO

from japan_tourism.application.models.stored_artifact import StoredArtifact
from japan_tourism.application.ports.artifact_reader import ArtifactReader


def test_concrete_implementation_satisfies_artifact_reader_protocol() -> None:
    class FakeArtifactReader:
        def open(
            self,
            artifact: StoredArtifact,
        ) -> AbstractContextManager[BinaryIO]:
            raise NotImplementedError

    reader: ArtifactReader = FakeArtifactReader()

    assert isinstance(reader, FakeArtifactReader)


def test_artifact_reader_exposes_open_method() -> None:
    assert callable(getattr(ArtifactReader, "open", None))
