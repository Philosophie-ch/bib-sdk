"""API format converters for exporting to the Rust Bibliography API.

This module provides data models and converter functions for transforming
bib-sdk BibItem objects to the format expected by the Rust API.
"""

from typing import Literal, Tuple
import attrs

from philoch_bib_sdk.logic.models import (
    Author,
    BibItem,
    BibItemDateAttr,
    BibStringAttr,
    Journal,
    KeywordsAttr,
    PageAttr,
)
from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey
from philoch_bib_sdk.converters.plaintext.bibitem.pages_formatter import format_pages

__all__: list[str] = [
    # Models
    "ApiAuthor",
    "ApiJournal",
    "ApiPublisher",
    "ApiInstitution",
    "ApiSchool",
    "ApiSeries",
    "ApiBibItem",
    "ApiBibItemAuthor",
    "ApiBibItemKeyword",
    # Converters
    "author_to_api",
    "journal_to_api",
    "bibitem_to_api",
    "format_pages_for_api",
]


# =============================================================================
# API Data Models
# =============================================================================


@attrs.define(frozen=True, slots=True)
class ApiAuthor:
    """Author data for API creation."""

    author_key: str
    family_name_latex: str = ""
    family_name_unicode: str = ""
    family_name_simplified: str = ""
    given_name_latex: str = ""
    given_name_unicode: str = ""
    given_name_simplified: str = ""
    mononym_latex: str = ""
    mononym_unicode: str = ""
    mononym_simplified: str = ""


@attrs.define(frozen=True, slots=True)
class ApiJournal:
    """Journal data for API creation."""

    journal_key: str
    name_latex: str = ""
    name_unicode: str = ""
    name_simplified: str = ""
    issn_print: str = ""
    issn_electronic: str = ""


@attrs.define(frozen=True, slots=True)
class ApiPublisher:
    """Publisher data for API creation."""

    publisher_key: str
    name_latex: str = ""
    name_unicode: str = ""
    name_simplified: str = ""
    default_address: str = ""


@attrs.define(frozen=True, slots=True)
class ApiInstitution:
    """Institution data for API creation."""

    institution_key: str
    name_latex: str = ""
    name_unicode: str = ""
    name_simplified: str = ""


@attrs.define(frozen=True, slots=True)
class ApiSchool:
    """School data for API creation."""

    school_key: str
    name_latex: str = ""
    name_unicode: str = ""
    name_simplified: str = ""


@attrs.define(frozen=True, slots=True)
class ApiSeries:
    """Series data for API creation."""

    series_key: str
    name_latex: str = ""
    name_unicode: str = ""
    name_simplified: str = ""


@attrs.define(frozen=True, slots=True)
class ApiBibItem:
    """BibItem data for API creation."""

    bibkey: str
    entry_type: str = ""
    pubstate: str = ""

    # Title fields
    title_latex: str = ""
    title_unicode: str = ""
    title_simplified: str = ""

    # Booktitle fields
    booktitle_latex: str = ""
    booktitle_unicode: str = ""
    booktitle_simplified: str = ""

    # Date fields
    date_year: int | None = None
    date_year_2_hyphen: int | None = None
    date_year_2_slash: int | None = None
    date_month: int | None = None
    date_day: int | None = None
    date_is_no_date: bool = False

    # Entity references (populated after entities are created)
    journal_id: int | None = None
    publisher_id: int | None = None
    institution_id: int | None = None
    school_id: int | None = None
    series_id: int | None = None
    person_id: int | None = None

    # Entity keys (for resolving IDs)
    journal_key: str = ""
    publisher_key: str = ""
    institution_key: str = ""
    school_key: str = ""
    series_key: str = ""
    person_key: str = ""

    # Simple string fields
    volume: str = ""
    number: str = ""
    pages: str = ""
    eid: str = ""
    edition: str = ""
    address: str = ""
    type_field: str = ""

    # Identifiers
    doi: str = ""
    url: str = ""
    urn: str = ""
    eprint: str = ""

    # Crossref
    crossref_bibkey: str = ""

    # Issue and notes
    issuetitle_latex: str = ""
    issuetitle_unicode: str = ""
    note_latex: str = ""
    note_unicode: str = ""
    extra_note_latex: str = ""
    extra_note_unicode: str = ""

    # Enums
    langid: str = ""
    epoch: str = ""

    # Other
    options: str = ""
    shorthand: str = ""
    has_fulltext: bool = False
    fulltext_path: str = ""


@attrs.define(frozen=True, slots=True)
class ApiBibItemAuthor:
    """Represents a link between a BibItem and an Author."""

    bibkey: str
    author_key: str
    role: Literal["author", "editor", "guesteditor"]
    position: int


@attrs.define(frozen=True, slots=True)
class ApiBibItemKeyword:
    """Represents keywords for a BibItem."""

    bibkey: str
    keyword_level_1: str = ""
    keyword_level_2: str = ""
    keyword_level_3: str = ""


# =============================================================================
# Converter Functions
# =============================================================================


def author_to_api(author: Author, author_key: str) -> ApiAuthor:
    """Convert a bib-sdk Author to API format.

    Args:
        author: The Author object from bib-sdk
        author_key: The explicit key for this author (from ODS column)

    Returns:
        ApiAuthor object ready for API creation

    Note:
        The API database has a CHECK constraint requiring `family_name_latex IS NOT NULL
        OR mononym_latex IS NOT NULL`. To satisfy this, we use simplified values as
        fallbacks for latex when latex is empty. This ensures names parsed from CSV
        (which only populates simplified) will satisfy the constraint.
    """
    # Use simplified as fallback for latex when latex is empty
    family_latex = author.family_name.latex or author.family_name.simplified
    given_latex = author.given_name.latex or author.given_name.simplified
    mononym_latex = author.mononym.latex or author.mononym.simplified

    return ApiAuthor(
        author_key=author_key,
        family_name_latex=family_latex,
        family_name_unicode=author.family_name.unicode,
        family_name_simplified=author.family_name.simplified,
        given_name_latex=given_latex,
        given_name_unicode=author.given_name.unicode,
        given_name_simplified=author.given_name.simplified,
        mononym_latex=mononym_latex,
        mononym_unicode=author.mononym.unicode,
        mononym_simplified=author.mononym.simplified,
    )


def journal_to_api(journal: Journal, journal_key: str) -> ApiJournal:
    """Convert a bib-sdk Journal to API format.

    Args:
        journal: The Journal object from bib-sdk
        journal_key: The explicit key for this journal (from ODS column)

    Returns:
        ApiJournal object ready for API creation
    """
    return ApiJournal(
        journal_key=journal_key,
        name_latex=journal.name.latex,
        name_unicode=journal.name.unicode,
        name_simplified=journal.name.simplified,
        issn_print=journal.issn_print,
        issn_electronic=journal.issn_electronic,
    )


def publisher_to_api(publisher: BibStringAttr, publisher_key: str, address: str = "") -> ApiPublisher:
    """Convert a publisher BibStringAttr to API format.

    Args:
        publisher: The publisher BibStringAttr from bib-sdk
        publisher_key: The explicit key for this publisher (from ODS column)
        address: Optional default address for the publisher

    Returns:
        ApiPublisher object ready for API creation
    """
    return ApiPublisher(
        publisher_key=publisher_key,
        name_latex=publisher.latex,
        name_unicode=publisher.unicode,
        name_simplified=publisher.simplified,
        default_address=address,
    )


def institution_to_api(institution: BibStringAttr, institution_key: str) -> ApiInstitution:
    """Convert an institution BibStringAttr to API format."""
    return ApiInstitution(
        institution_key=institution_key,
        name_latex=institution.latex,
        name_unicode=institution.unicode,
        name_simplified=institution.simplified,
    )


def school_to_api(school: BibStringAttr, school_key: str) -> ApiSchool:
    """Convert a school BibStringAttr to API format."""
    return ApiSchool(
        school_key=school_key,
        name_latex=school.latex,
        name_unicode=school.unicode,
        name_simplified=school.simplified,
    )


def series_to_api(series_name: BibStringAttr, series_key: str) -> ApiSeries:
    """Convert a series BibStringAttr to API format."""
    return ApiSeries(
        series_key=series_key,
        name_latex=series_name.latex,
        name_unicode=series_name.unicode,
        name_simplified=series_name.simplified,
    )


def format_pages_for_api(pages: Tuple[PageAttr, ...]) -> str:
    """Format pages tuple to a string for API.

    Args:
        pages: Tuple of PageAttr from BibItem

    Returns:
        Formatted pages string (e.g., "1-10" or "1-10, 15-20")
    """
    return format_pages(pages)


def _extract_date_fields(
    date: BibItemDateAttr | Literal["no date"],
) -> tuple[int | None, int | None, int | None, int | None, int | None, bool]:
    """Extract date fields for API format.

    Returns:
        Tuple of (year, year_2_hyphen, year_2_slash, month, day, is_no_date)
    """
    if date == "no date":
        return (None, None, None, None, None, True)

    return (
        date.year if date.year != 0 else None,
        date.year_part_2_hyphen,
        date.year_part_2_slash,
        date.month,
        date.day,
        False,
    )


def bibitem_to_api(
    bibitem: BibItem,
    journal_key: str = "",
    publisher_key: str = "",
    institution_key: str = "",
    school_key: str = "",
    series_key: str = "",
    person_key: str = "",
) -> ApiBibItem:
    """Convert a bib-sdk BibItem to API format.

    Args:
        bibitem: The BibItem object from bib-sdk
        journal_key: The explicit journal key (from ODS column)
        publisher_key: The explicit publisher key (from ODS column)
        institution_key: The explicit institution key (from ODS column)
        school_key: The explicit school key (from ODS column)
        series_key: The explicit series key (from ODS column)
        person_key: The explicit person key (from ODS column)

    Returns:
        ApiBibItem object ready for API creation
    """
    # Extract bibkey string
    bibkey_str = format_bibkey(bibitem.bibkey) if bibitem.bibkey else ""

    # Extract title fields
    title_latex = ""
    title_unicode = ""
    title_simplified = ""
    if isinstance(bibitem.title, BibStringAttr):
        title_latex = bibitem.title.latex
        title_unicode = bibitem.title.unicode
        title_simplified = bibitem.title.simplified

    # Extract booktitle fields
    booktitle_latex = ""
    booktitle_unicode = ""
    booktitle_simplified = ""
    if isinstance(bibitem.booktitle, BibStringAttr):
        booktitle_latex = bibitem.booktitle.latex
        booktitle_unicode = bibitem.booktitle.unicode
        booktitle_simplified = bibitem.booktitle.simplified

    # Extract date fields
    year, year_2_hyphen, year_2_slash, month, day, is_no_date = _extract_date_fields(bibitem.date)

    # Extract issuetitle fields
    issuetitle_latex = ""
    issuetitle_unicode = ""
    if isinstance(bibitem.issuetitle, BibStringAttr):
        issuetitle_latex = bibitem.issuetitle.latex
        issuetitle_unicode = bibitem.issuetitle.unicode

    # Extract note fields
    note_latex = ""
    note_unicode = ""
    if isinstance(bibitem.note, BibStringAttr):
        note_latex = bibitem.note.latex
        note_unicode = bibitem.note.unicode

    # Extract extra_note fields
    extra_note_latex = ""
    extra_note_unicode = ""
    if isinstance(bibitem._extra_note, BibStringAttr):
        extra_note_latex = bibitem._extra_note.latex
        extra_note_unicode = bibitem._extra_note.unicode

    # Extract address
    address = ""
    if isinstance(bibitem.address, BibStringAttr):
        address = bibitem.address.unicode or bibitem.address.latex or bibitem.address.simplified

    # Extract type field
    type_field = ""
    if isinstance(bibitem.type, BibStringAttr):
        type_field = bibitem.type.unicode or bibitem.type.latex or bibitem.type.simplified

    # Extract crossref bibkey
    crossref_bibkey = ""
    if bibitem.crossref:
        crossref_bibkey = format_bibkey(bibitem.crossref.bibkey) if bibitem.crossref.bibkey else ""

    # Format options as comma-separated string
    options = ",".join(bibitem.options) if bibitem.options else ""

    return ApiBibItem(
        bibkey=bibkey_str,
        entry_type=bibitem.entry_type if bibitem.entry_type != "UNKNOWN" else "",
        pubstate=bibitem.pubstate,
        title_latex=title_latex,
        title_unicode=title_unicode,
        title_simplified=title_simplified,
        booktitle_latex=booktitle_latex,
        booktitle_unicode=booktitle_unicode,
        booktitle_simplified=booktitle_simplified,
        date_year=year,
        date_year_2_hyphen=year_2_hyphen,
        date_year_2_slash=year_2_slash,
        date_month=month,
        date_day=day,
        date_is_no_date=is_no_date,
        journal_key=journal_key,
        publisher_key=publisher_key,
        institution_key=institution_key,
        school_key=school_key,
        series_key=series_key,
        person_key=person_key,
        volume=bibitem.volume,
        number=bibitem.number,
        pages=format_pages_for_api(bibitem.pages),
        eid=bibitem.eid,
        edition=str(bibitem.edition) if bibitem.edition else "",
        address=address,
        type_field=type_field,
        doi=bibitem.doi,
        url=bibitem.url,
        urn=bibitem.urn,
        eprint=bibitem.eprint,
        crossref_bibkey=crossref_bibkey,
        issuetitle_latex=issuetitle_latex,
        issuetitle_unicode=issuetitle_unicode,
        note_latex=note_latex,
        note_unicode=note_unicode,
        extra_note_latex=extra_note_latex,
        extra_note_unicode=extra_note_unicode,
        langid=bibitem._langid,
        epoch=bibitem._epoch,
        options=options,
    )


def extract_keywords(bibitem: BibItem) -> ApiBibItemKeyword | None:
    """Extract keywords from a BibItem.

    Args:
        bibitem: The BibItem object

    Returns:
        ApiBibItemKeyword or None if no keywords
    """
    if not isinstance(bibitem._kws, KeywordsAttr):
        return None

    bibkey_str = format_bibkey(bibitem.bibkey) if bibitem.bibkey else ""

    return ApiBibItemKeyword(
        bibkey=bibkey_str,
        keyword_level_1=bibitem._kws.level_1.name if bibitem._kws.level_1.name else "",
        keyword_level_2=bibitem._kws.level_2.name if bibitem._kws.level_2.name else "",
        keyword_level_3=bibitem._kws.level_3.name if bibitem._kws.level_3.name else "",
    )
