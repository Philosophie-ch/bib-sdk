from philoch_bib_sdk.logic.functions.comparator import _score_title


import pytest
from tests.shared import TTestCase


titles: TTestCase[str, str, int] = [
    ("A Study on the Effects of X", "A Study on the Effects of X", 200),
]


@pytest.mark.parametrize(
    "title_1, title_2, expected_score",
    titles,
)
def test_titles_scorer(
    title_1: str,
    title_2: str,
    expected_score: int,
) -> None:
    assert _score_title(title_1, title_2) == expected_score


titles_minimal_score: TTestCase[str, str, int] = [
    ("A Study on the Effects of X", "A Study on the Effects of X: We Found Cool Stuff", 150),
]


@pytest.mark.parametrize(
    "title_1, title_2, expected_score",
    titles_minimal_score,
)
def test_unexact_titles_scorer(
    title_1: str,
    title_2: str,
    expected_score: int,
) -> None:
    assert _score_title(title_1, title_2) >= expected_score


titles_max_score: TTestCase[str, str, int] = [
    ("A Study on the Effects of X", "A Study on the Effects of X: A Review", 100),
]


@pytest.mark.parametrize(
    "title_1, title_2, expected_score",
    titles_max_score,
)
def test_titles_max_scores(
    title_1: str,
    title_2: str,
    expected_score: int,
) -> None:
    assert _score_title(title_1, title_2) <= expected_score
