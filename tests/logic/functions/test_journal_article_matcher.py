import pytest
from philoch_bib_sdk.logic.default_models import BibItemArgs, default_bib_item
from philoch_bib_sdk.logic.functions.journal_article_matcher import (
    TJournalBibkeyIndex,
    get_bibkey_by_journal_volume_number,
)
from tests.shared import TTestCase


@pytest.fixture
def jvn_index() -> TJournalBibkeyIndex:
    """
    Returns a function that reads a journal volume number index from an ODS file, given the column names.
    """

    return {
        ("Journal of Testing", "1", "1"): "bibkey1",
        ("Journal of Testing", "1", "2"): "bibkey2",
        ("Journal of Testing", "2", "1"): "bibkey3",
    }


@pytest.fixture
def empty_jvn_index() -> TJournalBibkeyIndex:
    """
    Returns an empty journal volume number index.
    """
    return {}


var_names = ("bibitem_data", "expected_bibkey")
bibitems: TTestCase[BibItemArgs, str] = [
    ({"journal": {"name": {"latex": "Journal of Testing"}}, "volume": "1", "number": "1"}, "bibkey1"),
    ({"journal": {"name": {"latex": "Journal of Testing"}}, "volume": "1", "number": "2"}, "bibkey2"),
    ({"journal": {"name": {"latex": "Journal of Testing"}}, "volume": "2", "number": "1"}, "bibkey3"),
]


@pytest.mark.parametrize(
    var_names,
    bibitems,
)
def test_get_bibkey_by_journal_volume_number(
    jvn_index: TJournalBibkeyIndex,
    bibitem_data: BibItemArgs,
    expected_bibkey: str,
) -> None:
    """
    Tests the get_bibkey_by_journal_volume_number function with various journal volume number combinations.
    """

    subject = default_bib_item(**bibitem_data)

    assert expected_bibkey == get_bibkey_by_journal_volume_number(jvn_index, subject)


@pytest.mark.parametrize(
    var_names,
    bibitems,
)
def test_get_bibkey_by_journal_volume_number_empty_index(
    empty_jvn_index: TJournalBibkeyIndex,
    bibitem_data: BibItemArgs,
    expected_bibkey: str,
) -> None:
    """
    Tests the get_bibkey_by_journal_volume_number function with an empty index.
    """

    subject = default_bib_item(**bibitem_data)

    with pytest.raises(KeyError):
        get_bibkey_by_journal_volume_number(empty_jvn_index, subject)
