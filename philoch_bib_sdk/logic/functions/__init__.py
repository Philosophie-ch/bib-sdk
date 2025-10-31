"""Logic functions for bibliography processing."""

from philoch_bib_sdk.logic.functions.comparator import (
    compare_bibitems,
    compare_bibitems_detailed,
)
from philoch_bib_sdk.logic.functions.fuzzy_matcher import (
    BibItemBlockIndex,
    build_index,
    find_similar_bibitems,
    stage_bibitem,
    stage_bibitems_batch,
)
from philoch_bib_sdk.logic.functions.journal_article_matcher import (
    get_bibkey_by_journal_volume_number,
)

__all__ = [
    "compare_bibitems",
    "compare_bibitems_detailed",
    "BibItemBlockIndex",
    "build_index",
    "find_similar_bibitems",
    "stage_bibitem",
    "stage_bibitems_batch",
    "get_bibkey_by_journal_volume_number",
]
