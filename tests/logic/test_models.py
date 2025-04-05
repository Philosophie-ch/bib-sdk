from itertools import product
from typing import List
import pytest

from philoch_bib_sdk.logic.literals import TBasicPubState
from philoch_bib_sdk.logic.models import BibKeyAttr, BibKeyValidationError


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
