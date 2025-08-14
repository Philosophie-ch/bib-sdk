from typing import Tuple
from philoch_bib_sdk.logic.models import PageAttr


def _pages_single_str(page_pair: PageAttr) -> str:
    return "--".join((page_pair.start, page_pair.end)) if page_pair.end else page_pair.start


def format_pages(pages: Tuple[PageAttr, ...]) -> str:
    if pages is tuple():
        return ""

    return ", ".join((_pages_single_str(page_pair) for page_pair in pages))
