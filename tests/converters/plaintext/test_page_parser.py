import pytest
from philoch_bib_sdk.converters.plaintext.bibitem.pages_formatter import format_pages
from philoch_bib_sdk.converters.plaintext.bibitem.pages_parser import parse_pages
from aletk.ResultMonad import Ok, Err


pages_cases = [
    "",
    "1--2",
    "10",
    "50--100",
    "1--2, 10, 50--100",
]


@pytest.mark.parametrize(
    "pages_str",
    pages_cases,
)
def test_page_parser(pages_str: str) -> None:
    pages_res = parse_pages(pages_str)

    assert isinstance(pages_res, Ok)
    assert pages_str == format_pages(pages_res.out)


invalid_pages_cases = [
    "1--2--3",
    "10-20",
    "1--2--, 10, 50--100, 200",
    "1-2, 10, 50--100, 200",
]


@pytest.mark.parametrize(
    "pages_str",
    invalid_pages_cases,
)
def test_page_parser_invalid(pages_str: str) -> None:
    pages_res = parse_pages(pages_str)

    assert isinstance(pages_res, Err)
