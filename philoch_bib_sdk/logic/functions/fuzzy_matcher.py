"""High-performance fuzzy matching for BibItems using blocking indexes.

This module provides efficient fuzzy matching against large bibliographies (100k+ items)
by using multi-index blocking to reduce the search space before applying detailed scoring.
"""

import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any, DefaultDict, FrozenSet, Iterator, Sequence, Tuple

from aletk.utils import remove_extra_whitespace
from cytoolz import topk

from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey
from philoch_bib_sdk.logic.functions.comparator import compare_bibitems_detailed
from philoch_bib_sdk.logic.models import BibItem, BibItemDateAttr, TBibString
from philoch_bib_sdk.logic.models_staging import BibItemStaged, Match

if TYPE_CHECKING:
    from philoch_bib_sdk.logic.models import Author


class BibItemBlockIndex:
    """Multi-index structure for fast candidate retrieval.

    Uses multiple overlapping indexes (DOI, title n-grams, author surnames, year decades,
    journal names) to quickly find potential matches without excluding items due to dirty data.

    Attributes:
        doi_index: Exact DOI lookup for instant matches
        title_trigrams: Title n-gram index for fuzzy title matching
        author_surnames: Author surname index for author matching
        year_decades: Year grouped by decade (with None for missing)
        journals: Journal name index
        all_items: Complete tuple of all items (fallback)
    """

    def __init__(
        self,
        doi_index: dict[str, BibItem],
        title_trigrams: dict[str, FrozenSet[BibItem]],
        author_surnames: dict[str, FrozenSet[BibItem]],
        year_decades: dict[int | None, FrozenSet[BibItem]],
        journals: dict[str, FrozenSet[BibItem]],
        all_items: Tuple[BibItem, ...],
    ) -> None:
        self.doi_index = doi_index
        self.title_trigrams = title_trigrams
        self.author_surnames = author_surnames
        self.year_decades = year_decades
        self.journals = journals
        self.all_items = all_items


def _extract_trigrams(text: str) -> FrozenSet[str]:
    """Extract 3-character n-grams from text for fuzzy matching.

    Args:
        text: Input text to extract trigrams from

    Returns:
        Frozen set of trigrams (immutable for hashing)
    """
    normalized = remove_extra_whitespace(text).lower()
    if len(normalized) < 3:
        return frozenset()
    return frozenset(normalized[i : i + 3] for i in range(len(normalized) - 2))


def _extract_author_surnames(authors: Tuple["Author", ...]) -> FrozenSet[str]:
    """Extract author surnames for indexing.

    Args:
        authors: Tuple of Author objects

    Returns:
        Frozen set of normalized surnames
    """
    from philoch_bib_sdk.logic.models import Author, BibStringAttr

    if not authors:
        return frozenset()

    surnames: list[str] = []
    for author in authors:
        if isinstance(author, Author):
            family_name_attr = author.family_name
            if isinstance(family_name_attr, BibStringAttr) and family_name_attr.simplified:
                surnames.append(remove_extra_whitespace(family_name_attr.simplified).lower())

    return frozenset(surnames)


def _get_decade(date: BibItemDateAttr | str) -> int | None:
    """Get the decade from a date attribute.

    Args:
        date: BibItemDateAttr or "no date"

    Returns:
        Decade as integer (e.g., 1990) or None if no date
    """
    if date == "no date":
        return None
    if isinstance(date, BibItemDateAttr):
        return (date.year // 10) * 10
    return None


def _prepare_items_for_rust(bibitems: Sequence[BibItem]) -> list[dict[str, Any]]:
    """Extract minimal data needed by Rust build_index_rust.

    Args:
        bibitems: Sequence of BibItems to prepare

    Returns:
        List of dicts with minimal data for Rust
    """
    from philoch_bib_sdk.logic.models import BibStringAttr

    items_data = []
    for i, item in enumerate(bibitems):
        # Extract title string
        title_attr = item.title
        if isinstance(title_attr, BibStringAttr):
            title = title_attr.simplified
        else:
            title = str(title_attr) if title_attr else ""

        # Extract author surnames
        author_surnames = list(_extract_author_surnames(item.author))

        # Extract year
        decade = _get_decade(item.date)
        year = decade if decade is not None else None

        # Extract journal name
        journal_name = None
        if item.journal:
            journal_name_attr = item.journal.name
            if isinstance(journal_name_attr, BibStringAttr):
                journal_name = remove_extra_whitespace(journal_name_attr.simplified).lower()

        items_data.append(
            {
                "item_index": i,
                "doi": item.doi if item.doi else None,
                "title": title,
                "author_surnames": author_surnames,
                "year": year,
                "journal_name": journal_name,
            }
        )

    return items_data


def _reconstruct_index_from_rust(index_data: Any, items: Tuple[BibItem, ...]) -> BibItemBlockIndex:
    """Reconstruct BibItemBlockIndex from Rust IndexData.

    Args:
        index_data: IndexData object from Rust
        items: Tuple of original BibItems

    Returns:
        BibItemBlockIndex with all indexes built
    """
    # Convert Rust index mappings back to Python objects using original BibItems
    doi_index = {doi: items[idx] for doi, idx in index_data.doi_to_index.items()}

    title_trigrams = {
        trigram: frozenset(items[idx] for idx in indices) for trigram, indices in index_data.trigram_to_indices.items()
    }

    author_surnames = {
        surname: frozenset(items[idx] for idx in indices) for surname, indices in index_data.surname_to_indices.items()
    }

    year_decades = {
        decade: frozenset(items[idx] for idx in indices) for decade, indices in index_data.decade_to_indices.items()
    }

    journals = {
        name: frozenset(items[idx] for idx in indices) for name, indices in index_data.journal_to_indices.items()
    }

    return BibItemBlockIndex(
        doi_index=doi_index,
        title_trigrams=title_trigrams,
        author_surnames=author_surnames,
        year_decades=year_decades,
        journals=journals,
        all_items=items,
    )


def _build_index_python(bibitems: Tuple[BibItem, ...]) -> BibItemBlockIndex:
    """Pure Python implementation of build_index (fallback).

    Creates overlapping indexes to handle dirty data gracefully while maintaining
    fast lookup performance. No pre-filtering means no data loss.

    Optimized for performance:
    - Single-pass indexing (one loop instead of 5)
    - Deferred frozenset conversion (only at the end)
    - Reduced memory allocations

    Args:
        bibitems: Tuple of BibItems to index

    Returns:
        BibItemBlockIndex with all indexes built
    """
    from philoch_bib_sdk.logic.models import BibStringAttr

    # Initialize all index structures
    doi_index: dict[str, BibItem] = {}
    title_trigram_map: DefaultDict[str, set[BibItem]] = defaultdict(set)
    author_surname_map: DefaultDict[str, set[BibItem]] = defaultdict(set)
    year_decade_map: DefaultDict[int | None, set[BibItem]] = defaultdict(set)
    journal_map: DefaultDict[str, set[BibItem]] = defaultdict(set)

    # Single pass over all items - build all indexes at once
    for item in bibitems:
        # DOI index
        if item.doi:
            doi_index[item.doi] = item

        # Title trigram index
        title_attr = item.title
        if isinstance(title_attr, BibStringAttr):
            trigrams = _extract_trigrams(title_attr.simplified)
            for trigram in trigrams:
                title_trigram_map[trigram].add(item)

        # Author surname index
        surnames = _extract_author_surnames(item.author)
        for surname in surnames:
            author_surname_map[surname].add(item)

        # Year decade index
        decade = _get_decade(item.date)
        year_decade_map[decade].add(item)

        # Journal index
        if item.journal:
            journal_name_attr = item.journal.name
            if isinstance(journal_name_attr, BibStringAttr):
                journal_name = remove_extra_whitespace(journal_name_attr.simplified).lower()
                if journal_name:
                    journal_map[journal_name].add(item)

    # Convert sets to frozensets only at the end (single pass per index)
    title_trigrams = {trigram: frozenset(items) for trigram, items in title_trigram_map.items()}
    author_surnames = {surname: frozenset(items) for surname, items in author_surname_map.items()}
    year_decades = {decade: frozenset(items) for decade, items in year_decade_map.items()}
    journals = {name: frozenset(items) for name, items in journal_map.items()}

    return BibItemBlockIndex(
        doi_index=doi_index,
        title_trigrams=title_trigrams,
        author_surnames=author_surnames,
        year_decades=year_decades,
        journals=journals,
        all_items=bibitems,
    )


def build_index(bibitems: Sequence[BibItem]) -> BibItemBlockIndex:
    """Build multi-index structure for fast fuzzy matching.

    Creates overlapping indexes to handle dirty data gracefully while maintaining
    fast lookup performance. No pre-filtering means no data loss.

    Uses Rust implementation when available (100x faster), falls back to Python.

    Args:
        bibitems: Sequence of BibItems to index

    Returns:
        BibItemBlockIndex with all indexes built
    """
    # Try to use Rust implementation
    try:
        from philoch_bib_sdk._rust import build_index_rust  # type: ignore[import-not-found]

        use_rust = True
    except ImportError:
        use_rust = False

    # Convert to tuple for immutability
    items_tuple = tuple(bibitems)

    if use_rust:
        # Fast path: use Rust
        items_data = _prepare_items_for_rust(items_tuple)
        index_data = build_index_rust(items_data)
        return _reconstruct_index_from_rust(index_data, items_tuple)
    else:
        # Fallback: pure Python
        return _build_index_python(items_tuple)


def _get_candidate_set(subject: BibItem, index: BibItemBlockIndex) -> FrozenSet[BibItem]:
    """Get candidate items from index using multiple lookup strategies.

    Combines results from multiple indexes to create a candidate set that's
    much smaller than the full bibliography but still comprehensive.

    Args:
        subject: BibItem to find candidates for
        index: BibItemBlockIndex to search

    Returns:
        Frozen set of candidate BibItems (typically 0.5-2% of total)
    """
    candidates: set[BibItem] = set()

    from philoch_bib_sdk.logic.models import BibStringAttr

    # Check DOI first (instant exact match)
    if subject.doi and subject.doi in index.doi_index:
        return frozenset([index.doi_index[subject.doi]])

    # Title trigrams
    title_attr = subject.title
    if isinstance(title_attr, BibStringAttr):
        subject_trigrams = _extract_trigrams(title_attr.simplified)
        for trigram in subject_trigrams:
            if trigram in index.title_trigrams:
                candidates.update(index.title_trigrams[trigram])

    # Author surnames
    subject_surnames = _extract_author_surnames(subject.author)
    for surname in subject_surnames:
        if surname in index.author_surnames:
            candidates.update(index.author_surnames[surname])

    # Year decades (±5 decades = ±50 years for safety)
    subject_decade = _get_decade(subject.date)
    if subject_decade is not None:
        for offset in range(-5, 6):
            decade = subject_decade + (offset * 10)
            if decade in index.year_decades:
                candidates.update(index.year_decades[decade])
    else:
        # No date: include all items with no date
        if None in index.year_decades:
            candidates.update(index.year_decades[None])

    # Journal
    from philoch_bib_sdk.logic.models import BibStringAttr

    if subject.journal:
        journal_name_attr = subject.journal.name
        if isinstance(journal_name_attr, BibStringAttr):
            journal_name = remove_extra_whitespace(journal_name_attr.simplified).lower()
            if journal_name and journal_name in index.journals:
                candidates.update(index.journals[journal_name])

    # Fallback: if no candidates found, use all items (rare but safe)
    if not candidates:
        return frozenset(index.all_items)

    return frozenset(candidates)


def find_similar_bibitems(
    subject: BibItem,
    index: BibItemBlockIndex,
    top_n: int = 5,
    min_score: float = 0.0,
    bibstring_type: TBibString = "simplified",
) -> Tuple[Match, ...]:
    """Find top N most similar BibItems using fuzzy matching.

    Uses blocking indexes to reduce search space, then applies detailed
    fuzzy scoring to find the best matches.

    Args:
        subject: BibItem to find matches for
        index: Pre-built BibItemBlockIndex
        top_n: Number of top matches to return (default: 5)
        min_score: Minimum score threshold (default: 0.0)
        bibstring_type: Which bibstring variant to use (default: "simplified")

    Returns:
        Tuple of Match objects with detailed scoring, sorted by score (best first)
    """
    # Get candidate set from indexes
    candidates = _get_candidate_set(subject, index)

    # Score all candidates (generator for memory efficiency)
    scored_items = (
        (
            candidate,
            compare_bibitems_detailed(candidate, subject, bibstring_type),
        )
        for candidate in candidates
    )

    # Calculate total scores
    with_totals = (
        (candidate, partial_scores, sum(ps.weighted_score for ps in partial_scores))
        for candidate, partial_scores in scored_items
    )

    # Filter by minimum score
    filtered = (
        (candidate, partial_scores, total_score)
        for candidate, partial_scores, total_score in with_totals
        if total_score >= min_score
    )

    # Get top N using cytoolz (heap-based, efficient)
    top_results = tuple(topk(top_n, filtered, key=lambda x: x[2]))

    # Convert to Match objects
    return tuple(
        Match(
            bibkey=format_bibkey(candidate.bibkey),
            matched_bibitem=candidate,
            total_score=total_score,
            partial_scores=partial_scores,
            rank=rank,
        )
        for rank, (candidate, partial_scores, total_score) in enumerate(top_results, start=1)
    )


def stage_bibitem(
    bibitem: BibItem,
    index: BibItemBlockIndex,
    top_n: int = 5,
    min_score: float = 0.0,
) -> BibItemStaged:
    """Stage a single BibItem with its top matches.

    Args:
        bibitem: BibItem to stage
        index: Pre-built BibItemBlockIndex
        top_n: Number of top matches to find (default: 5)
        min_score: Minimum score threshold (default: 0.0)

    Returns:
        BibItemStaged with top matches and search metadata
    """
    start_time = time.perf_counter()
    candidates = _get_candidate_set(bibitem, index)
    top_matches = find_similar_bibitems(bibitem, index, top_n, min_score)
    end_time = time.perf_counter()

    search_metadata = {
        "search_time_ms": int((end_time - start_time) * 1000),
        "candidates_searched": len(candidates),
    }

    return BibItemStaged(
        bibitem=bibitem,
        top_matches=top_matches,
        search_metadata=search_metadata,
    )


def stage_bibitems_batch(
    bibitems: Sequence[BibItem],
    index: BibItemBlockIndex,
    top_n: int = 5,
    min_score: float = 0.0,
) -> Tuple[BibItemStaged, ...]:
    """Stage multiple BibItems in batch.

    Args:
        bibitems: Sequence of BibItems to stage
        index: Pre-built BibItemBlockIndex
        top_n: Number of top matches per item (default: 5)
        min_score: Minimum score threshold (default: 0.0)

    Returns:
        Tuple of BibItemStaged objects
    """
    return tuple(stage_bibitem(bibitem, index, top_n, min_score) for bibitem in bibitems)


def stage_bibitems_streaming(
    bibitems: Sequence[BibItem],
    index: BibItemBlockIndex,
    top_n: int = 5,
    min_score: float = 0.0,
) -> Iterator[BibItemStaged]:
    """Stage multiple BibItems with streaming results.

    Yields BibItemStaged objects one at a time as they're processed,
    enabling real-time progress monitoring and immediate CSV output.

    Args:
        bibitems: Sequence of BibItems to stage
        index: Pre-built BibItemBlockIndex
        top_n: Number of top matches per item (default: 5)
        min_score: Minimum score threshold (default: 0.0)

    Yields:
        BibItemStaged objects as they're processed
    """
    for bibitem in bibitems:
        yield stage_bibitem(bibitem, index, top_n, min_score)
