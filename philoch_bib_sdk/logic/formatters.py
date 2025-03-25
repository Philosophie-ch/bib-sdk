from typing import List
from aletk.utils import get_logger
from philoch_bib_sdk.logic.models import Author, BibKey, PagePair

lgr = get_logger(__name__)


def _author_full_name_generic(given_name: str | None, family_name: str | None) -> str:
    if given_name is None:
        return ""

    if family_name is None:
        return given_name

    return f"{family_name}, {given_name}"


def _author_full_name(author: Author | None) -> str:
    if author is None:
        return ""
    return _author_full_name_generic(author.given_name, author.family_name)


def _author_full_name_latex(author: Author | None) -> str:
    if author is None:
        return ""
    return _author_full_name_generic(author.given_name_latex, author.family_name_latex)


def author_full_name(authors: List[Author] | None) -> str:
    if authors is None:
        return ""
    return " and ".join([_author_full_name(author) for author in authors])


def author_full_name_latex(authors: List[Author] | None) -> str:
    if authors is None:
        return ""
    return " and ".join([_author_full_name_latex(author) for author in authors])


def bibkey_str(bibkey: BibKey | None) -> str:
    if bibkey is None:
        return ""

    if bibkey.other_authors:
        authors_l = [bibkey.first_author, bibkey.other_authors]
    else:
        authors_l = [bibkey.first_author]

    authors = "-".join(authors_l)

    year = (
        f"{bibkey.year}{bibkey.year_suffix}"
        if bibkey.pub_status in ["published", ""]
        else f"{bibkey.pub_status}{bibkey.year_suffix}"
    )

    return f"{authors}:{year}"


def _pages_single_str(page_pair: PagePair) -> str:
    return "--".join([page_pair.start, page_pair.end])


def pages_str(pages: List[PagePair] | None) -> str:
    if pages is None:
        return ""
    return ", ".join([_pages_single_str(page_pair) for page_pair in pages])


def person_str(person: Author | None) -> str:
    """
    Note: ignores LaTeX names
    """
    if person is None:
        return ""

    if person.famous_name is not None:
        return person.famous_name

    if person.given_name is None and person.family_name is None:
        return ""

    if person.given_name is None:
        return person.family_name

    # Mononym
    return person.given_name
