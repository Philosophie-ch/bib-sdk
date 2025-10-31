from aletk.utils import get_logger, fuzzy_match_score, remove_extra_whitespace

from typing import Tuple, TypedDict
from philoch_bib_sdk.converters.plaintext.author.formatter import format_author
from philoch_bib_sdk.logic.models import BibItem, BibItemDateAttr, TBibString
from philoch_bib_sdk.logic.models_staging import PartialScore, ScoreComponent


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


# Enhanced scoring functions with detailed breakdown for fuzzy matching


def _score_title_detailed(title_1: str, title_2: str, weight: float = 0.5) -> PartialScore:
    """Score title similarity with detailed explanation.

    Args:
        title_1: First title to compare
        title_2: Second title to compare
        weight: Weight to apply to the score (default 0.5 = 50%)

    Returns:
        PartialScore with raw score, weight, and explanation
    """
    norm_title_1 = remove_extra_whitespace(title_1).lower()
    norm_title_2 = remove_extra_whitespace(title_2).lower()

    if not norm_title_1 or not norm_title_2:
        return PartialScore(
            component=ScoreComponent.TITLE,
            score=0,
            weight=weight,
            weighted_score=0.0,
            details="Empty title(s)",
        )

    raw_score = fuzzy_match_score(norm_title_1, norm_title_2)

    # Bonuses and penalties
    one_included_in_other = (norm_title_1 in norm_title_2) or (norm_title_2 in norm_title_1)

    undesired_kws_1 = frozenset(kw for kw in UNDESIRED_TITLE_KEYWORDS if kw in norm_title_1)
    undesired_kws_2 = frozenset(kw for kw in UNDESIRED_TITLE_KEYWORDS if kw in norm_title_2)
    undesired_kws_mismatch = undesired_kws_1.symmetric_difference(undesired_kws_2)

    final_score = raw_score
    details_parts = [f"Fuzzy: {raw_score}"]

    if (raw_score > 85 or one_included_in_other) and not undesired_kws_mismatch:
        final_score += 100
        details_parts.append("High similarity bonus: +100")

    if undesired_kws_mismatch:
        penalty = len(undesired_kws_mismatch) * 50
        final_score -= penalty
        details_parts.append(f"Undesired keyword mismatch: -{penalty}")

    return PartialScore(
        component=ScoreComponent.TITLE,
        score=final_score,
        weight=weight,
        weighted_score=final_score * weight,
        details="; ".join(details_parts),
    )


def _score_author_detailed(author_1: str, author_2: str, weight: float = 0.3) -> PartialScore:
    """Score author similarity with detailed explanation.

    Args:
        author_1: First author string to compare
        author_2: Second author string to compare
        weight: Weight to apply to the score (default 0.3 = 30%)

    Returns:
        PartialScore with raw score, weight, and explanation
    """
    stripped_1 = remove_extra_whitespace(author_1)
    stripped_2 = remove_extra_whitespace(author_2)

    if not stripped_1 or not stripped_2:
        return PartialScore(
            component=ScoreComponent.AUTHOR,
            score=0,
            weight=weight,
            weighted_score=0.0,
            details="Empty author(s)",
        )

    raw_score = fuzzy_match_score(stripped_1, stripped_2)
    final_score = raw_score

    details_parts = [f"Fuzzy: {raw_score}"]

    if raw_score > 85:
        final_score += 100
        details_parts.append("High similarity bonus: +100")

    return PartialScore(
        component=ScoreComponent.AUTHOR,
        score=final_score,
        weight=weight,
        weighted_score=final_score * weight,
        details="; ".join(details_parts),
    )


def _score_date_detailed(
    date_1: BibItemDateAttr | str, date_2: BibItemDateAttr | str, weight: float = 0.1
) -> PartialScore:
    """Score date similarity with detailed explanation.

    Handles date ranges, missing dates, and flexible matching.

    Args:
        date_1: First date (BibItemDateAttr or "no date")
        date_2: Second date (BibItemDateAttr or "no date")
        weight: Weight to apply to the score (default 0.1 = 10%)

    Returns:
        PartialScore with raw score, weight, and explanation
    """
    # Handle missing dates
    if date_1 == "no date" or date_2 == "no date":
        return PartialScore(
            component=ScoreComponent.DATE,
            score=0,
            weight=weight,
            weighted_score=0.0,
            details="Missing date(s)",
        )

    # Both are BibItemDateAttr
    if not isinstance(date_1, BibItemDateAttr) or not isinstance(date_2, BibItemDateAttr):
        return PartialScore(
            component=ScoreComponent.DATE,
            score=0,
            weight=weight,
            weighted_score=0.0,
            details="Invalid date type",
        )

    year_1 = date_1.year
    year_2 = date_2.year

    # Exact match
    if year_1 == year_2:
        return PartialScore(
            component=ScoreComponent.DATE,
            score=100,
            weight=weight,
            weighted_score=100.0 * weight,
            details=f"Exact year match: {year_1}",
        )

    # Flexible matching (±3 years for reprints/editions)
    year_diff = abs(year_1 - year_2)
    if year_diff <= 3:
        score = 100 - (year_diff * 10)  # 90, 80, 70 for 1, 2, 3 year diff
        return PartialScore(
            component=ScoreComponent.DATE,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            details=f"Close years: {year_1} vs {year_2} (diff: {year_diff})",
        )

    # Same decade (partial credit)
    if year_1 // 10 == year_2 // 10:
        return PartialScore(
            component=ScoreComponent.DATE,
            score=30,
            weight=weight,
            weighted_score=30.0 * weight,
            details=f"Same decade: {year_1} vs {year_2}",
        )

    # Different years
    return PartialScore(
        component=ScoreComponent.DATE,
        score=0,
        weight=weight,
        weighted_score=0.0,
        details=f"Different years: {year_1} vs {year_2}",
    )


def _score_bonus_fields(reference: BibItem, subject: BibItem, weight: float = 0.1) -> PartialScore:
    """Score bonus fields (DOI, journal+volume+number, pages, publisher).

    Args:
        reference: Reference BibItem
        subject: Subject BibItem to compare
        weight: Weight to apply to the score (default 0.1 = 10%)

    Returns:
        PartialScore with combined bonus score and details
    """
    bonus_score = 0
    details_parts = []

    # DOI match (highest confidence)
    if reference.doi and subject.doi and reference.doi == subject.doi:
        bonus_score += 100
        details_parts.append("DOI exact match: +100")

    # Journal + Volume + Number match
    if reference.journal and subject.journal:
        ref_journal = reference.journal.name.simplified.lower()
        subj_journal = subject.journal.name.simplified.lower()
        if ref_journal == subj_journal and reference.volume and subject.volume and reference.number and subject.number:
            if reference.volume == subject.volume and reference.number == subject.number:
                bonus_score += 50
                details_parts.append("Journal+Vol+Num match: +50")

    # Pages overlap (same or overlapping page ranges)
    if reference.pages and subject.pages:
        # Simple check: if any page start matches
        ref_pages_str = " ".join(str(p.start) for p in reference.pages)
        subj_pages_str = " ".join(str(p.start) for p in subject.pages)
        if ref_pages_str and subj_pages_str and ref_pages_str == subj_pages_str:
            bonus_score += 20
            details_parts.append("Page match: +20")

    # Publisher match
    if reference.publisher and subject.publisher:
        ref_pub = reference.publisher.simplified.lower()
        subj_pub = subject.publisher.simplified.lower()
        if ref_pub and subj_pub:
            pub_score = fuzzy_match_score(ref_pub, subj_pub)
            if pub_score > 85:
                bonus_score += 10
                details_parts.append("Publisher match: +10")

    return PartialScore(
        component=ScoreComponent.PUBLISHER,  # Using PUBLISHER as generic bonus component
        score=bonus_score,
        weight=weight,
        weighted_score=bonus_score * weight,
        details="; ".join(details_parts) if details_parts else "No bonus matches",
    )


def compare_bibitems_detailed(
    reference: BibItem,
    subject: BibItem,
    bibstring_type: TBibString = "simplified",
    weights: tuple[float, float, float, float] = (0.5, 0.3, 0.1, 0.1),
) -> Tuple[PartialScore, ...]:
    """Compare two BibItems with detailed scoring breakdown.

    Args:
        reference: Reference BibItem to compare against
        subject: Subject BibItem to compare
        bibstring_type: Which bibstring variant to use (default: "simplified")
        weights: Tuple of weights (title, author, date, bonus) - must sum to 1.0

    Returns:
        Tuple of PartialScore objects for each component
    """
    weight_title, weight_author, weight_date, weight_bonus = weights

    # Title scoring - handle both string and BibStringAttr
    from philoch_bib_sdk.logic.models import BibStringAttr

    if isinstance(reference.title, BibStringAttr):
        title_1 = getattr(reference.title, bibstring_type)
    else:
        title_1 = str(reference.title) if reference.title else ""

    if isinstance(subject.title, BibStringAttr):
        title_2 = getattr(subject.title, bibstring_type)
    else:
        title_2 = str(subject.title) if subject.title else ""

    title_partial = _score_title_detailed(title_1, title_2, weight_title)

    # Author scoring
    author_1 = format_author(reference.author, bibstring_type)
    author_2 = format_author(subject.author, bibstring_type)
    author_partial = _score_author_detailed(author_1, author_2, weight_author)

    # Date scoring
    date_partial = _score_date_detailed(reference.date, subject.date, weight_date)

    # Bonus fields scoring
    bonus_partial = _score_bonus_fields(reference, subject, weight_bonus)

    return (title_partial, author_partial, date_partial, bonus_partial)
