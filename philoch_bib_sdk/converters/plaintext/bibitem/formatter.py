from typing import TypedDict
from aletk.utils import get_logger

from philoch_bib_sdk.converters.plaintext.author.formatter import format_author
from philoch_bib_sdk.converters.plaintext.bib_string_formatter import format_bib_string_attr
from philoch_bib_sdk.converters.plaintext.bibitem.bibkey_formatter import format_bibkey
from philoch_bib_sdk.converters.plaintext.bibitem.date_formatter import format_date
from philoch_bib_sdk.converters.plaintext.bibitem.pages_formatter import format_pages
from philoch_bib_sdk.converters.plaintext.journal.formatter import format_journal
from philoch_bib_sdk.logic.literals import TBibTeXEntryType
from philoch_bib_sdk.logic.models import BibItem


lgr = get_logger(__name__)


def format_entry_type(entry_type: TBibTeXEntryType) -> str:
    """
    Format the entry type for the BibItem.
    """
    match entry_type:
        case "UNKNOWN":
            return "UNKNOWN"
        case _ if entry_type:
            return f"@{entry_type}"
        case _:
            return ""


class FormattedBibItem(TypedDict, total=True):
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


def format_bibitem(bibitem: BibItem) -> FormattedBibItem:

    bibkey = format_bibkey(bibitem.bibkey)

    author = format_author(bibitem.author, "latex")
    editor = format_author(bibitem.editor, "latex")
    person = format_author((bibitem._person,), "latex") if bibitem._person else ""

    shorthand = ", ".join([author.mononym.latex for author in bibitem.author if author.mononym.latex])
    date = format_date(bibitem.date)

    pages = format_pages(bibitem.pages)

    journal = format_journal(bibitem.journal, "latex")

    crossref = format_bibkey(bibitem.crossref.bibkey) if bibitem.crossref else ""

    _kw_level1, kw_level2, kw_level3 = (
        bibitem._kws.level_1.name if bibitem._kws else "",
        bibitem._kws.level_2.name if bibitem._kws else "",
        bibitem._kws.level_3.name if bibitem._kws else "",
    )

    further_refs = ", ".join([format_bibkey(ref) for ref in bibitem._further_refs])
    depends_on = ", ".join([format_bibkey(dep) for dep in bibitem._depends_on])

    formatted: FormattedBibItem = {
        "_to_do_general": bibitem._to_do_general,
        "_change_request": bibitem._change_request,
        "entry_type": format_entry_type(bibitem.entry_type),
        "bibkey": bibkey,
        "author": author,
        "_author_ids": "",
        "editor": editor,
        "_editor_ids": "",
        "author_ids": "",
        "options": ", ".join(bibitem.options),
        "shorthand": shorthand,
        "date": date,
        "pubstate": bibitem.pubstate,
        "title": format_bib_string_attr(bibitem.title, "latex"),
        "_title_unicode": format_bib_string_attr(bibitem.title, "unicode"),
        "booktitle": format_bib_string_attr(bibitem.booktitle, "latex"),
        "crossref": crossref,
        "journal": journal,
        "journal_id": "",
        "volume": bibitem.volume,
        "number": bibitem.number,
        "pages": pages,
        "eid": bibitem.eid,
        "series": format_bib_string_attr(bibitem.series.name, "latex") if bibitem.series else "",
        "address": format_bib_string_attr(bibitem.address, "latex"),
        "institution": format_bib_string_attr(bibitem.institution, "latex"),
        "school": format_bib_string_attr(bibitem.school, "latex"),
        "publisher": format_bib_string_attr(bibitem.publisher, "latex"),
        "publisher_id": "",
        "type": format_bib_string_attr(bibitem.type, "latex"),
        "edition": str(bibitem.edition) if bibitem.edition is not None else "",
        "note": format_bib_string_attr(bibitem.note, "latex"),
        "_issuetitle": format_bib_string_attr(bibitem.issuetitle, "latex") if bibitem.issuetitle else "",
        "_guesteditor": ", ".join(format_author(tuple(author for author in bibitem._guesteditor), "latex")),
        "_extra_note": format_bib_string_attr(bibitem._extra_note, "latex") if bibitem._extra_note else "",
        "urn": bibitem.urn,
        "eprint": bibitem.eprint,
        "doi": bibitem.doi,
        "url": bibitem.url,
        "_kw_level1": _kw_level1,
        "_kw_level2": kw_level2,
        "_kw_level3": kw_level3,
        "_epoch": bibitem._epoch,
        "_person": person,
        "_comm_for_profile_bib": bibitem._comm_for_profile_bib,
        "_langid": bibitem._langid,
        "_lang_der": bibitem._lang_der,
        "_further_refs": further_refs,
        "_depends_on": depends_on,
        "_dltc_num": str(bibitem._dltc_num) if bibitem._dltc_num is not None else "",
        "_spec_interest": bibitem._spec_interest,
        "_note_perso": bibitem._note_perso,
        "_note_stock": bibitem._note_stock,
        "_note_status": bibitem._note_status,
        "_num_inwork_coll": str(bibitem._num_inwork_coll) if bibitem._num_inwork_coll is not None else "",
        "_num_inwork": bibitem._num_inwork,
        "_num_coll": str(bibitem._num_coll) if bibitem._num_coll is not None else "",
        "_dltc_copyediting_note": bibitem._dltc_copyediting_note,
        "_note_missing": bibitem._note_missing,
        "_num_sort": str(bibitem._num_sort) if bibitem._num_sort is not None else "",
    }

    return formatted
