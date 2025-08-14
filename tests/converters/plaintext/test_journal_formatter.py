import pytest
from philoch_bib_sdk.converters.plaintext.journal.formatter import format_journal
from philoch_bib_sdk.logic.default_models import JournalArgs, default_journal
from philoch_bib_sdk.logic.models import MaybeStr, TBibString
from tests.shared import TTestCase


journal_cases: TTestCase[MaybeStr[JournalArgs], TBibString, str] = [
    # simplified cases
    ({}, "simplified", ""),
    ({"name": {"simplified": "Journal of Testing"}}, "simplified", "Journal of Testing"),
    ({"name": {"latex": "Journal of Testing"}}, "latex", "Journal of Testing"),
    # LaTeX cases
    ({"name": {"latex": "{Journal} of Testing"}}, "latex", r"{Journal} of Testing"),
]


@pytest.mark.parametrize(
    "journal_data, bibstring_type, expected",
    journal_cases,
)
def test_journal_formatter(journal_data: JournalArgs, bibstring_type: TBibString, expected: str) -> None:
    journal = default_journal(**journal_data)
    assert format_journal(journal, bibstring_type) == expected
