import attrs

from philoch_bib_sdk.logic.default_models import AuthorArgs, default_author


def test_default_author_defaults() -> None:
    """Test that default_author correctly applies default values when no arguments are given."""
    data: AuthorArgs = {}
    author = default_author(**data)

    assert attrs.asdict(author) == {
        "given_name": {"simplified": "", "latex": "", "unicode": ""},
        "family_name": {"simplified": "", "latex": "", "unicode": ""},
        "mononym": {"simplified": "", "latex": "", "unicode": ""},
        "shorthand": {"simplified": "", "latex": "", "unicode": ""},
        "famous_name": {"simplified": "", "latex": "", "unicode": ""},
        "publications": (),
        "id": None,
    }


def test_default_author_field_assignment() -> None:
    """Test that default_author correctly assigns provided values while keeping defaults for others."""
    data: AuthorArgs = {"given_name": {"simplified": "John"}, "family_name": {"simplified": "Doe"}, "id": 42}
    author = default_author(**data)
    assert author.given_name.simplified == "John"
    assert author.family_name.simplified == "Doe"
    assert author.mononym.simplified == ""
    assert author.shorthand.simplified == ""
    assert author.famous_name.simplified == ""
    assert author.publications == ()


def test_default_author_ignores_invalid_fields() -> None:
    """Test that default_author silently ignores unexpected fields."""
    author = default_author(extra_field="invalid")  # type: ignore
    assert not hasattr(author, "extra_field")
