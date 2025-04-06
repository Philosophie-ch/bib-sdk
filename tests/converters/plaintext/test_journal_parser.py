import pytest
from aletk.ResultMonad import Ok

from philoch_bib_sdk.converters.plaintext.journal.parser import parse_journal
from philoch_bib_sdk.logic.default_models import JournalArgs, default_journal
from philoch_bib_sdk.logic.models import TBibString
from tests.shared import TTestCase


journal_cases: TTestCase[str, TBibString, JournalArgs] = [
    # simplified cases
    ("", "simplified", {}),
    ("Journal of Testing", "simplified", {"name": {"simplified": "Journal of Testing"}}),
    ("{Journal} of Testing", "latex", {"name": {"latex": "{Journal} of Testing"}}),
    # LaTeX cases
    ("Journal of Testing", "latex", {"name": {"latex": "Journal of Testing"}}),
    ("Journal of Testing", "unicode", {"name": {"unicode": "Journal of Testing"}}),
]


@pytest.mark.parametrize(
    "journal_str, bibstring_type, expected",
    journal_cases,
)
def test_journal_parse(journal_str: str, bibstring_type: TBibString, expected: JournalArgs) -> None:

    journal_res = parse_journal(journal_str, bibstring_type)
    assert isinstance(journal_res, Ok)

    expected_journal = default_journal(**expected)
    assert expected_journal == journal_res.out
