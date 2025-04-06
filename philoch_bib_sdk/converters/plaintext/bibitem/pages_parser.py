import re
import traceback
from typing import Tuple
from aletk.utils import remove_extra_whitespace
from aletk.ResultMonad import Ok, Err

from philoch_bib_sdk.logic.models import PageAttr


def is_valid_roman(raw_str: str) -> bool:
    """
    TODO: TBD, decide if we want to control if the pages are in roman numbers.
    """
    raw_str = raw_str.upper()
    pattern = r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"
    return bool(re.match(pattern, raw_str))


def _parse_single_page_attr(
    text: str,
) -> PageAttr:
    """
    Parse a single page attribute from a string.
    """
    if "--" not in text and "-" in text:
        raise ValueError(f"Unexpected page format found in '{text}'. Expected either '<start>--<end>' or '<page>'.")
    elif "--" in text:
        parts = remove_extra_whitespace(text).split("--")

        if len(parts) != 2:
            raise ValueError(f"Unexpected number of page parts found in '{text}': '{parts}'. Expected exactly 2.")

        start_page, end_page = (remove_extra_whitespace(part) for part in parts)

    else:
        start_page = remove_extra_whitespace(text)
        end_page = ""

    return PageAttr(start=start_page, end=end_page)


def parse_pages(text: str) -> Ok[Tuple[PageAttr, ...]] | Err:
    """
    Parse a string of pages into a tuple of PageAttr objects.
    The input string is expected to be a comma-separated list of page attributes, with each attribute in the format "<start>--<end>" or "<page>".
    """
    try:
        if text == "":
            return Ok(())

        parts = (remove_extra_whitespace(part) for part in text.split(","))
        parts_normalized = (_parse_single_page_attr(part) for part in parts)

        return Ok(tuple(parts_normalized))

    except Exception as e:
        error_message = f"Error parsing pages from '{text}': {e}"
        return Err(
            error_message,
            code=-1,
            error_type=f"{e.__class__.__name__}",
            error_trace=traceback.format_exc(),
        )
