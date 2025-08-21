from philoch_bib_sdk.converters.plaintext.bibitem.formatter import format_bibitem
from philoch_bib_sdk.logic.models import BibItem, BibKeyAttr, BibStringAttr, Author, BibItemDateAttr


def test_format_bibitem_minimal() -> None:
    """Test formatting a minimal BibItem."""
    bibitem = BibItem(
        to_do_general="",
        change_request="",
        entry_type="UNKNOWN",
        bibkey="",
        author=(),
        editor=(),
        options=(),
        date="no date",
        pubstate="",
        title=BibStringAttr(),
        booktitle=BibStringAttr(),
        crossref="",
        journal=None,
        volume="",
        number="",
        pages=(),
        eid="",
        series="",
        address=BibStringAttr(),
        institution=BibStringAttr(),
        school=BibStringAttr(),
        publisher=BibStringAttr(),
        type=BibStringAttr(),
        edition=None,
        note=BibStringAttr(),
        issuetitle="",
        guesteditor=(),
        extra_note="",
        urn="",
        eprint="",
        doi="",
        url="",
        kws="",
        epoch="",
        person="",
        comm_for_profile_bib="",
        langid="",
        lang_der="",
        further_refs=(),
        depends_on=(),
        dltc_num=None,
        spec_interest="",
        note_perso="",
        note_stock="",
        note_status="",
        num_inwork_coll=None,
        num_inwork="",
        num_coll=None,
        dltc_copyediting_note="",
        note_missing="",
        num_sort=None,
    )
    formatted = format_bibitem(bibitem)

    assert formatted["entry_type"] == "UNKNOWN"
    assert formatted["bibkey"] == ""
    assert formatted["author"] == ""
    assert formatted["date"] == "no date"


def test_format_bibitem_full() -> None:
    """Test formatting a fully populated BibItem."""
    bibitem = BibItem(
        to_do_general="",
        change_request="",
        entry_type="article",
        bibkey=BibKeyAttr(first_author="sample", other_authors="", date=2023, date_suffix=""),
        author=(
            Author(
                given_name=BibStringAttr(latex="John"),
                family_name=BibStringAttr(latex="Doe"),
                mononym=BibStringAttr(),
                shorthand=BibStringAttr(),
                famous_name=BibStringAttr(),
                publications=(),
            ),
            Author(
                given_name=BibStringAttr(latex="Jane"),
                family_name=BibStringAttr(latex="Smith"),
                mononym=BibStringAttr(),
                shorthand=BibStringAttr(),
                famous_name=BibStringAttr(),
                publications=(),
            ),
        ),
        editor=(),
        options=(),
        date=BibItemDateAttr(year=2023),
        pubstate="",
        title=BibStringAttr(latex="Sample Title"),
        booktitle=BibStringAttr(),
        crossref="",
        journal=None,
        volume="",
        number="",
        pages=(),
        eid="",
        series="",
        address=BibStringAttr(),
        institution=BibStringAttr(),
        school=BibStringAttr(),
        publisher=BibStringAttr(),
        type=BibStringAttr(),
        edition=None,
        note=BibStringAttr(),
        issuetitle="",
        guesteditor=(),
        extra_note="",
        urn="",
        eprint="",
        doi="",
        url="",
        kws="",
        epoch="",
        person="",
        comm_for_profile_bib="",
        langid="",
        lang_der="",
        further_refs=(),
        depends_on=(),
        dltc_num=None,
        spec_interest="",
        note_perso="",
        note_stock="",
        note_status="",
        num_inwork_coll=None,
        num_inwork="",
        num_coll=None,
        dltc_copyediting_note="",
        note_missing="",
        num_sort=None,
    )
    formatted = format_bibitem(bibitem)

    assert formatted["entry_type"] == "@article"
    assert formatted["bibkey"] == "sample:2023"
    assert formatted["author"] == "Doe, John and Smith, Jane"
    assert formatted["date"] == "2023"
    assert formatted["title"] == "Sample Title"
