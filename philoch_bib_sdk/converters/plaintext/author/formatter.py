from typing import List
from aletk.utils import get_logger
from philoch_bib_sdk.logic.models import Author

lgr = get_logger(__name__)


def _full_name_generic(given_name: str, family_name: str) -> str:
    if not given_name:
        return ""

    if not family_name:
        return given_name

    return f"{family_name}, {given_name}"


def _full_name(author: Author | None, latex: bool = False) -> str:

    if not latex:
        if author is None:
            return ""
        return _full_name_generic(author.given_name, author.family_name)

    if author is None:
        return ""
    return _full_name_generic(author.given_name_latex, author.family_name_latex)


def format_author(authors: List[Author] | None, latex: bool = False) -> str:
    if authors is None:
        return ""
    return " and ".join([_full_name(author, latex=latex) for author in authors])
