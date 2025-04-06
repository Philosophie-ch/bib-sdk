import pytest

from aletk.ResultMonad import Ok, Err
from philoch_bib_sdk.converters.plaintext.bibitem.date_formatter import format_date
from philoch_bib_sdk.converters.plaintext.bibitem.date_parser import parse_date


date_cases = [
    "no date",
    "2023",
    "2023-10-01",
    "2023-2024",
    "2024/2025",
]


@pytest.mark.parametrize(
    "date_str",
    date_cases,
)
def test_date_parser(date_str: str) -> None:
    date_res = parse_date(date_str)

    assert isinstance(date_res, Ok)
    assert date_str == format_date(date_res.out)


invalid_date_cases = [
    "2023-10-01-01",
    "2023-2024-01",
    "2024/2025/01",
    "2023//2025",
    "2023-10-01-01",
    "2023-10-01/01",
    "2023/10/01",
    "2023/10/01/01",
    "2023-2025/01",
]


@pytest.mark.parametrize(
    "date_str",
    invalid_date_cases,
)
def test_date_parser_invalid(date_str: str) -> None:
    date_res = parse_date(date_str)

    assert isinstance(date_res, Err)
