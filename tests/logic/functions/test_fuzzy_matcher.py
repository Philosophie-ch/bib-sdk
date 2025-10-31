"""Tests for fuzzy BibItem matching with blocking indexes."""

from philoch_bib_sdk.logic.default_models import default_bib_item
from philoch_bib_sdk.logic.functions.fuzzy_matcher import (
    BibItemBlockIndex,
    build_index,
    find_similar_bibitems,
    stage_bibitem,
    stage_bibitems_batch,
)
from philoch_bib_sdk.logic.models_staging import BibItemStaged, Match, ScoreComponent


def test_build_index_empty() -> None:
    """Test building index with empty sequence."""
    index = build_index(())
    assert isinstance(index, BibItemBlockIndex)
    assert len(index.all_items) == 0
    assert len(index.doi_index) == 0


def test_build_index_single_item() -> None:
    """Test building index with single item."""
    item = default_bib_item(
        title={"simplified": "The Republic"},
        author=(
            {
                "given_name": {"simplified": "Plato"},
                "family_name": {"simplified": ""},
            },
        ),
        date={"year": 1997},
    )
    index = build_index((item,))

    assert len(index.all_items) == 1
    assert len(index.title_trigrams) > 0  # Should have "the", "he ", "e r", etc.
    assert len(index.year_decades) == 1
    assert 1990 in index.year_decades


def test_build_index_with_doi() -> None:
    """Test that DOI index works correctly."""
    item1 = default_bib_item(
        title={"simplified": "Article with DOI"},
        doi="10.1234/example",
    )
    item2 = default_bib_item(
        title={"simplified": "Article without DOI"},
    )

    index = build_index((item1, item2))

    assert "10.1234/example" in index.doi_index
    assert index.doi_index["10.1234/example"] == item1


def test_find_similar_exact_doi_match() -> None:
    """Test that DOI provides instant exact match."""
    existing = default_bib_item(
        title={"simplified": "The Original Article"},
        doi="10.1234/exact",
        date={"year": 2020},
    )

    subject = default_bib_item(
        title={"simplified": "The Original Article (Different Title)"},
        doi="10.1234/exact",
        date={"year": 2020},
    )

    index = build_index((existing,))
    matches = find_similar_bibitems(subject, index, top_n=5)

    assert len(matches) == 1
    assert matches[0].matched_bibitem == existing
    assert matches[0].rank == 1
    # DOI match should give very high score
    assert matches[0].total_score > 50  # Weighted by 0.1, so 100 * 0.1 = 10, but other fields add up


def test_find_similar_exact_title_author_match() -> None:
    """Test matching with identical title and author."""
    existing = default_bib_item(
        title={"simplified": "The Republic"},
        author=(
            {
                "given_name": {"simplified": ""},
                "family_name": {"simplified": "Plato"},
            },
        ),
        date={"year": 1997},
    )

    subject = default_bib_item(
        title={"simplified": "The Republic"},
        author=(
            {
                "given_name": {"simplified": ""},
                "family_name": {"simplified": "Plato"},
            },
        ),
        date={"year": 1997},
    )

    index = build_index((existing,))
    matches = find_similar_bibitems(subject, index, top_n=1)

    assert len(matches) == 1
    assert matches[0].matched_bibitem == existing
    assert matches[0].total_score > 100  # High score for exact match


def test_find_similar_50_year_gap() -> None:
    """Test that reprints with 50-year gap are still found."""
    original = default_bib_item(
        title={"simplified": "Metaphysics"},
        author=(
            {
                "given_name": {"simplified": ""},
                "family_name": {"simplified": "Aristotle"},
            },
        ),
        date={"year": 1950},
    )

    reprint = default_bib_item(
        title={"simplified": "Metaphysics"},
        author=(
            {
                "given_name": {"simplified": ""},
                "family_name": {"simplified": "Aristotle"},
            },
        ),
        date={"year": 2000},
    )

    index = build_index((original,))
    matches = find_similar_bibitems(reprint, index, top_n=1)

    assert len(matches) == 1
    assert matches[0].matched_bibitem == original
    # Should match on title and author despite year gap
    assert matches[0].total_score > 80  # High score from title+author


def test_find_similar_dirty_title() -> None:
    """Test matching with dirty characters in title."""
    existing = default_bib_item(
        title={"simplified": "Analysis of Quantum Effects"},
        author=(
            {
                "given_name": {"simplified": "John"},
                "family_name": {"simplified": "Smith"},
            },
        ),
    )

    dirty = default_bib_item(
        title={"simplified": "**Analysis of Quantum Effects"},  # Garbage chars
        author=(
            {
                "given_name": {"simplified": "John"},
                "family_name": {"simplified": "Smith"},
            },
        ),
    )

    index = build_index((existing,))
    matches = find_similar_bibitems(dirty, index, top_n=1)

    assert len(matches) == 1
    assert matches[0].matched_bibitem == existing
    # Should still match despite dirty chars
    assert matches[0].total_score > 50


def test_find_similar_top_n() -> None:
    """Test that top_n parameter works correctly."""
    items = tuple(
        default_bib_item(
            title={"simplified": f"Similar Title {i}"},
            author=(
                {
                    "given_name": {"simplified": "Author"},
                    "family_name": {"simplified": f"Name{i}"},
                },
            ),
        )
        for i in range(10)
    )

    subject = default_bib_item(
        title={"simplified": "Similar Title"},
        author=(
            {
                "given_name": {"simplified": "Author"},
                "family_name": {"simplified": "Name"},
            },
        ),
    )

    index = build_index(items)

    # Test top_n=3
    matches = find_similar_bibitems(subject, index, top_n=3)
    assert len(matches) == 3
    assert matches[0].rank == 1
    assert matches[1].rank == 2
    assert matches[2].rank == 3

    # Scores should be descending
    assert matches[0].total_score >= matches[1].total_score
    assert matches[1].total_score >= matches[2].total_score


def test_find_similar_min_score() -> None:
    """Test that min_score filtering works."""
    good_match = default_bib_item(
        title={"simplified": "The Republic"},
        author=(
            {
                "given_name": {"simplified": ""},
                "family_name": {"simplified": "Plato"},
            },
        ),
    )

    poor_match = default_bib_item(
        title={"simplified": "Completely Different Book"},
        author=(
            {
                "given_name": {"simplified": "John"},
                "family_name": {"simplified": "Doe"},
            },
        ),
    )

    subject = default_bib_item(
        title={"simplified": "The Republic"},
        author=(
            {
                "given_name": {"simplified": ""},
                "family_name": {"simplified": "Plato"},
            },
        ),
    )

    index = build_index((good_match, poor_match))

    # With high min_score, should only get good match
    matches = find_similar_bibitems(subject, index, top_n=5, min_score=80.0)

    assert len(matches) >= 1
    assert matches[0].matched_bibitem == good_match
    # Verify all returned matches meet threshold
    for match in matches:
        assert match.total_score >= 80.0


def test_match_structure() -> None:
    """Test that Match object has correct structure."""
    item = default_bib_item(
        title={"simplified": "Test Article"},
        author=(
            {
                "given_name": {"simplified": "Test"},
                "family_name": {"simplified": "Author"},
            },
        ),
    )

    index = build_index((item,))
    matches = find_similar_bibitems(item, index, top_n=1)

    assert len(matches) == 1
    match = matches[0]

    # Check Match structure
    assert isinstance(match, Match)
    assert isinstance(match.bibkey, str)  # Should be a formatted string
    assert match.matched_bibitem == item
    assert isinstance(match.total_score, float)
    assert match.rank == 1
    assert len(match.partial_scores) == 4  # title, author, date, bonus

    # Check PartialScore components
    components = {ps.component for ps in match.partial_scores}
    assert ScoreComponent.TITLE in components
    assert ScoreComponent.AUTHOR in components
    assert ScoreComponent.DATE in components

    # Check to_json_summary works
    json_summary = match.to_json_summary()
    assert "bibkey" in json_summary
    assert "total_score" in json_summary
    assert "score_breakdown" in json_summary


def test_stage_bibitem() -> None:
    """Test staging a single BibItem."""
    existing = default_bib_item(
        title={"simplified": "Existing Article"},
    )

    subject = default_bib_item(
        title={"simplified": "Existing Article"},
    )

    index = build_index((existing,))
    staged = stage_bibitem(subject, index, top_n=5)

    assert isinstance(staged, BibItemStaged)
    assert staged.bibitem == subject
    assert len(staged.top_matches) >= 1
    assert "search_time_ms" in staged.search_metadata
    assert "candidates_searched" in staged.search_metadata
    assert staged.search_metadata["search_time_ms"] >= 0


def test_stage_bibitem_csv_export() -> None:
    """Test CSV export functionality."""
    existing = default_bib_item(
        title={"simplified": "Test Article"},
        author=(
            {
                "given_name": {"simplified": "John"},
                "family_name": {"simplified": "Doe"},
            },
        ),
        date={"year": 2020},
    )

    subject = default_bib_item(
        title={"simplified": "Test Article"},
        author=(
            {
                "given_name": {"simplified": "John"},
                "family_name": {"simplified": "Doe"},
            },
        ),
        date={"year": 2020},
    )

    index = build_index((existing,))
    staged = stage_bibitem(subject, index, top_n=3)

    csv_row = staged.to_csv_row()

    # Check CSV structure
    assert "staged_bibkey" in csv_row
    assert "staged_title" in csv_row
    assert "staged_author" in csv_row
    assert "staged_year" in csv_row
    assert "num_matches" in csv_row
    assert "best_match_score" in csv_row
    assert "best_match_bibkey" in csv_row
    assert "top_matches_json" in csv_row
    assert "search_time_ms" in csv_row
    assert "candidates_searched" in csv_row

    # Check values
    assert isinstance(csv_row["staged_bibkey"], str)
    assert csv_row["staged_title"] == "Test Article"
    assert csv_row["staged_year"] == "2020"
    num_matches = csv_row["num_matches"]
    assert isinstance(num_matches, int) and num_matches >= 1
    assert isinstance(csv_row["top_matches_json"], str)  # Should be JSON string


def test_stage_bibitems_batch() -> None:
    """Test batch staging of multiple BibItems."""
    existing = tuple(
        default_bib_item(
            title={"simplified": f"Article {i}"},
        )
        for i in range(5)
    )

    subjects = tuple(
        default_bib_item(
            title={"simplified": f"Article {i}"},
        )
        for i in range(3)
    )

    index = build_index(existing)
    staged_batch = stage_bibitems_batch(subjects, index, top_n=2)

    assert len(staged_batch) == 3
    assert all(isinstance(s, BibItemStaged) for s in staged_batch)
    assert all(len(s.top_matches) <= 2 for s in staged_batch)


def test_performance_large_dataset() -> None:
    """Test performance with larger dataset (1000 items)."""
    # Create 1000 items with varied titles
    large_dataset = tuple(
        default_bib_item(
            title={"simplified": f"Research on Topic {i % 100} Part {i // 100}"},
            author=(
                {
                    "given_name": {"simplified": f"Author{i % 50}"},
                    "family_name": {"simplified": f"Surname{i % 30}"},
                },
            ),
            date={"year": 1990 + (i % 30)},
        )
        for i in range(1000)
    )

    subject = default_bib_item(
        title={"simplified": "Research on Topic 42 Part 5"},
        author=(
            {
                "given_name": {"simplified": "Author42"},
                "family_name": {"simplified": "Surname12"},
            },
        ),
        date={"year": 2012},
    )

    # Build index
    index = build_index(large_dataset)

    # Search should complete in reasonable time
    staged = stage_bibitem(subject, index, top_n=5)

    # Should complete in less than 5 seconds (5000ms)
    assert staged.search_metadata["search_time_ms"] < 5000

    # Should reduce candidate set or search all items
    assert staged.search_metadata["candidates_searched"] <= 1000

    # Should find top matches
    assert len(staged.top_matches) > 0


def test_missing_dates_handled() -> None:
    """Test that missing dates don't break matching."""
    with_date = default_bib_item(
        title={"simplified": "Article Title"},
        date={"year": 2020},
    )

    without_date = default_bib_item(
        title={"simplified": "Article Title"},
        # date defaults to "no date"
    )

    index = build_index((with_date,))
    matches = find_similar_bibitems(without_date, index, top_n=1)

    # Should still find match based on title
    assert len(matches) == 1
    assert matches[0].matched_bibitem == with_date


def test_empty_authors_handled() -> None:
    """Test that empty authors don't break matching."""
    with_author = default_bib_item(
        title={"simplified": "Article Title"},
        author=(
            {
                "given_name": {"simplified": "John"},
                "family_name": {"simplified": "Doe"},
            },
        ),
    )

    without_author = default_bib_item(
        title={"simplified": "Article Title"},
        author=(),  # Empty tuple
    )

    index = build_index((with_author,))
    matches = find_similar_bibitems(without_author, index, top_n=1)

    # Should still find match based on title
    assert len(matches) == 1
    assert matches[0].matched_bibitem == with_author
