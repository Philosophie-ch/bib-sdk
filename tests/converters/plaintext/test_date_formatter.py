from typing import Dict

import pytest
from philoch_bib_sdk.converters.plaintext.bibitem.date_formatter import format_date
from philoch_bib_sdk.logic.models import BibItemDateAttr
from tests.shared import TTestCase

date_cases: TTestCase[Dict[str, int], str] = [
    ({"year": 2023}, "2023"),
    ({"year": 2023, "month": 10, "day": 1}, "2023-10-01"),
    ({"year": 2023, "year_part_2_hyphen": 2024}, "2023-2024"),
    ({"year": 2024, "year_part_2_slash": 2025}, "2024/2025"),
]


@pytest.mark.parametrize(
    "date_data, expected",
    date_cases,
)
def test_date_formatter(date_data: Dict[str, int], expected: str) -> None:
    date = BibItemDateAttr(**date_data)
    assert format_date(date) == expected


def test_no_date_formatter() -> None:
    assert format_date("no date") == "no date"
