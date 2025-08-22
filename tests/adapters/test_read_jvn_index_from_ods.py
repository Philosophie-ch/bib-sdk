from typing import Generator
import pytest
import odswriter as ods
from philoch_bib_sdk.adapters.tabular_data.read_journal_volume_number_index import ColumnNames, hof_read_from_ods
from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_parser import parse_bibkey
from philoch_bib_sdk.logic.functions.journal_article_matcher import TReadIndex
from aletk.ResultMonad import Ok


@pytest.fixture
def column_names() -> ColumnNames:
    return ColumnNames(bibkey="bibkey", journal="journal", volume="volume", number="number")


@pytest.fixture
def get_test_jvn_index(column_names: ColumnNames) -> TReadIndex:
    """
    Returns a function that reads a journal volume number index from an ODS file, given the column names.
    """
    column_names = column_names
    return hof_read_from_ods(column_names)


bibkeys_s = ["abell_c:2005a", "abell_c:2007", "abell_c:2009"]
bibkeys_parsed = [parse_bibkey(bibkey) for bibkey in bibkeys_s]
bibkeys = [bibkey.out for bibkey in bibkeys_parsed if isinstance(bibkey, Ok)]


@pytest.fixture
def write_test_tmp_ods() -> Generator[str, None, None]:
    """
    Returns a temporary ODS file path for testing.
    """
    import tempfile
    import os

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ods")

    rows = [
        ["bibkey", "journal", "volume", "number"],
        [bibkeys_s[0], "Journal of Testing", "1", "1"],
        [bibkeys_s[1], "Journal of Testing", "1", "2"],
        [bibkeys_s[2], "Journal of Testing", "2", "1"],
    ]

    with ods.writer(open(tmp_file.name, "wb")) as odsfile:
        sheet = odsfile.new_sheet("Default", cols=4)
        for row in rows:
            sheet.writerow(row)

    # Ensure the file is removed after the test
    yield tmp_file.name
    try:
        os.remove(tmp_file.name)
    except OSError:
        pass


@pytest.fixture
def empty_ods_file() -> Generator[str, None, None]:
    """
    Returns an empty ODS file path for testing.
    """
    import tempfile
    import os

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ods")

    # Ensure the file is removed after the test
    yield tmp_file.name
    try:
        os.remove(tmp_file.name)
    except OSError:
        pass


def test_read_jvn_index_from_ods(
    get_test_jvn_index: TReadIndex,
    write_test_tmp_ods: str,
) -> None:
    """
    Tests reading a journal volume number index from an ODS file.
    """
    index = get_test_jvn_index(write_test_tmp_ods)

    assert isinstance(index, dict)
    assert len(index) == 3
    assert ("Journal of Testing", "1", "1") in index
    assert index[("Journal of Testing", "1", "1")] == bibkeys[0]
    assert index[("Journal of Testing", "1", "2")] == bibkeys[1]
    assert index[("Journal of Testing", "2", "1")] == bibkeys[2]


def test_read_empty_jvn_index_from_ods(
    get_test_jvn_index: TReadIndex,
    empty_ods_file: str,
) -> None:
    """
    Tests reading an empty journal volume number index from an ODS file.
    """
    with pytest.raises(Exception):
        get_test_jvn_index(empty_ods_file)
