from __future__ import annotations
from typing import Literal, Tuple
import attrs

from philoch_bib_sdk.logic.literals import TBasicPubState, TBibTeXEntryType, TEpoch, TLanguageID, TPubState


@attrs.define(frozen=True, slots=True)
class BibStringAttr:
    """
    A representation of the different forms of a string we may need for different purposes.

    Args:
        latex: formatted string for LaTeX, can be used in bib files
        unicode: formatted string for Unicode, can be used in text. Produced from the LaTeX string
        simplified: simplified string, can be used to match strings. Produced from the Unicode string
    """

    latex: str = ""
    unicode: str = ""
    simplified: str = ""


type TBibString = Literal[
    "latex",
    "unicode",
    "simplified",
]


############
# Base Renderables
############


@attrs.define(frozen=True, slots=True)
class BaseRenderable:
    """
    Base class for renderable objects that contain a single 'text' attribute.

    Args:
        text: BibString
        id: int | None = None
    """

    text: BibStringAttr
    id: int | None = None


@attrs.define(frozen=True, slots=True)
class BaseNamedRenderable:
    """
    Base class for renderable objects that contain a single 'name' attribute.

    Args:
        name: BibString
        id: int | None = None
    """

    name: BibStringAttr
    id: int | None = None


############
# Author
############


@attrs.define(frozen=True, slots=True)
class Author:
    """
    An author of a publication.

    Args:
        given_name: BibStringAttr
        family_name: BibStringAttr
        given_name_latex: BibStringAttr
        family_name_latex: BibStringAttr
        publications: Tuple[BibItem] = []
        id: int | None = None
    """

    given_name: BibStringAttr
    family_name: BibStringAttr
    mononym: BibStringAttr
    shorthand: BibStringAttr
    famous_name: BibStringAttr
    publications: Tuple[BibItem, ...]
    id: int | None = None


############
# Journal
############


@attrs.define(frozen=True, slots=True)
class Journal:
    """
    A journal that publishes publications.

    Args:
        name: BibStringAttr
        name_latex: str
        issn_print: str
        issn_electronic: str
        id: int | None = None
    """

    name: BibStringAttr
    issn_print: str
    issn_electronic: str
    id: int | None = None


############
# Keyword
############


@attrs.define(frozen=True, slots=True)
class Keyword:
    """
    Keyword of a publication.

    Args:
        name: str
        id: int | None = None
    """

    name: str
    id: int | None = None


############
# BibItem
############


class BibKeyValidationError(Exception):
    pass


@attrs.define(frozen=True, slots=True)
class BibKeyAttr:
    """
    A unique identifier for a publication.

    Args:
        first_author: str
        other_authors: str
        date: int | TBasicPubStatus
        date_suffix: str
    """

    first_author: str
    other_authors: str
    date: int | TBasicPubState
    date_suffix: str

    def __attrs_post_init__(self) -> None:
        if not self.first_author or not self.date:
            raise BibKeyValidationError("Both 'first_author' and 'date' must not be empty.")


class BibItemDateValidationError(Exception):
    pass


@attrs.define(frozen=True, slots=True)
class BibItemDateAttr:
    """
    Year of a publication.

    Example:
        BibItemDate(year=2021, year_revised=2022) represents `2021/2022`.
        BibItemDate(year=2021, month=1, day=1) represents `2021-01-01`.
        BibItemDate(forthcoming=True) represents `forthcoming`.

    Args:
        year: int
        year_part_2_hyphens: int | Literal[""] = ""
        year_part_2_slash: int | Literal[""] = ""
        month: int | Literal[""] = ""
        day: int | Literal[""] = ""
    """

    year: int
    year_part_2_hyphens: int | Literal[""] = ""
    year_part_2_slash: int | Literal[""] = ""
    month: int | Literal[""] = ""
    day: int | Literal[""] = ""

    def __attrs_post_init__(self) -> None:
        if any([self.year_part_2_hyphens, self.year_part_2_slash]) and not self.year:
            raise BibItemDateValidationError(
                "If 'year_part_2_hyphens' or 'year_part_2_slash' is set, 'year' must not be empty."
            )

        if self.day and not self.month:
            raise BibItemDateValidationError("If 'day' is set, 'month' must not be empty.")

        if self.month and not self.year:
            raise BibItemDateValidationError("If 'month' is set, 'year' must not be empty.")


@attrs.define(frozen=True, slots=True)
class KeywordsAttr:
    """
    Keywords of a publication.

    Args:
        level_1: Keyword
        level_2: Keyword
        level_3: Keyword
    """

    level_1: Keyword
    level_2: Keyword
    level_3: Keyword


class PageValidationError(Exception):
    pass


@attrs.define(frozen=True, slots=True)
class PageAttr:
    """
    Page numbers of a publication. Can be a range, roman numerals, or a single page.

    Args:
        start: str
        end: str
    """

    start: str
    end: str

    def __attrs_post_init__(self) -> None:
        if self.end and not self.start:
            raise PageValidationError("If 'end' is set, 'start' must not be empty.")


class BibItemValidationError(Exception):
    pass


@attrs.define(frozen=True, slots=True)
class BibItem:
    """
    Bibliographic item type. All attributes are optional.

    Args:

    """

    # Normal string fields
    _to_do: str
    _change_request: str

    # Official fields, may be stored in different formats
    entry_type: TBibTeXEntryType
    bibkey: BibKeyAttr | Literal[""]
    author: Tuple[Author, ...]
    editor: Tuple[Author, ...]
    options: Tuple[str, ...]
    # shorthand: BibStringAttr  # Mononym of the author
    date: BibItemDateAttr | Literal["no date"]
    pubstate: TPubState
    title: BibStringAttr
    booktitle: BibStringAttr
    crossref: CrossrefBibItemAttr | Literal[""]
    journal: Journal | Literal[""]
    volume: str
    number: str
    pages: Tuple[PageAttr, ...]
    eid: str
    series: BaseNamedRenderable
    address: BibStringAttr
    institution: BibStringAttr
    school: BibStringAttr
    publisher: BibStringAttr
    type: BibStringAttr
    edition: int | Literal[""]
    note: BibStringAttr
    issuetitle: BibStringAttr
    guesteditor: Tuple[Author, ...]  # Custom field
    further_note: BibStringAttr  # Custom field
    urn: str
    eprint: str
    doi: str
    url: str

    # String fields
    _kws: KeywordsAttr
    _epoch: TEpoch
    _person: Author
    _comm_for_profile_bib: str
    langid: TLanguageID
    _lang_det: str
    _further_refs: Tuple[BibKeyAttr, ...]
    _depends_on: Tuple[BibKeyAttr, ...]
    dltc_num: int
    _spec_interest: str
    _note_perso: str
    _note_stock: str
    _note_status: str
    _num_in_work: str
    _num_in_work_coll: int | Literal[""]
    _num_coll: int | Literal[""]
    _dltc_copyediting_note: str
    _note_missing: str
    _num_sort: int | Literal[""]

    # Additional fields
    id: int | None = None
    _bib_info_source: str = ""

    def __attrs_post_init__(self) -> None:

        if self.crossref and self.bibkey == self.crossref.bibkey:
            raise BibItemValidationError("Crossref bibkey must be different from the main bibkey.")


@attrs.define(frozen=True, slots=True)
class CrossrefBibItemAttr(BibItem):
    """
    A cross-reference to another bibliographic item.

    Args:
        bibkey: str
    """

    def __attrs_post_init__(self) -> None:
        if self.entry_type != "book":
            raise ValueError("Crossref must have a 'type' of 'book'.")

        if not self.booktitle:
            raise ValueError("Crossref must have a 'booktitle'.")

        if not self.bibkey:
            raise ValueError("Crossref must have a 'bibkey'.")

        if self.crossref and self.bibkey == self.crossref.bibkey:
            raise BibItemValidationError("Crossref bibkey must be different from the main bibkey.")
