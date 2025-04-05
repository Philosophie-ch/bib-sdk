from typing import Tuple, TypedDict, Unpack

from philoch_bib_sdk.logic.literals import TBasicPubState
from philoch_bib_sdk.logic.models import (
    Author,
    BaseNamedRenderable,
    BaseRenderable,
    BibItem,
    BibKeyAttr,
    BibStringAttr,
    Journal,
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


def default_journal(**kwargs: Unpack[JournalArgs]) -> Journal:
    """
    Create a default Journal object, given a dictionary with any (or None) of its attributes. Defaults to empty strings if not provided.
    """
    return Journal(
        name=default_bib_string(**kwargs.get("name", {})),
        issn_print=kwargs.get("issn_print", ""),
        issn_electronic=kwargs.get("issn_electronic", ""),
        id=kwargs.get("id", None),
    )
