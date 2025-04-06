from itertools import product
from typing import Dict, List
import pytest

from philoch_bib_sdk.logic.literals import TBasicPubState
from philoch_bib_sdk.logic.models import BibItemDateAttr, BibItemDateValidationError, BibKeyAttr, BibKeyValidationError


first_author_values = ["", "smith"]
other_authors_values = ["", "etal"]
date_values: List[int | TBasicPubState] = ["", 2023, "forthcoming", "unpub"]
date_suffix_values = ["", "a"]

type TBibKeyData = tuple[str, str, int | TBasicPubState, str]

invalid_combinations: List[TBibKeyData] = [
    case
    for case in product(first_author_values, other_authors_values, date_values, date_suffix_values)
    if (
        # No 'other_authors' if 'first_author' is empty
        (not case[0] and case[1])
        or
        # No 'date_suffix' if 'date' is empty
        (not case[2] and case[3])
        or
        # No 'first_author' if 'date' is empty
        (case[0] and not case[2])
        or
        # No 'date' if 'first_author' is empty
        (not case[0] and case[2])
    )
]


@pytest.mark.parametrize("case", invalid_combinations)
def test_bibkey_validators(case: TBibKeyData) -> None:

    with pytest.raises(BibKeyValidationError):
        BibKeyAttr(*case)


invalid_date_cases = [
    # {},
    {"year": 2023, "month": 10},
    {"year": 2023, "day": 1},
    {"year": 2023, "year_part_2_hyphen": 2024, "month": 10},
    {"year": 2023, "year_part_2_slash": 2024, "month": 10},
    {"year": 2023, "year_part_2_hyphen": 2024, "day": 1},
    {"year": 2023, "year_part_2_slash": 2024, "day": 1},
    {"year": 2023, "year_part_2_hyphen": 2024, "year_part_2_slash": 2025},
]


@pytest.mark.parametrize(
    "date_data",
    invalid_date_cases,
)
def test_invalid_date_formatter(
    date_data: Dict[str, int],
) -> None:
    with pytest.raises(BibItemDateValidationError):
        BibItemDateAttr(**date_data)
