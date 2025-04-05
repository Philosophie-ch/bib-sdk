import traceback
from typing import Tuple
from aletk.ResultMonad import Ok, Err
from aletk.utils import get_logger, remove_extra_whitespace
from philoch_bib_sdk.logic.models import Author, BibStringAttr, TBibString

lgr = get_logger(__name__)


def _parse_normalize(text: str) -> Tuple[str, str, str]:
    """
    Return a tuple of two strings, the first of which is the given name, and the second of which is the family name. If only one name is found, the second string will be empty.

    Fails if more than two names are found.
    """
    parts = tuple(remove_extra_whitespace(part) for part in text.split(","))

    if len(parts) > 2:
        raise ValueError(f"Unexpected number of author parts found in '{text}': '{parts}'. Expected 2 or less.")

    elif len(parts) == 0:
        return ("", "", "")

    elif len(parts) == 1:
        # Mononym
        return ("", "", parts[0])

    else:
        # Full name
        return (parts[1], parts[0], "")


def _parse_single(normalized_name_parts: Tuple[str, str, str], bib_string_type: TBibString) -> Author:
    """
    Parse a single author from a string.
    """
    _given_name, _family_name, _mononym = normalized_name_parts

    return Author(
        given_name=BibStringAttr(**{str(bib_string_type): _given_name}),
        family_name=BibStringAttr(**{str(bib_string_type): _family_name}),
        mononym=BibStringAttr(**{str(bib_string_type): _mononym}),
        shorthand=BibStringAttr(),
        famous_name=BibStringAttr(),
        publications=(),
    )


def parse_author(text: str, bibstring_type: TBibString) -> Ok[Tuple[Author, ...]] | Err:
    """
    Return either a tuple of Author objects or an error.
    The input string is expected to be an ' and '-separated list of authors, with each author in the format "family_name, given_name" or "mononym".
    """
    try:
        if text == "":
            lgr.debug("Empty author string, returning empty tuple.")
            return Ok(())

        parts = tuple(remove_extra_whitespace(part) for part in text.split("and"))
        parts_normalized = (_parse_normalize(part) for part in parts)

        authors = tuple(_parse_single(part, bibstring_type) for part in parts_normalized)

        return Ok(authors)

    except Exception as e:
        return Err(
            message=f"Could not parse 'author' field with value [[ {text} ]]. {e.__class__.__name__}: {e}",
            code=-1,
            error_type="ParsingError",
            error_trace=f"{traceback.format_exc()}",
        )
