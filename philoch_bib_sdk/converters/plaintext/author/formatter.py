from typing import Tuple
from aletk.utils import get_logger
from philoch_bib_sdk.logic.models import Author, TBibString

lgr = get_logger(__name__)


def _full_name_generic(given_name: str, family_name: str, mononym: str) -> str:
    if mononym:
        return mononym

    if not given_name:
        return ""

    if not family_name:
        return given_name

    return f"{family_name}, {given_name}"


def _format_single(author: Author, bibstring_type: TBibString) -> str:
    given_name = f"{getattr(author.given_name, bibstring_type)}"
    family_name = f"{getattr(author.family_name, bibstring_type)}"
    mononym = f"{getattr(author.mononym, bibstring_type)}"

    return _full_name_generic(given_name, family_name, mononym)


def format_author(authors: Tuple[Author, ...], bibstring_type: TBibString) -> str:
    names = (_format_single(author, bibstring_type=bibstring_type) for author in authors)
    return " and ".join(name for name in names if name)
