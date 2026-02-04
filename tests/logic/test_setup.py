# from philoch_bib_sdk.logic.functions import author_full_name
from philoch_bib_sdk.logic.default_models import default_author, AuthorArgs


def test_slotted_classes_are_slotted() -> None:
    data: AuthorArgs = {"given_name": {"latex": "John"}, "family_name": {"latex": "Doe"}}
    author = default_author(**data)
    assert "__dict__" not in author.__slots__


# def test_author_full_name() -> None:
# author = Author(given_name="John", family_name="Doe")
# full_name = author_full_name(author)

# assert full_name == "Doe, John"
