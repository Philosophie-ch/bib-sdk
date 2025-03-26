from __future__ import annotations
from typing import Tuple
import attrs

from philoch_bib_sdk.logic.literals import TBibTeXEntryType, TEpoch, TLanguageID, TPubState


############
# Base Renderables
############


@attrs.define(frozen=True, slots=True)
class BaseRenderable:
    """
    Base class for renderable objects, that contain LaTeX code, and possibly a unicode representation of it.

    Args:
        text: str = ""
        text_latex: str = ""
        id: int = -1
    """

    text: str = ""
    text_latex: str = ""
    id: int = -1


@attrs.define(frozen=True, slots=True)
class BaseNamedRenderable:
    """
    Base class for renderable, named, objects, that contain LaTeX code, and possibly a unicode representation of it.

    Args:
        name: str
        name_latex: str | None = None
        id: int | None = None
    """

    name: str = ""
    name_latex: str = ""
    id: int = -1


############
# Author
############


@attrs.define(frozen=True, slots=True)
class Author:
    """
    An author of a publication.

    Args:
        given_name: str = ""
        family_name: str = ""
        given_name_latex: str  = ""
        family_name_latex: str = ""
        publications: List[BibItem] = []
        id: int = -1
    """

    given_name: str = ""
    family_name: str = ""
    given_name_latex: str = ""
    family_name_latex: str = ""
    famous_name: str = ""
    publications: Tuple[BibItem, ...] = ()
    id: int = -1


############
# Journal
############


@attrs.define(frozen=True, slots=True)
class Journal:
    """
    A journal that publishes publications.

    Args:
        name: str = ""
        name_latex: str = ""
        issn_print: str = ""
        issn_electronic: str = ""
        id: int = -1
    """

    name: str = ""
    name_latex: str = ""
    issn_print: str = ""
    issn_electronic: str = ""
    id: int = -1


############
# BibItem
############


@attrs.define(frozen=True, slots=True)
class BibKey:
    """
    A unique identifier for a publication.

    Args:
        first_author: str = ""
        year: int | None = None
        pub_status: TPubState = "published"
        other_authors: str = ""
        et_al: bool = False
        year_suffix
    """

    first_author: str
    other_authors: str = ""
    year: int | None = None
    pub_status: TPubState = ""
    year_suffix: str = ""


@attrs.define(frozen=True, slots=True)
class BibItemDate:
    """
    Year of a publication.

    Example:
        BibItemDate(year=2021, year_revised=2022) represents `2021/2022`.
        BibItemDate(year=2021, month=1, day=1) represents `2021-01-01`.
        BibItemDate(forthcoming=True) represents `forthcoming`.

    Args:
        year: int | None = None
        year_revised: int | None = None
        month: int | None = None
        day: int | None = None
        forthcoming: bool | None = None
    """

    year: int | None = None
    year_revised: int | None = None
    month: int | None = None
    day: int | None = None
    forthcoming: bool = False


@attrs.define(frozen=True, slots=True)
class Keyword:
    """
    Keyword of a publication.

    Args:
        name: str = ""
        id: int = -1
    """

    name: str = ""
    id: int = -1


@attrs.define(frozen=True, slots=True)
class Keywords:
    level1: Keyword = Keyword()
    level2: Keyword = Keyword()
    level3: Keyword = Keyword()


@attrs.define(frozen=True, slots=True)
class PagePair:
    """
    Page numbers of a publication. Can be a range, roman numerals, or a single page.

    Args:
        start: str
        end: str | None = None
    """

    start: str
    end: str = ""


@attrs.define(frozen=True, slots=True)
class BibItem:
    """
    Bibliographic item type. All attributes are optional.

    Args:

    """

    _to_do: str = ""
    _change_request: str = ""
    entry_type: TBibTeXEntryType = ""
    bibkey: BibKey | None = None
    author: Tuple[Author, ...] = ()
    editor: Tuple[Author, ...] = ()
    options: Tuple[str, ...] = ()
    shorthand: str = ""
    date: BibItemDate | None = None
    pubstate: TPubState | None = None
    title: str = ""
    _title_unicode: str = ""
    booktitle: str = ""
    crossref: str = ""
    journal: Journal | None = None
    volume: str = ""
    number: str = ""
    pages: Tuple[PagePair, ...] = ()
    eid: str = ""
    series: BaseNamedRenderable | None = None
    address: str = ""
    institution: str = ""
    school: str = ""
    publisher: BaseNamedRenderable | None = None
    type: BaseNamedRenderable | None = None
    edition: str = ""
    note: BaseRenderable | None = None
    issuetitle: BaseRenderable | None = None
    guesteditor: Tuple[Author, ...] = ()
    further_note: BaseRenderable | None = None
    urn: str = ""
    eprint: str = ""
    doi: str = ""
    url: str = ""
    _kws: Keywords = Keywords()
    _epoch: TEpoch = ""
    _person: Author | None = None
    _comm_for_profile_bib: str = ""
    langid: TLanguageID = ""
    _lang_det: str = ""
    _further_refs: Tuple[BibKey, ...] = ()
    _depends_on: Tuple[BibKey, ...] = ()
    dltc_num: int | None = None
    _spec_interest: str = ""
    _note_perso: BaseRenderable | None = None
    _note_stock: BaseRenderable | None = None
    _note_status: BaseRenderable | None = None
    _num_in_work: str = ""
    _num_in_work_coll: int | None = None
    _num_coll: int | None = None
    _dltc_copyediting_note: str = ""
    _note_missing: str = ""
    _num_sort: int = 0
    _bib_info_source: str = ""
