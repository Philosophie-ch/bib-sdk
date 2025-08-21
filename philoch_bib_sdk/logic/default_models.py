from typing import Tuple, TypedDict, Unpack, Literal
from philoch_bib_sdk.logic.models import BibItem, PageAttr, KeywordsAttr, BibItemDateAttr, BibKeyAttr, Keyword

from philoch_bib_sdk.logic.literals import TBasicPubState, TBibTeXEntryType, TEpoch, TLanguageID, TPubState
from philoch_bib_sdk.logic.models import (
    Author,
    BaseNamedRenderable,
    BaseRenderable,
    BibItem,
    BibStringAttr,
    Journal,
    Keyword,
)


class BibStringArgs(TypedDict, total=False):
    latex: str
    unicode: str
    simplified: str


def default_bib_string(**kwargs: Unpack[BibStringArgs]) -> BibStringAttr:
    """
    Create a default BibString object, given a dictionary with any (or None) of its attributes. Defaults to empty strings if not provided.
    """
    return BibStringAttr(
        latex=kwargs.get("latex", ""),
        unicode=kwargs.get("unicode", ""),
        simplified=kwargs.get("simplified", ""),
    )


############
# Base Renderables
############


class BaseRenderableArgs(TypedDict, total=False):
    text: BibStringArgs
    id: int | None


def default_base_renderable(**kwargs: Unpack[BaseRenderableArgs]) -> BaseRenderable:
    """
    Create a default BaseRenderable object, given a dictionary with any (or None) of its attributes. Defaults to empty strings if not provided.
    """
    return BaseRenderable(
        text=default_bib_string(**kwargs.get("text", {})),
        id=kwargs.get("id", None),
    )


class BaseNamedRenderableArgs(TypedDict, total=False):
    name: BibStringArgs
    id: int | None


def default_base_named_renderable(**kwargs: Unpack[BaseNamedRenderableArgs]) -> BaseNamedRenderable:
    """
    Create a default BaseNamedRenderable object, given a dictionary with any (or None) of its attributes. Defaults to empty strings if not provided.
    """
    return BaseNamedRenderable(
        name=default_bib_string(**kwargs.get("name", {})),
        id=kwargs.get("id", None),
    )


############
# Author
############


class AuthorArgs(TypedDict, total=False):
    given_name: BibStringArgs
    family_name: BibStringArgs
    mononym: BibStringArgs
    shorthand: BibStringArgs
    famous_name: BibStringArgs
    publications: Tuple[BibItem, ...]
    id: int | None


def default_author(**kwargs: Unpack[AuthorArgs]) -> Author:
    """
    Create a default Author object, given a dictionary with any (or None) of its attributes. Defaults to empty strings and an empty tuple for publications if not provided.
    """

    return Author(
        given_name=default_bib_string(**kwargs.get("given_name", {})),
        family_name=default_bib_string(**kwargs.get("family_name", {})),
        mononym=default_bib_string(**kwargs.get("mononym", {})),
        shorthand=default_bib_string(**kwargs.get("shorthand", {})),
        famous_name=default_bib_string(**kwargs.get("famous_name", {})),
        publications=kwargs.get("publications", ()),
        id=kwargs.get("id", None),
    )


############
# Journal
############


class JournalArgs(TypedDict, total=False):
    name: BibStringArgs
    issn_print: str
    issn_electronic: str
    id: int | None


def default_journal(**kwargs: Unpack[JournalArgs]) -> Journal | None:
    """
    Create a default Journal object, given a dictionary with any (or None) of its attributes. Defaults to empty strings if not provided.
    """
    if kwargs == {}:
        return None

    return Journal(
        name=default_bib_string(**kwargs.get("name", {})),
        issn_print=kwargs.get("issn_print", ""),
        issn_electronic=kwargs.get("issn_electronic", ""),
        id=kwargs.get("id", None),
    )


############
# Support Args
############


class PageArgs(TypedDict, total=False):
    start: str
    end: str


def default_page(**kwargs: Unpack[PageArgs]) -> PageAttr:
    return PageAttr(
        start=kwargs.get("start", ""),
        end=kwargs.get("end", ""),
    )


class KeywordsArgs(TypedDict, total=False):
    level_1: str
    level_2: str
    level_3: str


def default_keywords(**kwargs: Unpack[KeywordsArgs]) -> KeywordsAttr:
    return KeywordsAttr(
        level_1=Keyword(name=kwargs.get("level_1", "")),
        level_2=Keyword(name=kwargs.get("level_2", "")),
        level_3=Keyword(name=kwargs.get("level_3", "")),
    )


class BibItemDateArgs(TypedDict, total=False):
    year: int
    year_part_2_hyphen: int | None
    year_part_2_slash: int | None
    month: int | None
    day: int | None


def default_bib_item_date(**kwargs: Unpack[BibItemDateArgs]) -> BibItemDateAttr:
    return BibItemDateAttr(
        year=kwargs.get("year", 0),
        year_part_2_hyphen=kwargs.get("year_part_2_hyphen"),
        year_part_2_slash=kwargs.get("year_part_2_slash"),
        month=kwargs.get("month"),
        day=kwargs.get("day"),
    )


def parse_date(date: BibItemDateArgs | Literal["no date"]) -> BibItemDateAttr | Literal["no date"]:
    if isinstance(date, dict):
        return default_bib_item_date(**date)
    else:
        return "no date"


class BibKeyArgs(TypedDict, total=False):
    first_author: str
    other_authors: str
    date: int | TBasicPubState
    date_suffix: str


def default_bib_key(**kwargs: Unpack[BibKeyArgs]) -> BibKeyAttr:
    # Then pass to BibKeyAttr
    return BibKeyAttr(
        first_author=kwargs.get("first_author", ""),
        other_authors=kwargs.get("other_authors", ""),
        date=kwargs.get("date", ""),
        date_suffix=kwargs.get("date_suffix", ""),
    )


############
# BibItem Args
############


class BibItemArgs(TypedDict, total=False):
    _to_do_general: str
    _change_request: str
    entry_type: TBibTeXEntryType
    bibkey: BibKeyArgs
    author: Tuple[AuthorArgs, ...]
    editor: Tuple[AuthorArgs, ...]
    options: Tuple[str, ...]
    date: BibItemDateArgs | Literal["no date"]
    pubstate: TPubState
    title: BibStringArgs
    booktitle: BibStringArgs
    #    crossref: dict
    journal: JournalArgs
    volume: str
    number: str
    pages: Tuple[PageArgs, ...]
    eid: str
    series: BaseNamedRenderableArgs
    address: BibStringArgs
    institution: BibStringArgs
    school: BibStringArgs
    publisher: BibStringArgs
    type: BibStringArgs
    edition: int
    note: BibStringArgs
    issuetitle: BibStringArgs
    _guesteditor: Tuple[AuthorArgs, ...]
    _extra_note: BibStringArgs
    urn: str
    eprint: str
    doi: str
    url: str
    _kws: KeywordsArgs
    _epoch: TEpoch
    _person: AuthorArgs
    _comm_for_profile_bib: str
    _langid: TLanguageID
    _lang_der: str
    _further_refs: Tuple[BibKeyArgs, ...]
    _depends_on: Tuple[BibKeyArgs, ...]
    _dltc_num: int
    _spec_interest: str
    _note_perso: str
    _note_stock: str
    _note_status: str
    _num_inwork_coll: int
    _num_inwork: str
    _num_coll: int
    _dltc_copyediting_note: str
    _note_missing: str
    _num_sort: int
    id: int
    _bib_info_source: str


def default_bib_item(**kwargs: Unpack[BibItemArgs]) -> BibItem:
    return BibItem(
        to_do_general=kwargs.get("_to_do_general", ""),
        change_request=kwargs.get("_change_request", ""),
        entry_type=kwargs.get("entry_type", "UNKNOWN"),
        bibkey=default_bib_key(**kwargs.get("bibkey", {})) if "bibkey" in kwargs else "",
        author=tuple(default_author(**a) for a in kwargs.get("author", ())),
        editor=tuple(default_author(**e) for e in kwargs.get("editor", ())),
        options=kwargs.get("options", ()),
        date=parse_date(kwargs.get("date", "no date")),
        pubstate=kwargs.get("pubstate", ""),
        title=default_bib_string(**kwargs.get("title", {})) if "title" in kwargs else "",
        booktitle=default_bib_string(**kwargs.get("booktitle", {})) if "booktitle" in kwargs else "",
        crossref="",  # Crossref is not defined in the provided context, so we leave it as an empty string
        journal=default_journal(**kwargs.get("journal", {})) if "journal" in kwargs else None,
        volume=kwargs.get("volume", ""),
        number=kwargs.get("number", ""),
        pages=tuple(default_page(**p) for p in kwargs.get("pages", ())),
        eid=kwargs.get("eid", ""),
        series=default_base_named_renderable(**kwargs.get("series", {})) if "series" in kwargs else "",
        address=default_bib_string(**kwargs.get("address", {})) if "address" in kwargs else "",
        institution=default_bib_string(**kwargs.get("institution", {})) if "institution" in kwargs else "",
        school=default_bib_string(**kwargs.get("school", {})) if "school" in kwargs else "",
        publisher=default_bib_string(**kwargs.get("publisher", {})) if "publisher" in kwargs else "",
        type=default_bib_string(**kwargs.get("type", {})) if "type" in kwargs else "",
        edition=kwargs.get("edition"),
        note=default_bib_string(**kwargs.get("note", {})) if "note" in kwargs else "",
        issuetitle=default_bib_string(**kwargs.get("issuetitle", {})) if "issuetitle" in kwargs else "",
        guesteditor=tuple(default_author(**a) for a in kwargs.get("_guesteditor", ())),
        extra_note=default_bib_string(**kwargs.get("_extra_note", {})) if "_extra_note" in kwargs else "",
        urn=kwargs.get("urn", ""),
        eprint=kwargs.get("eprint", ""),
        doi=kwargs.get("doi", ""),
        url=kwargs.get("url", ""),
        kws=default_keywords(**kwargs.get("_kws", {})) if "_kws" in kwargs else "",
        epoch=kwargs.get("_epoch", ""),
        person=default_author(**kwargs.get("_person", {})) if "_person" in kwargs else "",
        comm_for_profile_bib=kwargs.get("_comm_for_profile_bib", ""),
        langid=kwargs.get("_langid", ""),
        lang_der=kwargs.get("_lang_der", ""),
        further_refs=tuple(default_bib_key(**b) for b in kwargs.get("_further_refs", ())),
        depends_on=tuple(default_bib_key(**b) for b in kwargs.get("_depends_on", ())),
        dltc_num=kwargs.get("_dltc_num"),
        spec_interest=kwargs.get("_spec_interest", ""),
        note_perso=kwargs.get("_note_perso", ""),
        note_stock=kwargs.get("_note_stock", ""),
        note_status=kwargs.get("_note_status", ""),
        num_inwork_coll=kwargs.get("_num_inwork_coll"),
        num_inwork=kwargs.get("_num_inwork", ""),
        num_coll=kwargs.get("_num_coll"),
        dltc_copyediting_note=kwargs.get("_dltc_copyediting_note", ""),
        note_missing=kwargs.get("_note_missing", ""),
        num_sort=kwargs.get("_num_sort"),
        id=kwargs.get("id"),
        bib_info_source=kwargs.get("_bib_info_source", ""),
    )
