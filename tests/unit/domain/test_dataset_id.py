import pytest

from japan_tourism.domain.value_objects.dataset_id import DatasetId


def test_dataset_id_accepts_valid_identifier() -> None:
    dataset_id = DatasetId("accommodation_foreign_guest_nights")

    assert dataset_id.value == "accommodation_foreign_guest_nights"
    assert str(dataset_id) == "accommodation_foreign_guest_nights"


def test_dataset_id_is_immutable() -> None:
    dataset_id = DatasetId("tourism_statistics")

    with pytest.raises(AttributeError):
        setattr(dataset_id, "value", "other_dataset")  # noqa: B010


@pytest.mark.parametrize(
    "value",
    [
        "",
        "Accommodation",
        "accommodation-foreign-guests",
        "123_dataset",
        "dataset name",
    ],
)
def test_dataset_id_rejects_invalid_identifier(value: str) -> None:
    with pytest.raises(ValueError):
        DatasetId(value)
