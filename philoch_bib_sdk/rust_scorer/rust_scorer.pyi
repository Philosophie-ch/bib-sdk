"""Type stubs for rust_scorer - high-performance fuzzy matching for BibItems."""

from typing import TypedDict

class BibItemData(TypedDict):
    """Input data for a single BibItem."""

    index: int
    title: str
    author: str
    year: int | None
    doi: str | None
    journal: str | None
    volume: str | None
    number: str | None
    pages: str | None
    publisher: str | None

class MatchResult(TypedDict):
    """Result of scoring a candidate against a subject."""

    candidate_index: int
    total_score: float
    title_score: float
    author_score: float
    date_score: float
    bonus_score: float

class SubjectMatchResult(TypedDict):
    """Result for a single subject with its top matches."""

    subject_index: int
    matches: list[MatchResult]
    candidates_searched: int

def token_sort_ratio(s1: str, s2: str) -> float:
    """Token sort ratio using Jaro-Winkler similarity.

    Args:
        s1: First string to compare
        s2: Second string to compare

    Returns:
        Similarity score from 0.0 to 100.0
    """
    ...

def score_batch(
    subjects: list[BibItemData],
    candidates: list[BibItemData],
    top_n: int,
    min_score: float,
) -> list[SubjectMatchResult]:
    """Batch score multiple subjects against candidates in parallel.

    Args:
        subjects: List of BibItems to find matches for
        candidates: List of BibItems to match against
        top_n: Maximum number of matches to return per subject
        min_score: Minimum score threshold for matches

    Returns:
        List of results, one per subject, containing top matches
    """
    ...
