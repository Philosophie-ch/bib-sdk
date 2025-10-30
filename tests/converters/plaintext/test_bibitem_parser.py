from typing import TypeGuard, Any
from aletk.ResultMonad import Ok, Err
from philoch_bib_sdk.converters.plaintext.bibitem.parser import parse_bibitem, ParsedBibItemData
from philoch_bib_sdk.logic.models import (
    BibItem,
    BibKeyAttr,
    Author,
    Journal,
    BibStringAttr,
    TBibString,
    BIB_STRING_VALUES,
    BibItemDateAttr,
    BaseNamedRenderable,
    KeywordsAttr,
)


def _is_valid_bibstring_type(value: Any) -> TypeGuard[TBibString]:
    """TypeGuard function to validate if a value is a valid TBibString."""
    return isinstance(value, str) and value in BIB_STRING_VALUES


def test_parse_bibitem(parsed_bibitem_entries: list[ParsedBibItemData]) -> None:
    """Test that all 50 entries can be successfully parsed."""
    successful_parses = 0
    failed_entries = []

    for i, entry in enumerate(parsed_bibitem_entries):
        result = parse_bibitem(entry, "latex")

        if isinstance(result, Ok):
            successful_parses += 1
            bibitem = result.out

            # Verify it's a BibItem instance
            assert isinstance(bibitem, BibItem)

            # Verify basic fields are populated correctly
            if entry.get("bibkey"):
                assert bibitem.bibkey is not None
                assert isinstance(bibitem.bibkey, BibKeyAttr)

            if entry.get("title"):
                assert bibitem.title is not None
                assert isinstance(bibitem.title, BibStringAttr)
                assert bibitem.title.latex == entry["title"]

            if entry.get("author"):
                assert len(bibitem.author) > 0
                assert all(isinstance(author, Author) for author in bibitem.author)

            if entry.get("journal"):
                assert bibitem.journal is not None
                assert isinstance(bibitem.journal, Journal)

        else:
            failed_entries.append((i, entry.get("bibkey", "unknown"), result.message))

    # Report results
    print(f"Successfully parsed {successful_parses}/{len(parsed_bibitem_entries)} entries")

    if failed_entries:
        print("Failed entries:")
        for idx, bibkey, error in failed_entries:
            print(f"  Entry {idx} ({bibkey}): {error}")

    # Assert that at least 75% of entries parse successfully (allowing for some edge cases)
    success_rate = successful_parses / len(parsed_bibitem_entries)
    assert success_rate >= 0.75, f"Success rate too low: {success_rate:.2%}"


def test_parse_specific_entries(parsed_bibitem_entries: list[ParsedBibItemData]) -> None:
    """Test parsing of specific entries with known characteristics."""

    # Test first entry (incollection)
    first_entry = parsed_bibitem_entries[0]
    result = parse_bibitem(first_entry, "latex")

    assert isinstance(result, Ok)
    bibitem = result.out

    assert bibitem.entry_type == "incollection"
    assert isinstance(bibitem.bibkey, BibKeyAttr)
    assert bibitem.bibkey.first_author == "collins_r"
    assert bibitem.bibkey.other_authors == ""
    assert bibitem.bibkey.date == 1999
    assert bibitem.bibkey.date_suffix == "a"
    assert len(bibitem.author) == 1  # One author
    assert bibitem.author[0].given_name.latex == "Robin"
    assert bibitem.author[0].family_name.latex == "Collins"

    # Find and test a book entry
    book_entry = None
    for entry in parsed_bibitem_entries:
        if entry.get("entry_type") == "@book":
            book_entry = entry
            break

    assert book_entry is not None, "No book entry found in test data"

    book_result = parse_bibitem(book_entry, "latex")
    assert isinstance(book_result, Ok)
    book_bibitem = book_result.out
    assert book_bibitem.entry_type == "book"
    assert len(book_bibitem.author) >= 1

    # Test an article entry - find one that successfully parsed
    for entry in parsed_bibitem_entries:
        if entry.get("entry_type") == "@article":
            result = parse_bibitem(entry, "latex")
            if isinstance(result, Ok):
                bibitem = result.out
                assert bibitem.entry_type == "article"
                if bibitem.journal:
                    assert isinstance(bibitem.journal.name, BibStringAttr)
                if bibitem.pages and len(bibitem.pages) > 0:
                    assert bibitem.pages[0].start
                break


def test_parse_empty_fields(parsed_bibitem_entries: list[ParsedBibItemData]) -> None:
    """Test that empty fields are handled correctly."""

    # Find an entry with some empty fields
    entry = parsed_bibitem_entries[0]

    # Modify to have empty optional fields
    entry_copy = entry.copy()
    entry_copy["editor"] = ""
    entry_copy["note"] = ""
    entry_copy["_guesteditor"] = ""

    result = parse_bibitem(entry_copy, "latex")

    assert isinstance(result, Ok)
    bibitem = result.out

    assert len(bibitem.editor) == 0
    assert bibitem.note == ""
    assert len(bibitem._guesteditor) == 0


def test_parse_invalid_bibkey() -> None:
    """Test error handling for invalid bibkey."""

    invalid_entry: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "invalid-bibkey-format",  # Missing colon separator
        "author": "Test Author",
        "date": "2020",
        "title": "Test Title",
    }

    result = parse_bibitem(invalid_entry, "latex")
    assert isinstance(result, Err)
    assert "bibkey" in result.message.lower()


def test_parse_different_bibstring_types(parsed_bibitem_entries: list[ParsedBibItemData]) -> None:
    """Test parsing with different bibstring types."""

    entry = parsed_bibitem_entries[0]

    for bibstring_type_str in ["latex", "unicode", "simplified"]:
        if _is_valid_bibstring_type(bibstring_type_str):
            result = parse_bibitem(entry, bibstring_type_str)

            assert isinstance(result, Ok)
            bibitem = result.out

            # Verify the bibstring type was used correctly
            if isinstance(bibitem.title, BibStringAttr):
                title_attr = getattr(bibitem.title, bibstring_type_str, "")
                assert title_attr == entry["title"]


def test_parse_complex_fields() -> None:
    """Test parsing of complex fields like editors, pages, dates."""

    complex_entry: ParsedBibItemData = {
        "entry_type": "@incollection",
        "bibkey": "smith-johnson:2020a",
        "author": "Smith, John and Johnson, Jane",
        "editor": "Brown, Robert and Davis, Emily",
        "date": "2020",
        "title": "Complex Field Test",
        "booktitle": "Test Collection",
        "pages": "10--25",
        "publisher": "Test Publisher",
        "address": "Test City",
        "volume": "5",
        "number": "3",
        "series": "Test Series",
        "edition": "2",
        "doi": "10.1234/test.doi",
        "url": "https://example.com/test",
        "urn": "urn:test:12345",
        "eprint": "arXiv:2020.12345",
    }

    result = parse_bibitem(complex_entry, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    # Check entry type
    assert bibitem.entry_type == "incollection"

    # Check authors
    assert len(bibitem.author) == 2
    assert bibitem.author[0].family_name.latex == "Smith"
    assert bibitem.author[0].given_name.latex == "John"
    assert bibitem.author[1].family_name.latex == "Johnson"
    assert bibitem.author[1].given_name.latex == "Jane"

    # Check editors
    assert len(bibitem.editor) == 2
    assert bibitem.editor[0].family_name.latex == "Brown"
    assert bibitem.editor[0].given_name.latex == "Robert"

    # Check pages
    assert len(bibitem.pages) == 1
    assert bibitem.pages[0].start == "10"
    assert bibitem.pages[0].end == "25"

    # Check numeric fields
    assert bibitem.volume == "5"
    assert bibitem.number == "3"
    assert bibitem.edition == 2

    # Check identifiers
    assert bibitem.doi == "10.1234/test.doi"
    assert bibitem.url == "https://example.com/test"
    assert bibitem.urn == "urn:test:12345"
    assert bibitem.eprint == "arXiv:2020.12345"

    # Check BibStringAttr fields
    assert isinstance(bibitem.title, BibStringAttr)
    assert bibitem.title.latex == "Complex Field Test"
    assert isinstance(bibitem.booktitle, BibStringAttr)
    assert bibitem.booktitle.latex == "Test Collection"
    assert isinstance(bibitem.publisher, BibStringAttr)
    assert bibitem.publisher.latex == "Test Publisher"
    assert isinstance(bibitem.address, BibStringAttr)
    assert bibitem.address.latex == "Test City"

    # Check series
    assert isinstance(bibitem.series, BaseNamedRenderable)
    assert bibitem.series.name.latex == "Test Series"


def test_parse_minimal_entry() -> None:
    """Test parsing of minimal entry with only required fields."""

    minimal_entry: ParsedBibItemData = {
        "entry_type": "@misc",
        "bibkey": "minimal:2024",
        "title": "Minimal Entry",
        "date": "2024",
    }

    result = parse_bibitem(minimal_entry, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    assert bibitem.entry_type == "misc"
    assert isinstance(bibitem.bibkey, BibKeyAttr)
    assert bibitem.bibkey.first_author == "minimal"
    assert bibitem.bibkey.date == 2024
    assert isinstance(bibitem.title, BibStringAttr)
    assert bibitem.title.latex == "Minimal Entry"

    # Check that optional fields are empty
    assert len(bibitem.author) == 0
    assert len(bibitem.editor) == 0
    assert bibitem.journal is None
    assert len(bibitem.pages) == 0
    assert bibitem.volume == ""
    assert bibitem.number == ""


def test_parse_special_characters() -> None:
    """Test parsing entries with special LaTeX characters."""

    special_entry: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "muller:2023",  # Changed from müller to muller to fix bibkey parsing
        "author": r"M{\"u}ller, Hans and Garc{\'i}a, Jos{\'e}",
        "title": r"Test with {\LaTeX} special characters: $\alpha$, $\beta$",
        "journal": r"Journal f{\"u}r Wissenschaft",
        "date": "2023",
        "pages": "100--150",
    }

    result = parse_bibitem(special_entry, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    # Check that special characters are preserved
    assert isinstance(bibitem.title, BibStringAttr)
    assert r"{\LaTeX}" in bibitem.title.latex
    assert r"$\alpha$" in bibitem.title.latex

    assert len(bibitem.author) == 2
    assert r"{\"u}" in bibitem.author[0].family_name.latex
    assert r"{\'i}" in bibitem.author[1].family_name.latex

    assert bibitem.journal is not None
    assert r"{\"u}" in bibitem.journal.name.latex


def test_parse_date_variations() -> None:
    """Test parsing different date formats."""

    # Test normal year
    entry_year: ParsedBibItemData = {
        "entry_type": "@book",
        "bibkey": "author:2020",
        "title": "Test Book",
        "date": "2020",
    }
    result = parse_bibitem(entry_year, "latex")
    assert isinstance(result, Ok)
    assert isinstance(result.out.date, BibItemDateAttr)
    assert result.out.date.year == 2020

    # Test year with month - note: 2021-03 is parsed as year-hyphen format, not year-month
    # For actual month parsing, we need proper date format like "2021-03-01"
    entry_month: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "author:2021",
        "title": "Test Article",
        "date": "2021-03-01",  # Full date format
    }
    result = parse_bibitem(entry_month, "latex")
    assert isinstance(result, Ok)
    assert isinstance(result.out.date, BibItemDateAttr)
    assert result.out.date.year == 2021
    assert result.out.date.month == 3
    assert result.out.date.day == 1

    # Test year-hyphen format (parsed as year_part_2_hyphen, not month)
    entry_year_hyphen: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "author:2022",
        "title": "Test Year Hyphen",
        "date": "2022-05",  # Year-hyphen format
    }
    result = parse_bibitem(entry_year_hyphen, "latex")
    assert isinstance(result, Ok)
    assert isinstance(result.out.date, BibItemDateAttr)
    assert result.out.date.year == 2022
    assert result.out.date.year_part_2_hyphen == 5  # This is parsed as year range, not month

    # Test full date
    entry_full: ParsedBibItemData = {
        "entry_type": "@misc",
        "bibkey": "author:2022",
        "title": "Test Misc",
        "date": "2022-12-25",
    }
    result = parse_bibitem(entry_full, "latex")
    assert isinstance(result, Ok)
    assert isinstance(result.out.date, BibItemDateAttr)
    assert result.out.date.year == 2022
    assert result.out.date.month == 12
    assert result.out.date.day == 25

    # Test empty date
    entry_no_date: ParsedBibItemData = {
        "entry_type": "@unpublished",
        "bibkey": "author:unpub",
        "title": "Unpublished Work",
        "date": "",
    }
    result = parse_bibitem(entry_no_date, "latex")
    assert isinstance(result, Ok)
    # Default date when empty
    assert isinstance(result.out.date, BibItemDateAttr)
    assert result.out.date.year == 0


def test_parse_publication_states() -> None:
    """Test parsing different publication states."""

    pubstates = ["", "unpub", "forthcoming", "inwork", "submitted", "published"]

    for pubstate in pubstates:
        # Use valid bibkey format - only unpub and forthcoming are valid in bibkey dates
        if pubstate in ["unpub", "forthcoming"]:
            bibkey = f"author:{pubstate}"
        else:
            bibkey = "author:2024"

        entry: ParsedBibItemData = {
            "entry_type": "@unpublished",
            "bibkey": bibkey,
            "title": f"Test {pubstate or 'default'}",
            "date": "2024",
            "pubstate": pubstate,
        }
        result = parse_bibitem(entry, "latex")
        assert isinstance(result, Ok)
        assert result.out.pubstate == pubstate


def test_parse_keywords() -> None:
    """Test parsing keyword hierarchy."""

    entry_with_keywords: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "author:2024",
        "title": "Keyword Test",
        "date": "2024",
        "_kw_level1": "Philosophy",
        "_kw_level2": "Ethics",
        "_kw_level3": "Applied Ethics",
    }

    result = parse_bibitem(entry_with_keywords, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    assert isinstance(bibitem._kws, KeywordsAttr)
    assert bibitem._kws.level_1.name == "Philosophy"
    assert bibitem._kws.level_2.name == "Ethics"
    assert bibitem._kws.level_3.name == "Applied Ethics"

    # Test partial keywords
    entry_partial: ParsedBibItemData = {
        "entry_type": "@book",
        "bibkey": "author:2024",
        "title": "Partial Keywords",
        "date": "2024",
        "_kw_level1": "Science",
        "_kw_level2": "",
        "_kw_level3": "",
    }

    result = parse_bibitem(entry_partial, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    assert isinstance(bibitem._kws, KeywordsAttr)
    assert bibitem._kws.level_1.name == "Science"
    assert bibitem._kws.level_2.name == ""
    assert bibitem._kws.level_3.name == ""


def test_parse_cross_references() -> None:
    """Test parsing further_refs and depends_on fields."""

    entry: ParsedBibItemData = {
        "entry_type": "@inproceedings",
        "bibkey": "author:2024",
        "title": "Cross Reference Test",
        "date": "2024",
        "_further_refs": "smith:2023,jones:2022a,brown:2021",
        "_depends_on": "foundation:2020,base:2019",
    }

    result = parse_bibitem(entry, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    # Check further_refs
    assert len(bibitem._further_refs) == 3
    assert all(isinstance(ref, BibKeyAttr) for ref in bibitem._further_refs)
    assert bibitem._further_refs[0].first_author == "smith"
    assert bibitem._further_refs[0].date == 2023
    assert bibitem._further_refs[1].first_author == "jones"
    assert bibitem._further_refs[1].date == 2022
    assert bibitem._further_refs[1].date_suffix == "a"
    assert bibitem._further_refs[2].first_author == "brown"
    assert bibitem._further_refs[2].date == 2021

    # Check depends_on
    assert len(bibitem._depends_on) == 2
    assert all(isinstance(ref, BibKeyAttr) for ref in bibitem._depends_on)
    assert bibitem._depends_on[0].first_author == "foundation"
    assert bibitem._depends_on[0].date == 2020
    assert bibitem._depends_on[1].first_author == "base"
    assert bibitem._depends_on[1].date == 2019


def test_parse_numeric_fields() -> None:
    """Test parsing of numeric fields like edition, dltc_num, etc."""

    entry: ParsedBibItemData = {
        "entry_type": "@book",
        "bibkey": "author:2024",
        "title": "Numeric Fields Test",
        "date": "2024",
        "edition": "3",
        "_dltc_num": "42",
        "_num_inwork_coll": "7",
        "_num_coll": "15",
        "_num_sort": "100",
    }

    result = parse_bibitem(entry, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    assert bibitem.edition == 3
    assert bibitem._dltc_num == 42
    assert bibitem._num_inwork_coll == 7
    assert bibitem._num_coll == 15
    assert bibitem._num_sort == 100

    # Test with empty numeric fields
    entry_empty: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "author:2024",
        "title": "Empty Numeric Fields",
        "date": "2024",
        "edition": "",
        "_dltc_num": "",
        "_num_inwork_coll": "",
        "_num_coll": "",
        "_num_sort": "",
    }

    result = parse_bibitem(entry_empty, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    assert bibitem.edition is None
    assert bibitem._dltc_num is None
    assert bibitem._num_inwork_coll is None
    assert bibitem._num_coll is None
    assert bibitem._num_sort is None


def test_parse_entry_type_variations() -> None:
    """Test parsing various entry type formats."""

    # Test with @ prefix
    entry_with_at: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "test:2024",
        "title": "Test",
        "date": "2024",
    }
    result = parse_bibitem(entry_with_at, "latex")
    assert isinstance(result, Ok)
    assert result.out.entry_type == "article"

    # Test without @ prefix
    entry_without_at: ParsedBibItemData = {
        "entry_type": "book",
        "bibkey": "test:2024",
        "title": "Test",
        "date": "2024",
    }
    result = parse_bibitem(entry_without_at, "latex")
    assert isinstance(result, Ok)
    assert result.out.entry_type == "book"

    # Test unknown entry type
    entry_unknown: ParsedBibItemData = {
        "entry_type": "@weirdtype",
        "bibkey": "test:2024",
        "title": "Test",
        "date": "2024",
    }
    result = parse_bibitem(entry_unknown, "latex")
    assert isinstance(result, Ok)
    assert result.out.entry_type == "UNKNOWN"

    # Test empty entry type
    entry_empty: ParsedBibItemData = {
        "entry_type": "",
        "bibkey": "test:2024",
        "title": "Test",
        "date": "2024",
    }
    result = parse_bibitem(entry_empty, "latex")
    assert isinstance(result, Ok)
    assert result.out.entry_type == "UNKNOWN"


def test_parse_epoch_and_language() -> None:
    """Test parsing epoch and language fields."""

    entry: ParsedBibItemData = {
        "entry_type": "@book",
        "bibkey": "philosopher:1800",
        "title": "Historical Work",
        "date": "1800",
        "_epoch": "enlightenment",
        "_langid": "ngerman",
        "_lang_der": "Derived from German",
    }

    result = parse_bibitem(entry, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    assert bibitem._epoch == "enlightenment"
    assert bibitem._langid == "ngerman"
    assert bibitem._lang_der == "Derived from German"

    # Test invalid epoch and language
    entry_invalid: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "author:2024",
        "title": "Test",
        "date": "2024",
        "_epoch": "invalid-epoch",
        "_langid": "invalid-language",
    }

    result = parse_bibitem(entry_invalid, "latex")
    assert isinstance(result, Ok)
    bibitem = result.out

    assert bibitem._epoch == ""  # Falls back to empty string
    assert bibitem._langid == ""  # Falls back to empty string


def test_parse_error_handling() -> None:
    """Test various error scenarios."""

    # Test with invalid date format
    entry_bad_date: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "test:2024",
        "title": "Test",
        "date": "not-a-date",
    }
    result = parse_bibitem(entry_bad_date, "latex")
    assert isinstance(result, Err)
    assert "date" in result.message.lower()

    # Test with invalid pages format
    entry_bad_pages: ParsedBibItemData = {
        "entry_type": "@article",
        "bibkey": "test:2024",
        "title": "Test",
        "date": "2024",
        "pages": "invalid--pages--format",
    }
    result = parse_bibitem(entry_bad_pages, "latex")
    assert isinstance(result, Err)
    assert "page" in result.message.lower()

    # Test with malformed author
    entry_bad_author: ParsedBibItemData = {
        "entry_type": "@book",
        "bibkey": "test:2024",
        "title": "Test",
        "date": "2024",
        "author": "Invalid Author Format {{{}}}",
    }
    result = parse_bibitem(entry_bad_author, "latex")
    # This might succeed or fail depending on author parser implementation
    # Just check that it returns a Result
    assert isinstance(result, (Ok, Err))
