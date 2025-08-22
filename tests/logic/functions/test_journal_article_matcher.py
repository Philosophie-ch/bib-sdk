import pytest
from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_parser import parse_bibkey
from philoch_bib_sdk.logic.default_models import BibItemArgs, default_bib_item
from philoch_bib_sdk.logic.functions.journal_article_matcher import (
    TJournalBibkeyIndex,
    get_bibkey_by_journal_volume_number,
)
from philoch_bib_sdk.logic.models import BibKeyAttr
from tests.shared import TTestCase
from aletk.ResultMonad import Ok


bibkeys_s = ["abell_c:2005a", "abell_c:2007", "abell_c:2009"]
bibkeys_parsed = [parse_bibkey(bibkey) for bibkey in bibkeys_s]
bibkeys = [bibkey.out for bibkey in bibkeys_parsed if isinstance(bibkey, Ok)]


@pytest.fixture
def jvn_index() -> TJournalBibkeyIndex:
    """
    Returns a function that reads a journal volume number index from an ODS file, given the column names.
    """

    jvns = [
        ("Journal of Testing", "1", "1"),
        ("Journal of Testing", "1", "2"),
        ("Journal of Testing", "2", "1"),
    ]

    return {(journal, volume, number): bibkey for (journal, volume, number), bibkey in zip(jvns, bibkeys)}


@pytest.fixture
def empty_jvn_index() -> TJournalBibkeyIndex:
    """
    Returns an empty journal volume number index.
    """
    return {}


var_names = ("bibitem_data", "expected_bibkey")
bibitems: TTestCase[BibItemArgs, BibKeyAttr] = [
    ({"journal": {"name": {"latex": "Journal of Testing"}}, "volume": "1", "number": "1"}, bibkeys[0]),
    ({"journal": {"name": {"latex": "Journal of Testing"}}, "volume": "1", "number": "2"}, bibkeys[1]),
    ({"journal": {"name": {"latex": "Journal of Testing"}}, "volume": "2", "number": "1"}, bibkeys[2]),
]


@pytest.mark.parametrize(
    var_names,
    bibitems,
)
def test_get_bibkey_by_journal_volume_number(
    jvn_index: TJournalBibkeyIndex,
    bibitem_data: BibItemArgs,
    expected_bibkey: BibKeyAttr,
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
    expected_bibkey: BibKeyAttr,
) -> None:
    """
    Tests the get_bibkey_by_journal_volume_number function with an empty index.
    """

    subject = default_bib_item(**bibitem_data)

    with pytest.raises(KeyError):
        get_bibkey_by_journal_volume_number(empty_jvn_index, subject)
