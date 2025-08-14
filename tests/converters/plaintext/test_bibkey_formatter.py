from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey
from philoch_bib_sdk.logic.models import BibKeyAttr, MaybeStr


def test_bibkey_formatter() -> None:

    bibkey: MaybeStr[BibKeyAttr]

    bibkey = BibKeyAttr(first_author="aristotle", other_authors="etal", date=300, date_suffix="a")
    assert format_bibkey(bibkey) == "aristotle-etal:300a"

    bibkey = BibKeyAttr("aristotle", "", 300, "")
    assert format_bibkey(bibkey) == "aristotle:300"

    bibkey = BibKeyAttr("bordogarcia_l", "", "forthcoming", "1")
    assert format_bibkey(bibkey) == "bordogarcia_l:forthcoming-1"

    bibkey = BibKeyAttr("bordogarcia_l", "olivadoti_s", 2027, "z2")
    assert format_bibkey(bibkey) == "bordogarcia_l-olivadoti_s:2027z2"

    bibkey = ""
    assert format_bibkey(bibkey) == ""
