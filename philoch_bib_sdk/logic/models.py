from __future__ import annotations
from typing import Literal, Tuple, get_args
import attrs

from philoch_bib_sdk.logic.literals import TBasicPubState, TBibTeXEntryType, TEpoch, TLanguageID, TPubState


type Maybe[T] = T | None
type MaybeStr[T] = T | Literal[""]


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


BibStringLiteral = Literal["latex", "unicode", "simplified"]

type TBibString = BibStringLiteral
BIB_STRING_VALUES: Tuple[str, ...] = get_args(BibStringLiteral)


############
# Base Renderables
############


@attrs.define(frozen=True, slots=True)
class BaseRenderable:
    """
    Base class for renderable objects that contain a single 'text' attribute.

    Args:
        text: BibString
        id: Maybe[int] = None
    """

    text: BibStringAttr
    id: Maybe[int] = None


@attrs.define(frozen=True, slots=True)
class BaseNamedRenderable:
    """
    Base class for renderable objects that contain a single 'name' attribute.

    Args:
        name: BibString
        id: Maybe[int] = None
    """

    name: BibStringAttr
    id: Maybe[int] = None


RenderablesLiteral = Literal["text", "name"]

type TRenderable = RenderablesLiteral
RENDERABLES_VALUES: Tuple[str, ...] = get_args(RenderablesLiteral)


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
        id: Maybe[int] = None
    """

    given_name: BibStringAttr
    family_name: BibStringAttr
    mononym: BibStringAttr
    shorthand: BibStringAttr
    famous_name: BibStringAttr
    publications: Tuple[BibItem, ...]
    id: Maybe[int] = None


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
        id: Maybe[int] = None
    """

    name: BibStringAttr
    issn_print: str
    issn_electronic: str
    id: Maybe[int] = None


############
# Keyword
############


@attrs.define(frozen=True, slots=True)
class Keyword:
    """
    Keyword of a publication.

    Args:
        name: str
        id: Maybe[int] = None
    """

    name: str
    id: Maybe[int] = None


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

    Args:
        year: int
        year_part_2_hyphen: Maybe[int] = None
        year_part_2_slash: Maybe[int] = None
        month: Maybe[int] = None
        day: Maybe[int] = None
    """

    year: int
    year_part_2_hyphen: Maybe[int] = None
    year_part_2_slash: Maybe[int] = None
    month: Maybe[int] = None
    day: Maybe[int] = None

    def __attrs_post_init__(self) -> None:
        if any([self.year_part_2_hyphen, self.year_part_2_slash]) and not self.year:
            raise BibItemDateValidationError(
                "If 'year_part_2_hyphens' or 'year_part_2_slash' is set, 'year' must not be empty."
            )

        if not ((self.month and self.day) or (not self.month and not self.day)):
            raise BibItemDateValidationError("If 'day' is set, 'month' must be set too, and vice versa.")

        if self.month and not self.year:
            raise BibItemDateValidationError("If 'month' is set, 'year' must not be empty.")

        if self.year_part_2_hyphen and self.year_part_2_slash:
            raise BibItemDateValidationError("If 'year_part_2_hyphen' is set, 'year_part_2_slash' must not be set.")


VALID_DATE_FORMATS = [
    "{year}",
    "{year_1}-{year_2}",
    "{year}/{year_2}",
    "{year}-{month}-{day}",
    "{year}-{month}",
]


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
    _to_do_general: str
    _change_request: str

    # Official fields, may be stored in different formats
    entry_type: TBibTeXEntryType
    bibkey: MaybeStr[BibKeyAttr]
    author: Tuple[Author, ...]
    editor: Tuple[Author, ...]
    options: Tuple[str, ...]
    # shorthand: BibStringAttr  # Mononym of the author
    date: BibItemDateAttr | Literal["no date"]
    pubstate: TPubState
    title: MaybeStr[BibStringAttr]
    booktitle: MaybeStr[BibStringAttr]
    crossref: MaybeStr[CrossrefBibItemAttr]
    journal: Maybe[Journal]
    volume: str
    number: str
    pages: Tuple[PageAttr, ...]
    eid: str
    series: MaybeStr[BaseNamedRenderable]
    address: MaybeStr[BibStringAttr]
    institution: MaybeStr[BibStringAttr]
    school: MaybeStr[BibStringAttr]
    publisher: MaybeStr[BibStringAttr]
    type: MaybeStr[BibStringAttr]
    edition: Maybe[int]
    note: MaybeStr[BibStringAttr]
    issuetitle: MaybeStr[BibStringAttr]
    _guesteditor: Tuple[Author, ...]  # Custom field
    _extra_note: MaybeStr[BibStringAttr]  # Custom field
    urn: str
    eprint: str
    doi: str
    url: str

    # String fields
    _kws: MaybeStr[KeywordsAttr]
    _epoch: TEpoch
    _person: MaybeStr[Author]
    _comm_for_profile_bib: str
    _langid: TLanguageID
    _lang_der: str
    _further_refs: Tuple[BibKeyAttr, ...]
    _depends_on: Tuple[BibKeyAttr, ...]
    _dltc_num: Maybe[int]
    _spec_interest: str
    _note_perso: str
    _note_stock: str
    _note_status: str
    _num_inwork_coll: Maybe[int]
    _num_inwork: str
    _num_coll: Maybe[int]
    _dltc_copyediting_note: str
    _note_missing: str
    _num_sort: Maybe[int]

    # Additional fields
    id: Maybe[int] = None
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
