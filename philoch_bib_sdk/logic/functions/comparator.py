from aletk.utils import get_logger, fuzzy_match_score, remove_extra_whitespace

from typing import TypedDict
from philoch_bib_sdk.converters.plaintext.author.formatter import format_author
from philoch_bib_sdk.logic.models import BibItem, BibItemDateAttr, TBibString


logger = get_logger(__name__)


class BibItemScore(TypedDict):
    score: int
    score_title: int
    score_author: int
    score_year: int


class ScoredBibItems(TypedDict):
    reference: BibItem
    subject: BibItem
    score: BibItemScore


UNDESIRED_TITLE_KEYWORDS = ["errata", "review"]


def _score_title(title_1: str, title_2: str) -> int:

    norm_title_1 = remove_extra_whitespace(title_1).lower()
    norm_title_2 = remove_extra_whitespace(title_2).lower()

    if not norm_title_1 or not norm_title_2:
        raise ValueError("Titles cannot be empty for comparison")

    title_score = fuzzy_match_score(
        norm_title_1,
        norm_title_2,
    )

    # Might catch cases in which one doesn't include the subtitle
    one_included_in_the_other = (norm_title_1 in norm_title_2) or (norm_title_2 in norm_title_1)

    undesired_kws_in_title_1 = {kw for kw in UNDESIRED_TITLE_KEYWORDS if kw in norm_title_1}

    undesired_kws_in_title_2 = {kw for kw in UNDESIRED_TITLE_KEYWORDS if kw in norm_title_2}

    # disjunction
    undesired_kws = undesired_kws_in_title_1.symmetric_difference(undesired_kws_in_title_2)

    undesired_kws_mismatch = True if len(undesired_kws) > 0 else False

    if ((title_score > 85) or one_included_in_the_other) and not undesired_kws_mismatch:
        title_score += 100

    for _ in undesired_kws:
        title_score -= 50

    return title_score


def _score_author(author_1_full_name: str, author_2_full_name: str) -> int:
    stripped_author_1 = remove_extra_whitespace(author_1_full_name)
    stripped_author_2 = remove_extra_whitespace(author_2_full_name)

    if not stripped_author_1 or not stripped_author_2:
        raise ValueError("Authors cannot be empty for comparison")

    author_score = fuzzy_match_score(
        stripped_author_1,
        stripped_author_2,
    )

    if author_score > 85:
        author_score += 100

    return author_score


def _score_year(year_1: int, year_2: int, range_offset: int = 1) -> int:

    if not year_1 or not year_2:
        raise ValueError("Years cannot be empty for comparison")

    if not any(isinstance(year, int) for year in (year_1, year_2)):
        if year_1 == year_2:
            return 100
        else:
            return 0

    range = [year_1 - range_offset, year_1, year_1 + range_offset]

    if year_2 in range:
        return 100
    else:
        return 0


def compare_bibitems(reference: BibItem, subject: BibItem, bibstring_type: TBibString) -> ScoredBibItems:
    """
    Calculate the score of two BibItems based on their title, author, and year.
    The scoring is done using fuzzy matching for title and author, and exact matching for year.
    The final score is a combination of the individual scores.
    """

    logger.debug(f"Scoring bibitems: {reference}, {subject}")

    title_1 = getattr(reference.title, bibstring_type)
    title_2 = getattr(subject.title, bibstring_type)
    title_score = _score_title(title_1, title_2)

    author_1_full_name = format_author(reference.author, bibstring_type)
    author_2_full_name = format_author(subject.author, bibstring_type)

    author_score = _score_author(author_1_full_name, author_2_full_name)

    if isinstance(reference.date, BibItemDateAttr) and isinstance(subject.date, BibItemDateAttr):
        year_1 = reference.date.year
        year_2 = subject.date.year
        year_score = _score_year(year_1, year_2)
    else:
        year_score = 0

    total_score = title_score + author_score + year_score

    return {
        "reference": reference,
        "subject": subject,
        "score": {
            "score": total_score,
            "score_title": title_score,
            "score_author": author_score,
            "score_year": year_score,
        },
    }
