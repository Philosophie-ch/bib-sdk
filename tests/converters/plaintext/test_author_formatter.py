from typing import List
import pytest

from philoch_bib_sdk.converters.plaintext.author.formatter import _format_single, _full_name_generic, format_author
from philoch_bib_sdk.logic.default_models import AuthorArgs, default_author
from philoch_bib_sdk.logic.models import TBibString
from tests.shared import TTestCase


@pytest.mark.parametrize(
    "given_name, family_name, mononym, expected",
    [
        # If given_name is "" but family_name exists, return family_name
        ("", "Doe", "", "Doe"),
        # If family_name is "", return given_name
        ("John", "", "", "John"),
        # If both are "", return ""
        ("", "", "", ""),
        # If both are not "", return "family_name, given_name"
        ("John", "Doe", "", "Doe, John"),
        # If there's a mononym, return it and ignore the other fields
        ("Name", "Family", "Aristotle", "Aristotle"),
    ],
)
def test_full_name_generic(given_name: str, family_name: str, mononym: str, expected: str) -> None:
    assert _full_name_generic(given_name, family_name, mononym) == expected


full_name_cases: TTestCase[AuthorArgs, TBibString, str] = [
    # simplified cases
    ({}, "simplified", ""),
    ({"given_name": {"simplified": "John"}}, "simplified", "John"),
    ({"family_name": {"simplified": "Doe"}}, "simplified", "Doe"),
    ({"given_name": {"simplified": "John"}, "family_name": {"simplified": "Doe"}}, "simplified", "Doe, John"),
    # Latex cases
    ({}, "simplified", ""),
    ({"given_name": {"latex": "John"}}, "latex", "John"),
    ({"family_name": {"latex": "Doe"}}, "latex", "Doe"),
    ({"given_name": {"latex": "John"}, "family_name": {"latex": "Doe"}}, "latex", "Doe, John"),
]


@pytest.mark.parametrize(
    "author_data, bibstring_type, expected",
    full_name_cases,
)
def test_full_name_single_author(author_data: AuthorArgs, bibstring_type: TBibString, expected: str) -> None:
    author = default_author(**author_data)
    assert _format_single(author, bibstring_type) == expected


# Simplified name cases
john_simplified: AuthorArgs = {"given_name": {"simplified": "John"}}
jane_simplified: AuthorArgs = {"given_name": {"simplified": "Jane"}}
joe_simplified: AuthorArgs = {"given_name": {"simplified": "Joe"}}
doe_family_simplified: AuthorArgs = {"family_name": {"simplified": "Doe"}}
john_doe_simplified: AuthorArgs = {"given_name": {"simplified": "John"}, "family_name": {"simplified": "Doe"}}
jane_doe_simplified: AuthorArgs = {"given_name": {"simplified": "Jane"}, "family_name": {"simplified": "Doe"}}
doe_id_simplified: AuthorArgs = {**doe_family_simplified, "id": 3}

# LaTeX name cases
john_latex: AuthorArgs = {"given_name": {"latex": "John"}}
jane_latex: AuthorArgs = {"given_name": {"latex": "Jane"}}
joe_latex: AuthorArgs = {"given_name": {"latex": "Joe"}}
doe_family_latex: AuthorArgs = {"family_name": {"latex": "Doe"}}
john_doe_latex: AuthorArgs = {"given_name": {"latex": "John"}, "family_name": {"latex": "Doe"}}
jane_doe_latex: AuthorArgs = {"given_name": {"latex": "Jane"}, "family_name": {"latex": "Doe"}}
joe_doe_latex: AuthorArgs = {"given_name": {"latex": "Joe"}, "family_name": {"latex": "Doe"}}

# Parameterized test cases using pytest.param for clarity
full_name_list_cases: TTestCase[List[AuthorArgs], TBibString, str] = [
    ([], "simplified", ""),  # 0
    ([john_simplified], "simplified", "John"),  # 1
    ([john_simplified, jane_simplified], "simplified", "John and Jane"),  # 2
    ([john_simplified, jane_simplified, joe_simplified], "simplified", "John and Jane and Joe"),  # 3
    (
        [john_doe_simplified, jane_doe_simplified, doe_family_simplified],
        "simplified",
        "Doe, John and Doe, Jane and Doe",
    ),  # 4
    (
        [{**john_doe_simplified, "id": 1}, {**jane_doe_simplified, "id": 2}, doe_id_simplified],
        "simplified",
        "Doe, John and Doe, Jane and Doe",
    ),  # 5
    ([john_latex, jane_latex], "latex", "John and Jane"),  # 6
    ([john_latex, jane_latex, joe_latex], "latex", "John and Jane and Joe"),  # 7
    ([john_doe_latex, jane_doe_latex, joe_doe_latex], "latex", "Doe, John and Doe, Jane and Doe, Joe"),  # 8
]


@pytest.mark.parametrize("author_attrs_list, bibstring_type, expected", full_name_list_cases)
def test_full_name_author_list(author_attrs_list: List[AuthorArgs], bibstring_type: TBibString, expected: str) -> None:
    authors_list = tuple(default_author(**author_attrs) for author_attrs in author_attrs_list)
    assert format_author(authors_list, bibstring_type=bibstring_type) == expected
