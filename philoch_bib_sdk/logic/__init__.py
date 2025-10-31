"""Logic layer for bibliography SDK."""

from philoch_bib_sdk.logic.literals import TBibTeXEntryType
from philoch_bib_sdk.logic.models import (
    Author,
    BibItem,
    BibItemDateAttr,
    BibKeyAttr,
    BibStringAttr,
    Journal,
    Maybe,
    PageAttr,
    TBibString,
)
from philoch_bib_sdk.logic.models_staging import (
    BibItemStaged,
    Match,
    PartialScore,
    ScoreComponent,
)

__all__ = [
    # Core models
    "Author",
    "BibItem",
    "BibItemDateAttr",
    "BibKeyAttr",
    "BibStringAttr",
    "Journal",
    "Maybe",
    "PageAttr",
    "TBibString",
    "TBibTeXEntryType",
    # Staging models
    "BibItemStaged",
    "Match",
    "PartialScore",
    "ScoreComponent",
]
