from aletk.utils import remove_extra_whitespace, get_logger
from aletk.ResultMonad import Ok, Err
from typing import Literal
from philoch_bib_sdk.logic.models import VALID_DATE_FORMATS, BibItemDateAttr


lgr = get_logger(__name__)


def _parse_date(text: str) -> BibItemDateAttr | Literal["no date"]:
    """
    Parse a single date attribute from a string.
    """
    text = remove_extra_whitespace(text)

    if remove_extra_whitespace(text).lower() == "no date":
        return "no date"

    # Split by potential delimiters (hyphens or slashes)
    parts = text.replace("-", "/").split("/")

    # Handle the number of parts (could be year, year-year2, year/year_2, year-month-day)
    if len(parts) == 1:
        return BibItemDateAttr(
            year=int(parts[0]), year_part_2_hyphen=None, year_part_2_slash=None, month=None, day=None
        )

    elif len(parts) == 2 and "-" in text:
        return BibItemDateAttr(
            year=int(parts[0]), year_part_2_hyphen=int(parts[1]), year_part_2_slash=None, month=None, day=None
        )

    elif len(parts) == 2 and "/" in text:
        return BibItemDateAttr(
            year=int(parts[0]), year_part_2_hyphen=None, year_part_2_slash=int(parts[1]), month=None, day=None
        )

    elif len(parts) == 3 and "-" in text and len(parts[1]) <= 2 and len(parts[2]) <= 2:
        return BibItemDateAttr(
            year=int(parts[0]), year_part_2_hyphen=None, year_part_2_slash=None, month=int(parts[1]), day=int(parts[2])
        )

    else:
        raise ValueError(f"Invalid date format found in '{text}'. Expected one of {', '.join(VALID_DATE_FORMATS)}.")


def parse_date(text: str) -> Ok[BibItemDateAttr | Literal["no date"]] | Err:
    """
    Parse a single date string into a BibItemDateAttr object.
    The input is expected to be a single date, either in the format '<year>' or '<year>-<month>' or '<year>-<month>-<day>' (or slashes instead of hyphens).
    """
    try:
        return Ok(_parse_date(text))

    except Exception as e:
        error_message = f"Error parsing date from '{text}': {e}"
        return Err(
            message=error_message,
            code=-1,
            error_type=f"{e.__class__.__name__}",
            error_trace="",
        )
