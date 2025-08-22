import traceback
from typing import Tuple
from aletk.ResultMonad import Ok, Err
from aletk.utils import get_logger
from philoch_bib_sdk.logic.literals import TBasicPubState
from philoch_bib_sdk.logic.models import BibKeyAttr

lgr = get_logger(__name__)


def _parse_bibkey_author(text: str) -> Tuple[str, str]:

    author_parts = text.split("-")

    if len(author_parts) == 1:
        first_author = author_parts[0]
        other_authors = ""
    elif len(author_parts) == 2:
        first_author = author_parts[0]
        other_authors = author_parts[1]
    else:
        raise ValueError(
            f"Unexpected bibkey author parts in [[ {text} ]]. Found [[ {author_parts} ]]. Expected 1 author, or 2 authors separated by '-'."
        )

    return first_author, other_authors


def _parse_bibkey_date_int_part(text: str) -> Tuple[int | None, int | None]:

    char_index_type_d = {i: (char, char.isdigit()) for i, char in enumerate(text)}

    year_l: list[str] = []
    int_breakpoint = None
    for i, (char, is_digit) in char_index_type_d.items():
        if is_digit:
            year_l.append(char)
            int_breakpoint = i
        else:
            break

    if year_l != []:
        year_int = int(f"{''.join(year_l)}")
    else:
        year_int = None

    if year_int and len(f"{year_int}") > 4:
        raise ValueError(f"Unexpected year value in '{text}': is not a valid year or publication state")

    return year_int, int_breakpoint


def _parse_bibkey_date_suffix_part(
    date_parts: str, year_int: int | None, int_breakpoint: int | None
) -> Tuple[int | TBasicPubState, str]:

    # Case 1. The first part of the year is a digit
    if int_breakpoint is not None:
        if year_int is None:
            raise ValueError(
                f"Unexpected case! year_int is None but int_breakpoint is not None. This should not happen."
            )

        date_suffix_raw = date_parts[int_breakpoint + 1 :]
        return (
            year_int,
            date_suffix_raw,
        )

    if year_int is not None:
        raise ValueError(f"Unexpected case! year_int is None but int_breakpoint is not None. This should not happen.")

    # Case 2. first characters are non-digits
    # has to start with either "unpub" or "forthcoming" then
    date_suffix_raw = "".join(date_parts)

    if not (date_suffix_raw.startswith("forthcoming") or date_suffix_raw.startswith("unpub")):
        raise ValueError(f"Unexpected year value in '{date_parts}': it is not a valid publication state.")

    date_suffix_parts = date_suffix_raw.split("-")

    if len(date_suffix_parts) == 2:
        suffix = date_suffix_parts[1]
        if not suffix:
            raise ValueError(
                f"Unexpected year value in '{date_parts}': it is not a valid publication state. Expected a suffix after '-'."
            )
    elif len(date_suffix_parts) == 1:
        suffix = ""
    else:
        raise ValueError(f"Unexpected year value in '{date_parts}': it is not a valid publication state.")

    pubstate: TBasicPubState = ""
    if date_suffix_parts[0] == "unpub":
        pubstate = "unpub"
    elif date_suffix_parts[0] == "forthcoming":
        pubstate = "forthcoming"
    else:
        raise ValueError(f"Unexpected year value in '{date_parts}': it is not a valid publication state.")

    return pubstate, suffix


def parse_bibkey(text: str) -> Ok[BibKeyAttr] | Err:
    """
    Return either a Bibkey object, or a BibkeyError object to indicate a parsing error.
    """

    try:
        bibkey_parts = text.split(":")
        if len(bibkey_parts) != 2:
            raise ValueError(
                f"Unexpected number of bibkey parts in [[ {text} ]]. Expected only two parts separated by ':'."
            )

        # Parse the author part
        first_author, other_authors = _parse_bibkey_author(bibkey_parts[0])

        # Parse the date part
        date_parts = bibkey_parts[1]

        year_int, int_breakpoint = _parse_bibkey_date_int_part(date_parts)

        # Parse the date suffix part
        date, date_suffix = _parse_bibkey_date_suffix_part(date_parts, year_int, int_breakpoint)

        return Ok(
            BibKeyAttr(
                first_author=first_author,
                other_authors=other_authors,
                date=date,
                date_suffix=date_suffix,
            )
        )

    except Exception as e:
        error_message = f"Could not parse bibkey for '{text}'"

        return Err(
            message=error_message,
            code=-1,
            error_type="BibkeyError",
            error_trace=f"{traceback.format_exc()}",
        )


def hard_parse_bibkey(text: str) -> BibKeyAttr:
    """
    Hard parse a bibkey, without any error handling.
    This is used for testing purposes only.
    """

    bibkey_parsed = parse_bibkey(text)

    if isinstance(bibkey_parsed, Err):
        raise ValueError(f"Could not hard parse '{text}' as bibkey: {bibkey_parsed.message}")

    return bibkey_parsed.out
