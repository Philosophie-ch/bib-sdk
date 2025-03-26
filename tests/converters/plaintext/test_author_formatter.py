from philoch_bib_sdk.converters.plaintext.author.formatter import _full_name, _full_name_generic, format_author
from philoch_bib_sdk.logic.models import Author


def test_full_name_generic() -> None:
    """
    Desiderata:
    - If given_name is None, return ""
    - If family_name is None, return given_name
    - If both are None, return ""
    - If both are not None, return "family_name, given_name"
    """
    assert _full_name_generic("", "Doe") == ""
    assert _full_name_generic("John", "") == "John"
    assert _full_name_generic("", "") == ""
    assert _full_name_generic("John", "Doe") == "Doe, John"


def test_full_name_single_author() -> None:
    """
    Desiderata:
    - If author is None, return ""
    - If author.given_name is None, return ""
    - If author.family_name is None, return author.given_name
    - If both are not None, return "author.family_name, author.given_name"
    """

    assert _full_name(None) == ""
    assert _full_name(Author()) == ""
    assert _full_name(Author("John")) == "John"
    assert _full_name(Author("", "Doe")) == ""
    assert _full_name(Author("John", "Doe")) == "Doe, John"

    assert _full_name(None, latex=True) == ""
    assert _full_name(Author(), latex=True) == ""
    assert _full_name(Author(given_name_latex="John"), latex=True) == "John"
    assert _full_name(Author(family_name_latex="Doe"), latex=True) == ""
    assert _full_name(Author(given_name_latex="John", family_name_latex="Doe"), latex=True) == "Doe, John"


def test_full_name_author_list() -> None:
    assert format_author(None) == ""
    assert format_author([]) == ""
    assert format_author([Author("John")]) == "John"
    assert format_author([Author("John", "Doe"), Author("Jane")]) == "Doe, John and Jane"
    assert format_author([Author("John"), Author("Jane"), Author("Doe")]) == "John and Jane and Doe"
    assert (
        format_author([Author("John", "Doe"), Author("Jane", "Doe"), Author("Doe", "Doe")])
        == "Doe, John and Doe, Jane and Doe, Doe"
    )
    assert (
        format_author([Author("John", "Doe"), Author("Jane", "Doe"), Author("Doe", "Doe")])
        == "Doe, John and Doe, Jane and Doe, Doe"
    )
    assert (
        format_author([Author("John", "Doe", id=1), Author("Jane", "Doe", id=2), Author("Doe", "Doe", id=3)])
        == "Doe, John and Doe, Jane and Doe, Doe"
    )

    assert (
        format_author([Author(given_name_latex="John"), Author(given_name_latex="Jane")], latex=True) == "John and Jane"
    )
    assert (
        format_author(
            [Author(given_name_latex="John"), Author(given_name_latex="Jane"), Author(given_name_latex="Doe")],
            latex=True,
        )
        == "John and Jane and Doe"
    )
    assert (
        format_author(
            [
                Author(given_name_latex="John", family_name_latex="Doe"),
                Author(given_name_latex="Jane", family_name_latex="Doe"),
                Author(given_name_latex="Doe", family_name_latex="Doe"),
            ],
            latex=True,
        )
        == "Doe, John and Doe, Jane and Doe, Doe"
    )
    assert (
        format_author(
            [
                Author(given_name_latex="John", family_name_latex="Doe"),
                Author(given_name_latex="Jane", family_name_latex="Doe"),
                Author(given_name_latex="Doe", family_name_latex="Doe"),
            ],
            latex=True,
        )
        == "Doe, John and Doe, Jane and Doe, Doe"
    )
