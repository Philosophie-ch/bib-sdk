from typing import Tuple
from philoch_bib_sdk.converters.plaintext.bibitem.pages_formatter import format_pages
from philoch_bib_sdk.logic.models import PageAttr


def test_pages_formatter() -> None:

    pages_empty: Tuple[PageAttr, ...] = tuple()
    assert format_pages(pages_empty) == ""

    pages_1 = PageAttr(start="1", end="2")
    assert format_pages((pages_1,)) == "1--2"

    pages_2 = PageAttr(start="10", end="")
    assert format_pages((pages_2,)) == "10"

    pages_3 = PageAttr(start="50", end="100")

    pages = (pages_1, pages_2, pages_3)
    assert format_pages(pages) == "1--2, 10, 50--100"
