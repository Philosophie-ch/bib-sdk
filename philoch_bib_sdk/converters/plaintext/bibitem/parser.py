import traceback
from typing import Tuple, Literal, TypedDict, TypeGuard, Any
from aletk.ResultMonad import Ok, Err
from aletk.utils import get_logger, remove_extra_whitespace
from philoch_bib_sdk.converters.plaintext.author.parser import parse_author
from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_parser import parse_bibkey
from philoch_bib_sdk.converters.plaintext.bibitem.date_parser import parse_date
from philoch_bib_sdk.converters.plaintext.bibitem.pages_parser import parse_pages
from philoch_bib_sdk.converters.plaintext.journal.parser import parse_journal
from philoch_bib_sdk.logic.literals import (
    TBibTeXEntryType,
    TPubState,
    TEpoch,
    TLanguageID,
    BIBTEX_ENTRY_TYPE_VALUES,
    PUB_STATE_VALUES,
    EPOCH_VALUES,
    LANGUAGE_ID_VALUES,
)
from philoch_bib_sdk.logic.models import (
    BibItem,
    BibStringAttr,
    BibKeyAttr,
    Author,
    PageAttr,
    BibItemDateAttr,
    BaseNamedRenderable,
    KeywordsAttr,
    Keyword,
    TBibString,
)

lgr = get_logger(__name__)


class ParsedBibItemData(TypedDict, total=False):
    _to_do_general: str
    _change_request: str
    entry_type: str
    bibkey: str
    author: str
    _author_ids: str
    editor: str
    _editor_ids: str
    author_ids: str
    options: str
    shorthand: str
    date: str
    pubstate: str
    title: str
    _title_unicode: str
    booktitle: str
    crossref: str
    journal: str
    journal_id: str
    volume: str
    number: str
    pages: str
    eid: str
    series: str
    address: str
    institution: str
    school: str
    publisher: str
    publisher_id: str
    type: str
    edition: str
    note: str
    _issuetitle: str
    _guesteditor: str
    _extra_note: str
    urn: str
    eprint: str
    doi: str
    url: str
    _kw_level1: str
    _kw_level2: str
    _kw_level3: str
    _epoch: str
    _person: str
    _comm_for_profile_bib: str
    _langid: str
    _lang_der: str
    _further_refs: str
    _depends_on: str
    _dltc_num: str
    _spec_interest: str
    _note_perso: str
    _note_stock: str
    _note_status: str
    _num_inwork_coll: str
    _num_inwork: str
    _num_coll: str
    _dltc_copyediting_note: str
    _note_missing: str
    _num_sort: str


def _is_valid_bibtex_entry_type(value: Any) -> TypeGuard[TBibTeXEntryType]:
    """
    TypeGuard function to validate if a value is a valid BibTeX entry type.
    """
    return isinstance(value, str) and value in BIBTEX_ENTRY_TYPE_VALUES


def parse_entry_type(text: str) -> TBibTeXEntryType:
    """
    Parse the entry type from a string.
    """
    if text == "" or text == "UNKNOWN":
        return "UNKNOWN"

    clean = text.strip().replace(" ", "").lower().replace("@", "").replace("{", "").replace("}", "")

    if _is_valid_bibtex_entry_type(clean):
        return clean
    else:
        return "UNKNOWN"


def parse_options(text: str) -> Tuple[str, ...]:
    """
    Parse a comma-separated list of options.
    """
    if not text:
        return ()
    return tuple(remove_extra_whitespace(opt) for opt in text.split(",") if opt.strip())


def parse_bibkey_list(text: str) -> Tuple[BibKeyAttr, ...]:
    """
    Parse a comma-separated list of bibkeys.
    """
    if not text:
        return ()

    bibkeys = []
    for bibkey_str in text.split(","):
        bibkey_str = remove_extra_whitespace(bibkey_str)
        if bibkey_str:
            result = parse_bibkey(bibkey_str)
            if isinstance(result, Ok):
                bibkeys.append(result.out)
            else:
                raise ValueError(f"Failed to parse bibkey '{bibkey_str}': {result.message}")

    return tuple(bibkeys)


def _clean_keyword(text: str) -> str:
    """
    Clean a keyword string by stripping whitespace and removing unwanted characters.
    """
    return remove_extra_whitespace(text).replace(",", "").replace(";", "")


def parse_keywords(level1: str, level2: str, level3: str) -> KeywordsAttr | None:
    """
    Parse keywords from three level strings.
    """
    if not any([level1, level2, level3]):
        return None

    return KeywordsAttr(
        level_1=Keyword(name=_clean_keyword(level1), id=None) if level1 else Keyword(name="", id=None),
        level_2=Keyword(name=_clean_keyword(level2), id=None) if level2 else Keyword(name="", id=None),
        level_3=Keyword(name=_clean_keyword(level3), id=None) if level3 else Keyword(name="", id=None),
    )


def _is_valid_pubstate(value: Any) -> TypeGuard[TPubState]:
    """
    TypeGuard function to validate if a value is a valid publication state.
    """
    return isinstance(value, str) and value in PUB_STATE_VALUES


def parse_pubstate(text: str) -> TPubState:
    """
    Parse publication state from a string.
    """
    if _is_valid_pubstate(text):
        return text
    else:
        return ""


def _is_valid_epoch(value: Any) -> TypeGuard[TEpoch]:
    """
    TypeGuard function to validate if a value is a valid epoch.
    """
    return isinstance(value, str) and value in EPOCH_VALUES


def parse_epoch(text: str) -> TEpoch:
    """
    Parse epoch from a string.
    """
    if _is_valid_epoch(text):
        return text
    else:
        return ""


def _is_valid_language_id(value: Any) -> TypeGuard[TLanguageID]:
    """
    TypeGuard function to validate if a value is a valid language ID.
    """
    return isinstance(value, str) and value in LANGUAGE_ID_VALUES


def parse_language_id(text: str) -> TLanguageID:
    """
    Parse language ID from a string.
    """
    if _is_valid_language_id(text):
        return text
    else:
        return ""


def _create_bibstring_attr(value: str, bibstring_type: TBibString) -> BibStringAttr:
    """
    Create a BibStringAttr with the correct field set based on bibstring_type.
    """
    if bibstring_type == "latex":
        return BibStringAttr(latex=value)
    elif bibstring_type == "unicode":
        return BibStringAttr(unicode=value)
    else:  # simplified
        return BibStringAttr(simplified=value)


def parse_bibitem(data: ParsedBibItemData, bibstring_type: TBibString = "latex") -> Ok[BibItem] | Err:
    """
    Parse a bibitem from a dictionary of string fields into a BibItem object.
    """
    try:
        # Parse bibkey
        bibkey = None
        if data.get("bibkey"):
            bibkey_result = parse_bibkey(data["bibkey"])
            if isinstance(bibkey_result, Err):
                return bibkey_result
            bibkey = bibkey_result.out

        # Parse authors
        authors: tuple[Author, ...] = ()
        if data.get("author"):
            author_result = parse_author(data["author"], bibstring_type)
            if isinstance(author_result, Err):
                return author_result
            authors = author_result.out

        # Parse editors
        editors: tuple[Author, ...] = ()
        if data.get("editor"):
            editor_result = parse_author(data["editor"], bibstring_type)
            if isinstance(editor_result, Err):
                return editor_result
            editors = editor_result.out

        # Parse guest editors
        guesteditors: tuple[Author, ...] = ()
        if data.get("_guesteditor"):
            guesteditor_result = parse_author(data["_guesteditor"], bibstring_type)
            if isinstance(guesteditor_result, Err):
                return guesteditor_result
            guesteditors = guesteditor_result.out

        # Parse person
        person = None
        if data.get("_person"):
            person_result = parse_author(data["_person"], bibstring_type)
            if isinstance(person_result, Err):
                return person_result
            if person_result.out:
                person = person_result.out[0]

        # Parse date
        date: BibItemDateAttr | Literal["no date"] = BibItemDateAttr(year=0)
        if data.get("date"):
            date_result = parse_date(data["date"])
            if isinstance(date_result, Err):
                return date_result
            date = date_result.out

        # Parse pages
        pages: tuple[PageAttr, ...] = ()
        if data.get("pages"):
            pages_result = parse_pages(data["pages"])
            if isinstance(pages_result, Err):
                return pages_result
            pages = pages_result.out

        # Parse journal
        journal = None
        if data.get("journal"):
            journal_result = parse_journal(data["journal"], bibstring_type)
            if isinstance(journal_result, Err):
                return journal_result
            journal = journal_result.out

        # Parse crossref - for now, we'll skip complex crossref parsing and set to empty string
        # TODO: Implement proper crossref parsing if needed

        # Parse further_refs and depends_on
        further_refs = parse_bibkey_list(data.get("_further_refs", ""))
        depends_on = parse_bibkey_list(data.get("_depends_on", ""))

        # Parse keywords
        keywords = parse_keywords(data.get("_kw_level1", ""), data.get("_kw_level2", ""), data.get("_kw_level3", ""))

        # Parse edition
        edition = None
        if data.get("edition"):
            edition_str = data["edition"].strip()
            if edition_str:
                edition = int(edition_str)

        # Parse numeric fields
        dltc_num = None
        if data.get("_dltc_num"):
            dltc_num_str = data["_dltc_num"].strip()
            if dltc_num_str:
                dltc_num = int(dltc_num_str)

        num_inwork_coll = None
        if data.get("_num_inwork_coll"):
            num_inwork_coll_str = data["_num_inwork_coll"].strip()
            if num_inwork_coll_str:
                num_inwork_coll = int(num_inwork_coll_str)

        num_coll = None
        if data.get("_num_coll"):
            num_coll_str = data["_num_coll"].strip()
            if num_coll_str:
                num_coll = int(num_coll_str)

        num_sort = None
        if data.get("_num_sort"):
            num_sort_str = data["_num_sort"].strip()
            if num_sort_str:
                num_sort = int(num_sort_str)

        # Parse series
        series: BaseNamedRenderable | Literal[""] = ""
        if data.get("series"):
            series_attr = _create_bibstring_attr(data["series"], bibstring_type)
            series = BaseNamedRenderable(name=series_attr, id=None)

        # Create BibItem
        bibitem = BibItem(
            to_do_general=data.get("_to_do_general", ""),
            change_request=data.get("_change_request", ""),
            entry_type=parse_entry_type(data.get("entry_type", "")),
            bibkey=bibkey or "",
            author=authors,
            editor=editors,
            options=parse_options(data.get("options", "")),
            date=date,
            pubstate=parse_pubstate(data.get("pubstate", "")),
            title=_create_bibstring_attr(data["title"], bibstring_type) if data.get("title") else "",
            booktitle=_create_bibstring_attr(data["booktitle"], bibstring_type) if data.get("booktitle") else "",
            crossref="",
            journal=journal,
            volume=data.get("volume", ""),
            number=data.get("number", ""),
            pages=pages,
            eid=data.get("eid", ""),
            series=series,
            address=_create_bibstring_attr(data["address"], bibstring_type) if data.get("address") else "",
            institution=_create_bibstring_attr(data["institution"], bibstring_type) if data.get("institution") else "",
            school=_create_bibstring_attr(data["school"], bibstring_type) if data.get("school") else "",
            publisher=_create_bibstring_attr(data["publisher"], bibstring_type) if data.get("publisher") else "",
            type=_create_bibstring_attr(data["type"], bibstring_type) if data.get("type") else "",
            edition=edition,
            note=_create_bibstring_attr(data["note"], bibstring_type) if data.get("note") else "",
            issuetitle=_create_bibstring_attr(data["_issuetitle"], bibstring_type) if data.get("_issuetitle") else "",
            guesteditor=guesteditors,
            extra_note=_create_bibstring_attr(data["_extra_note"], bibstring_type) if data.get("_extra_note") else "",
            urn=data.get("urn", ""),
            eprint=data.get("eprint", ""),
            doi=data.get("doi", ""),
            url=data.get("url", ""),
            kws=keywords or "",
            epoch=parse_epoch(data.get("_epoch", "")),
            person=person or "",
            comm_for_profile_bib=data.get("_comm_for_profile_bib", ""),
            langid=parse_language_id(data.get("_langid", "")),
            lang_der=data.get("_lang_der", ""),
            further_refs=further_refs,
            depends_on=depends_on,
            dltc_num=dltc_num,
            spec_interest=data.get("_spec_interest", ""),
            note_perso=data.get("_note_perso", ""),
            note_stock=data.get("_note_stock", ""),
            note_status=data.get("_note_status", ""),
            num_inwork_coll=num_inwork_coll,
            num_inwork=data.get("_num_inwork", ""),
            num_coll=num_coll,
            dltc_copyediting_note=data.get("_dltc_copyediting_note", ""),
            note_missing=data.get("_note_missing", ""),
            num_sort=num_sort,
        )

        return Ok(bibitem)

    except Exception as e:
        return Err(
            message=f"Failed to parse bibitem: {e.__class__.__name__}: {e}",
            code=-1,
            error_type="BibItemParsingError",
            error_trace=traceback.format_exc(),
        )
